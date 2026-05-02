package com.qswitch.validation;

import org.jpos.iso.ISOMsg;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Phase 09 — Authorization Rules Engine
 *
 * Evaluates configurable authorization rules AFTER ISO field validation
 * and BEFORE fraud scoring. Rules include:
 *
 * - MAX_AMOUNT       : per-scheme single-transaction ceiling
 * - MIN_AMOUNT       : per-scheme floor (e.g. no zero-amount purchases)
 * - CURRENCY_ALLOW   : allowed currency codes (ISO 4217 numeric)
 * - PROC_CODE_ALLOW  : allowed processing codes (F3)
 * - TERMINAL_BLOCK   : blocked terminal IDs (static, separate from fraud blacklist)
 * - PAN_PREFIX_BLOCK : blocked PAN BIN prefixes (6-digit)
 *
 * Rules are loaded from in-memory defaults but are overridable via
 * {@link #addRule} to support DB-driven updates pushed from the Python API.
 */
public class AuthorizationRulesEngine {

    public enum RuleType {
        MAX_AMOUNT,
        MIN_AMOUNT,
        CURRENCY_ALLOW,
        PROC_CODE_ALLOW,
        TERMINAL_BLOCK,
        PAN_PREFIX_BLOCK
    }

    public static class AuthRule {
        public final String scheme;       // "LOCAL", "VISA", "MC", or "*" for all
        public final RuleType type;
        public final String value;        // numeric string for amounts, code for others
        public final boolean enabled;

        public AuthRule(String scheme, RuleType type, String value, boolean enabled) {
            this.scheme = scheme == null ? "*" : scheme.toUpperCase(Locale.ROOT);
            this.type = type;
            this.value = value;
            this.enabled = enabled;
        }
    }

    public static class AuthDecision {
        private final boolean approved;
        private final String rejectCode;
        private final String reason;

        public AuthDecision(boolean approved, String rejectCode, String reason) {
            this.approved = approved;
            this.rejectCode = rejectCode;
            this.reason = reason;
        }

        public boolean isApproved() { return approved; }
        public String getRejectCode() { return rejectCode; }
        public String getReason() { return reason; }

        @Override
        public String toString() {
            return approved ? "APPROVED" : "REJECTED[" + reason + "] RC=" + rejectCode;
        }
    }

    // ── In-memory rule store ───────────────────────────────────────────────────

    private final List<AuthRule> rules = new ArrayList<>();

    public AuthorizationRulesEngine() {
        loadDefaults();
    }

    /**
     * Load sensible built-in defaults.
     * These mirror real-world scheme rules at a minimal level.
     */
    private void loadDefaults() {
        // All schemes: minimum 1 minor unit (no zero-amount authorisations)
        rules.add(new AuthRule("*",     RuleType.MIN_AMOUNT,     "1",       true));

        // LOCAL scheme: max 10,000,000 minor units (100,000.00)
        rules.add(new AuthRule("LOCAL", RuleType.MAX_AMOUNT,     "10000000", true));

        // VISA: max 99,999,999 minor units; only specific proc codes
        rules.add(new AuthRule("VISA",  RuleType.MAX_AMOUNT,     "99999999", true));
        rules.add(new AuthRule("VISA",  RuleType.PROC_CODE_ALLOW, "000000",  true));
        rules.add(new AuthRule("VISA",  RuleType.PROC_CODE_ALLOW, "010000",  true));
        rules.add(new AuthRule("VISA",  RuleType.PROC_CODE_ALLOW, "011000",  true));
        rules.add(new AuthRule("VISA",  RuleType.PROC_CODE_ALLOW, "200000",  true));

        // MC: same max; slightly different proc code set
        rules.add(new AuthRule("MC",    RuleType.MAX_AMOUNT,     "99999999", true));
        rules.add(new AuthRule("MC",    RuleType.PROC_CODE_ALLOW, "000000",  true));
        rules.add(new AuthRule("MC",    RuleType.PROC_CODE_ALLOW, "010000",  true));
        rules.add(new AuthRule("MC",    RuleType.PROC_CODE_ALLOW, "011000",  true));

        // All schemes: allowed currencies (USD=840, EUR=978, GBP=826, EGP=818)
        rules.add(new AuthRule("*",     RuleType.CURRENCY_ALLOW, "840",      true));
        rules.add(new AuthRule("*",     RuleType.CURRENCY_ALLOW, "978",      true));
        rules.add(new AuthRule("*",     RuleType.CURRENCY_ALLOW, "826",      true));
        rules.add(new AuthRule("*",     RuleType.CURRENCY_ALLOW, "818",      true));
    }

    /** Add or replace a rule at runtime (called by Java-side config reload). */
    public synchronized void addRule(AuthRule rule) {
        rules.add(rule);
    }

    /** Replace all rules (called when reloading from DB). */
    public synchronized void setRules(List<AuthRule> newRules) {
        rules.clear();
        rules.addAll(newRules);
    }

    // ── Evaluation ─────────────────────────────────────────────────────────────

    /**
     * Evaluate all enabled rules for the given scheme and message.
     *
     * @param request ISO message
     * @param scheme  routing-resolved scheme ("LOCAL", "VISA", "MC") or null
     * @param amount  amount in minor units (already parsed by SwitchListener)
     * @return AuthDecision — first failing rule causes immediate reject
     */
    public AuthDecision evaluate(ISOMsg request, String scheme, long amount) {
        String s = scheme == null ? "LOCAL" : scheme.toUpperCase(Locale.ROOT);

        String currency   = safeField(request, 49);
        String procCode   = safeField(request, 3);
        String terminalId = safeField(request, 41);
        String pan        = safeField(request, 2);
        String bin        = (pan != null && pan.length() >= 6) ? pan.substring(0, 6) : null;

        // Determine which rules apply: global ("*") + scheme-specific
        List<AuthRule> applicable = new ArrayList<>();
        for (AuthRule r : rules) {
            if (r.enabled && ("*".equals(r.scheme) || r.scheme.equals(s))) {
                applicable.add(r);
            }
        }

        // Collect ALLOW sets for types that use allowlist logic
        Set<String> allowedCurrencies  = collectAllowSet(applicable, RuleType.CURRENCY_ALLOW);
        Set<String> allowedProcCodes   = collectAllowSet(applicable, RuleType.PROC_CODE_ALLOW);
        Set<String> blockedTerminals   = collectAllowSet(applicable, RuleType.TERMINAL_BLOCK);
        Set<String> blockedPanPrefixes = collectAllowSet(applicable, RuleType.PAN_PREFIX_BLOCK);

        // ── Evaluate each rule class ──────────────────────────────────────────

        // MIN_AMOUNT
        for (AuthRule r : applicable) {
            if (r.type == RuleType.MIN_AMOUNT) {
                try {
                    long min = Long.parseLong(r.value);
                    if (amount < min) {
                        return new AuthDecision(false, "13",
                            "MIN_AMOUNT_VIOLATION[amount=" + amount + ",min=" + min + ",scheme=" + s + "]");
                    }
                } catch (NumberFormatException ignored) {}
            }
        }

        // MAX_AMOUNT
        for (AuthRule r : applicable) {
            if (r.type == RuleType.MAX_AMOUNT) {
                try {
                    long max = Long.parseLong(r.value);
                    if (amount > max) {
                        return new AuthDecision(false, "61",
                            "MAX_AMOUNT_VIOLATION[amount=" + amount + ",max=" + max + ",scheme=" + s + "]");
                    }
                } catch (NumberFormatException ignored) {}
            }
        }

        // CURRENCY_ALLOW
        if (!allowedCurrencies.isEmpty() && currency != null && !currency.isBlank()) {
            if (!allowedCurrencies.contains(currency.trim())) {
                return new AuthDecision(false, "57",
                    "CURRENCY_NOT_ALLOWED[currency=" + currency + ",scheme=" + s + "]");
            }
        }

        // PROC_CODE_ALLOW (only evaluated if there are procCode rules for this scheme)
        if (!allowedProcCodes.isEmpty() && procCode != null && !procCode.isBlank()) {
            if (!allowedProcCodes.contains(procCode.trim())) {
                return new AuthDecision(false, "57",
                    "PROC_CODE_NOT_ALLOWED[procCode=" + procCode + ",scheme=" + s + "]");
            }
        }

        // TERMINAL_BLOCK
        if (terminalId != null && blockedTerminals.contains(terminalId.trim().toUpperCase(Locale.ROOT))) {
            return new AuthDecision(false, "62",
                "TERMINAL_BLOCKED[terminal=" + terminalId + "]");
        }

        // PAN_PREFIX_BLOCK
        if (bin != null && blockedPanPrefixes.contains(bin)) {
            return new AuthDecision(false, "62",
                "PAN_PREFIX_BLOCKED[bin=" + bin + "]");
        }

        return new AuthDecision(true, null, "ALL_RULES_PASSED");
    }

    // ── Helpers ────────────────────────────────────────────────────────────────

    private Set<String> collectAllowSet(List<AuthRule> rules, RuleType type) {
        Set<String> set = ConcurrentHashMap.newKeySet();
        for (AuthRule r : rules) {
            if (r.type == type && r.value != null) {
                set.add(r.value.trim().toUpperCase(Locale.ROOT));
            }
        }
        return set;
    }

    private String safeField(ISOMsg msg, int field) {
        try {
            return msg.hasField(field) ? msg.getString(field) : null;
        } catch (Exception e) {
            return null;
        }
    }
}
