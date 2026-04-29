package com.qswitch.fraud;

import org.jpos.iso.ISOMsg;

import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class FraudEngine {
    private static final int DEFAULT_HIGH_AMOUNT_MINOR = 100_000;
    private static final int DEFAULT_VELOCITY_LIMIT = 5;
    private static final int DEFAULT_VELOCITY_WINDOW_SECONDS = 60;
    private static final int DEFAULT_FLAG_THRESHOLD = 50;
    private static final int DEFAULT_DECLINE_THRESHOLD = 80;

    private final Map<String, Deque<Instant>> terminalActivity = new ConcurrentHashMap<>();

    public FraudDecision evaluate(ISOMsg request, long amountMinor) {
        if (!isEnabled()) {
            return new FraudDecision(FraudDecision.Action.APPROVE, 0, List.of("FRAUD_DISABLED"));
        }

        List<String> reasons = new ArrayList<>();
        int riskScore = 0;

        String terminal = upper(safeField(request, 41));
        String pan = safeField(request, 2);
        String bin = pan != null && pan.length() >= 6 ? pan.substring(0, 6) : null;

        if (terminal != null && blacklistTerminals().contains(terminal)) {
            reasons.add("BLACKLIST_TERMINAL");
            riskScore = Math.max(riskScore, DEFAULT_DECLINE_THRESHOLD);
        }

        if (bin != null && blacklistBins().contains(bin)) {
            reasons.add("BLACKLIST_BIN");
            riskScore = Math.max(riskScore, DEFAULT_DECLINE_THRESHOLD);
        }

        if (amountMinor >= highAmountMinor()) {
            reasons.add("HIGH_AMOUNT");
            riskScore += 60;
        }

        if (terminal != null) {
            int hits = registerAndCountVelocity(terminal, velocityWindowSeconds());
            if (hits > velocityLimit()) {
                reasons.add("VELOCITY");
                riskScore += 30;
            }
        }

        riskScore = Math.min(100, riskScore);

        FraudDecision.Action action;
        if (riskScore >= declineThreshold()) {
            action = FraudDecision.Action.DECLINE;
        } else if (riskScore >= flagThreshold()) {
            action = FraudDecision.Action.FLAG;
        } else {
            action = FraudDecision.Action.APPROVE;
        }

        return new FraudDecision(action, riskScore, reasons);
    }

    protected int registerAndCountVelocity(String key, int windowSeconds) {
        Deque<Instant> queue = terminalActivity.computeIfAbsent(key, ignored -> new ArrayDeque<>());
        Instant now = Instant.now();
        Instant threshold = now.minusSeconds(windowSeconds);

        synchronized (queue) {
            queue.addLast(now);
            while (!queue.isEmpty() && queue.peekFirst().isBefore(threshold)) {
                queue.removeFirst();
            }
            return queue.size();
        }
    }

    private boolean isEnabled() {
        return !"false".equalsIgnoreCase(System.getProperty("switch.fraud.enabled", "true"));
    }

    private int highAmountMinor() {
        return intProp("switch.fraud.high-amount-minor", DEFAULT_HIGH_AMOUNT_MINOR);
    }

    private int velocityLimit() {
        return intProp("switch.fraud.velocity.limit", DEFAULT_VELOCITY_LIMIT);
    }

    private int velocityWindowSeconds() {
        return intProp("switch.fraud.velocity.window-seconds", DEFAULT_VELOCITY_WINDOW_SECONDS);
    }

    private int flagThreshold() {
        return intProp("switch.fraud.flag-threshold", DEFAULT_FLAG_THRESHOLD);
    }

    private int declineThreshold() {
        return intProp("switch.fraud.decline-threshold", DEFAULT_DECLINE_THRESHOLD);
    }

    private Set<String> blacklistTerminals() {
        return csvSet(System.getProperty("switch.fraud.blacklist.terminals", ""));
    }

    private Set<String> blacklistBins() {
        return csvSet(System.getProperty("switch.fraud.blacklist.bins", ""));
    }

    private int intProp(String key, int defaultValue) {
        String value = System.getProperty(key);
        if (value == null || value.isBlank()) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(value.trim());
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    private Set<String> csvSet(String value) {
        if (value == null || value.isBlank()) {
            return Set.of();
        }
        Set<String> out = new HashSet<>();
        for (String token : value.split(",")) {
            String cleaned = upper(token);
            if (cleaned != null) {
                out.add(cleaned);
            }
        }
        return out;
    }

    private String safeField(ISOMsg msg, int field) {
        try {
            if (!msg.hasField(field)) {
                return null;
            }
            return msg.getString(field);
        } catch (Exception e) {
            return null;
        }
    }

    private String upper(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        if (trimmed.isEmpty()) {
            return null;
        }
        return trimmed.toUpperCase(Locale.ROOT);
    }
}
