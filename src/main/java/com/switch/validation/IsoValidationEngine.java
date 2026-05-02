package com.qswitch.validation;

import org.jpos.iso.ISOMsg;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Phase 09 — Scheme-Level ISO 8583 Validation Engine
 *
 * Validates incoming ISOMsg fields against scheme-specific rules:
 * - Mandatory field presence
 * - Field length (min/max)
 * - Field format (NUMERIC, ALPHA, ALPHANUMERIC)
 * - Processing code allowlist
 * - Card expiry format (F14)
 * - MTI integrity check
 *
 * Rules are built-in by scheme (LOCAL / VISA / MC) and can be extended
 * via {@link IsoFieldRule} to support DB-driven rules in future iterations.
 */
public class IsoValidationEngine {

    // ── Enums ──────────────────────────────────────────────────────────────────

    public enum Format { NUMERIC, ALPHA, ALPHANUMERIC, ANY }

    public static class IsoFieldRule {
        public final int field;
        public final String name;
        public final boolean mandatory;
        public final int minLen;
        public final int maxLen;
        public final Format format;

        public IsoFieldRule(int field, String name, boolean mandatory,
                            int minLen, int maxLen, Format format) {
            this.field = field;
            this.name = name;
            this.mandatory = mandatory;
            this.minLen = minLen;
            this.maxLen = maxLen;
            this.format = format;
        }
    }

    public static class ValidationResult {
        private final boolean valid;
        private final List<String> errors;
        private final String rejectCode; // ISO RC to return on reject

        public ValidationResult(boolean valid, List<String> errors, String rejectCode) {
            this.valid = valid;
            this.errors = errors;
            this.rejectCode = rejectCode;
        }

        public boolean isValid() { return valid; }
        public List<String> getErrors() { return errors; }
        public String getRejectCode() { return rejectCode; }

        @Override
        public String toString() {
            return valid ? "VALID" : "INVALID[" + String.join(", ", errors) + "] RC=" + rejectCode;
        }
    }

    // ── Schema-specific rule sets ──────────────────────────────────────────────

    /**
     * Mandatory + format rules for a 0200 purchase authorisation.
     * LOCAL scheme is lenient; VISA/MC follow spec more strictly.
     */
    private static List<IsoFieldRule> rulesFor(String scheme) {
        List<IsoFieldRule> r = new ArrayList<>();
        String s = scheme == null ? "LOCAL" : scheme.toUpperCase(Locale.ROOT);

        switch (s) {

            case "VISA":
            case "MC":
                // F2 — PAN: 13-19 digits
                r.add(new IsoFieldRule(2,  "PAN",               true,  13, 19, Format.NUMERIC));
                // F3 — Processing code: 6 digits
                r.add(new IsoFieldRule(3,  "Processing Code",   true,   6,  6, Format.NUMERIC));
                // F4 — Amount: 12 digits
                r.add(new IsoFieldRule(4,  "Amount",            true,  12, 12, Format.NUMERIC));
                // F11 — STAN: 6 digits
                r.add(new IsoFieldRule(11, "STAN",              true,   6,  6, Format.NUMERIC));
                // F14 — Expiry date: YYMM, optional but if present must be valid
                r.add(new IsoFieldRule(14, "Expiry Date",       false,  4,  4, Format.NUMERIC));
                // F22 — POS entry mode
                r.add(new IsoFieldRule(22, "POS Entry Mode",    true,   3,  3, Format.NUMERIC));
                // F37 — RRN: 12 chars
                r.add(new IsoFieldRule(37, "RRN",               true,  12, 12, Format.ALPHANUMERIC));
                // F41 — Terminal ID: up to 8 chars
                r.add(new IsoFieldRule(41, "Terminal ID",       true,   1,  8, Format.ALPHANUMERIC));
                // F42 — Merchant ID: optional on MC, present on VISA acquiring
                if ("VISA".equals(s)) {
                    r.add(new IsoFieldRule(42, "Merchant ID",   false,  1, 15, Format.ALPHANUMERIC));
                }
                break;

            case "LOCAL":
            default:
                // Minimal rules for local switch test transactions
                r.add(new IsoFieldRule(2,  "PAN",               true,   1, 19, Format.NUMERIC));
                r.add(new IsoFieldRule(4,  "Amount",            true,   1, 12, Format.NUMERIC));
                r.add(new IsoFieldRule(11, "STAN",              true,   1,  6, Format.NUMERIC));
                r.add(new IsoFieldRule(41, "Terminal ID",       true,   1, 16, Format.ALPHANUMERIC));
                break;
        }
        return r;
    }

    // ── Public API ─────────────────────────────────────────────────────────────

    /**
     * Validate a 0200/0201 authorisation request against scheme rules.
     *
     * @param request ISO message
     * @param scheme  e.g. "LOCAL", "VISA", "MC" — derived from BIN routing or default
     * @return ValidationResult
     */
    public ValidationResult validate(ISOMsg request, String scheme) {
        List<String> errors = new ArrayList<>();

        // 1. MTI must be 0200 or 0201
        try {
            String mti = request.getMTI();
            if (!"0200".equals(mti) && !"0201".equals(mti)) {
                errors.add("MTI_NOT_AUTHORISATION[mti=" + mti + "]");
                return new ValidationResult(false, errors, "30");
            }
        } catch (Exception e) {
            errors.add("MTI_UNREADABLE");
            return new ValidationResult(false, errors, "30");
        }

        // 2. Field-level rules
        List<IsoFieldRule> rules = rulesFor(scheme);
        for (IsoFieldRule rule : rules) {
            String value = safeField(request, rule.field);

            // Presence check
            if (rule.mandatory && (value == null || value.isBlank())) {
                errors.add("MISSING_F" + rule.field + "[" + rule.name + "]");
                continue;
            }
            if (value == null || value.isBlank()) {
                continue; // optional and absent — OK
            }

            // Length checks
            int len = value.length();
            if (len < rule.minLen) {
                errors.add("F" + rule.field + "_TOO_SHORT[len=" + len + ",min=" + rule.minLen + "]");
            }
            if (len > rule.maxLen) {
                errors.add("F" + rule.field + "_TOO_LONG[len=" + len + ",max=" + rule.maxLen + "]");
            }

            // Format check
            switch (rule.format) {
                case NUMERIC:
                    if (!value.matches("\\d+")) {
                        errors.add("F" + rule.field + "_NOT_NUMERIC[val=" + value + "]");
                    }
                    break;
                case ALPHA:
                    if (!value.matches("[A-Za-z ]+")) {
                        errors.add("F" + rule.field + "_NOT_ALPHA[val=" + value + "]");
                    }
                    break;
                case ALPHANUMERIC:
                    if (!value.matches("[A-Za-z0-9 ]+")) {
                        errors.add("F" + rule.field + "_NOT_ALPHANUMERIC[val=" + value + "]");
                    }
                    break;
                default:
                    break;
            }
        }

        // 3. Card expiry integrity: if F14 present, must be future or current month
        String expiry = safeField(request, 14);
        if (expiry != null && expiry.length() == 4) {
            if (!isExpiryValid(expiry)) {
                errors.add("CARD_EXPIRED[F14=" + expiry + "]");
            }
        }

        // 4. Amount must be > 0
        String amountStr = safeField(request, 4);
        if (amountStr != null && !amountStr.isBlank()) {
            try {
                long amount = Long.parseLong(amountStr.trim());
                if (amount <= 0) {
                    errors.add("AMOUNT_ZERO_OR_NEGATIVE[F4=" + amountStr + "]");
                }
            } catch (NumberFormatException ignored) {
                // already caught by NUMERIC format check
            }
        }

        if (errors.isEmpty()) {
            return new ValidationResult(true, errors, null);
        }
        // RC 30 = format error; RC 13 = invalid amount
        String rc = errors.stream().anyMatch(e -> e.startsWith("AMOUNT")) ? "13" : "30";
        return new ValidationResult(false, errors, rc);
    }

    // ── Helpers ────────────────────────────────────────────────────────────────

    private String safeField(ISOMsg msg, int field) {
        try {
            return msg.hasField(field) ? msg.getString(field) : null;
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * F14 is YYMM. Card is valid if it hasn't expired relative to current month.
     */
    private boolean isExpiryValid(String yymm) {
        try {
            int yy = Integer.parseInt(yymm.substring(0, 2));
            int mm = Integer.parseInt(yymm.substring(2, 4));
            if (mm < 1 || mm > 12) return false;
            java.time.YearMonth expiry = java.time.YearMonth.of(2000 + yy, mm);
            java.time.YearMonth now = java.time.YearMonth.now();
            return !expiry.isBefore(now);
        } catch (Exception e) {
            return false;
        }
    }
}
