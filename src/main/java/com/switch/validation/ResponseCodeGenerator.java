package com.qswitch.validation;

import java.util.HashMap;
import java.util.Map;

/**
 * Phase 09 — ISO 8583 Response Code Reference
 *
 * Centralises all response codes used by the switch so that every
 * component (validation, auth-rules, fraud, routing) draws from the
 * same authoritative map.
 *
 * Usage:
 *   String desc = ResponseCodeGenerator.describe("30");  // "Format error"
 *   String rc   = ResponseCodeGenerator.RC_FORMAT_ERROR; // "30"
 */
public final class ResponseCodeGenerator {

    // ── Commonly used RC constants ─────────────────────────────────────────────

    /** Approved */
    public static final String RC_APPROVED               = "00";
    /** Refer to card issuer */
    public static final String RC_REFER_ISSUER           = "01";
    /** Pick up card */
    public static final String RC_PICK_UP                = "04";
    /** Do not honour */
    public static final String RC_DO_NOT_HONOUR          = "05";
    /** Error */
    public static final String RC_ERROR                  = "06";
    /** Pick up card — special conditions */
    public static final String RC_PICK_UP_SPECIAL        = "07";
    /** Invalid transaction */
    public static final String RC_INVALID_TRANSACTION    = "12";
    /** Invalid amount */
    public static final String RC_INVALID_AMOUNT         = "13";
    /** Invalid card number */
    public static final String RC_INVALID_PAN            = "14";
    /** No such issuer */
    public static final String RC_NO_SUCH_ISSUER         = "15";
    /** Format error / mandatory data missing */
    public static final String RC_FORMAT_ERROR           = "30";
    /** Requested function not supported */
    public static final String RC_NOT_SUPPORTED          = "40";
    /** Lost card */
    public static final String RC_LOST_CARD              = "41";
    /** Stolen card */
    public static final String RC_STOLEN_CARD            = "43";
    /** Insufficient funds */
    public static final String RC_INSUFFICIENT_FUNDS     = "51";
    /** Expired card */
    public static final String RC_EXPIRED_CARD           = "54";
    /** Incorrect PIN */
    public static final String RC_INCORRECT_PIN          = "55";
    /** Transaction not permitted to cardholder */
    public static final String RC_NOT_PERMITTED          = "57";
    /** Exceeds withdrawal amount limit */
    public static final String RC_EXCEEDS_LIMIT          = "61";
    /** Restricted card */
    public static final String RC_RESTRICTED_CARD        = "62";
    /** Security violation */
    public static final String RC_SECURITY_VIOLATION     = "63";
    /** Exceeds frequency limit */
    public static final String RC_EXCEEDS_FREQUENCY      = "65";
    /** Response received too late */
    public static final String RC_TIMEOUT                = "68";
    /** Issuer or switch inoperative */
    public static final String RC_INOPERATIVE            = "91";
    /** Financial institution or intermediate network facility cannot be found for routing */
    public static final String RC_CANNOT_ROUTE           = "92";
    /** Transaction cannot be completed (violation of law) */
    public static final String RC_CANNOT_COMPLETE        = "93";
    /** Duplicate transmission */
    public static final String RC_DUPLICATE              = "94";
    /** Reconcile error */
    public static final String RC_RECONCILE_ERROR        = "95";
    /** System malfunction */
    public static final String RC_SYSTEM_MALFUNCTION     = "96";

    // ── Description map ───────────────────────────────────────────────────────

    private static final Map<String, String> DESCRIPTIONS = new HashMap<>();

    static {
        DESCRIPTIONS.put("00", "Approved");
        DESCRIPTIONS.put("01", "Refer to card issuer");
        DESCRIPTIONS.put("02", "Refer to card issuer — special condition");
        DESCRIPTIONS.put("03", "Invalid merchant");
        DESCRIPTIONS.put("04", "Pick up card");
        DESCRIPTIONS.put("05", "Do not honour");
        DESCRIPTIONS.put("06", "Error");
        DESCRIPTIONS.put("07", "Pick up card — special conditions");
        DESCRIPTIONS.put("08", "Honour with identification");
        DESCRIPTIONS.put("09", "Request in progress");
        DESCRIPTIONS.put("10", "Approved for partial amount");
        DESCRIPTIONS.put("11", "Approved (VIP)");
        DESCRIPTIONS.put("12", "Invalid transaction");
        DESCRIPTIONS.put("13", "Invalid amount");
        DESCRIPTIONS.put("14", "Invalid card number");
        DESCRIPTIONS.put("15", "No such issuer");
        DESCRIPTIONS.put("17", "Customer cancellation");
        DESCRIPTIONS.put("19", "Re-enter transaction");
        DESCRIPTIONS.put("20", "Invalid response");
        DESCRIPTIONS.put("21", "No action taken");
        DESCRIPTIONS.put("22", "Suspected malfunction");
        DESCRIPTIONS.put("25", "Unable to locate record");
        DESCRIPTIONS.put("28", "File is temporarily unavailable");
        DESCRIPTIONS.put("30", "Format error / mandatory data missing");
        DESCRIPTIONS.put("39", "No credit account");
        DESCRIPTIONS.put("40", "Requested function not supported");
        DESCRIPTIONS.put("41", "Lost card");
        DESCRIPTIONS.put("43", "Stolen card");
        DESCRIPTIONS.put("51", "Insufficient funds");
        DESCRIPTIONS.put("52", "No cheque account");
        DESCRIPTIONS.put("53", "No savings account");
        DESCRIPTIONS.put("54", "Expired card");
        DESCRIPTIONS.put("55", "Incorrect PIN");
        DESCRIPTIONS.put("56", "No card record");
        DESCRIPTIONS.put("57", "Transaction not permitted to cardholder");
        DESCRIPTIONS.put("58", "Transaction not permitted to terminal");
        DESCRIPTIONS.put("59", "Suspected fraud");
        DESCRIPTIONS.put("61", "Exceeds withdrawal amount limit");
        DESCRIPTIONS.put("62", "Restricted card");
        DESCRIPTIONS.put("63", "Security violation");
        DESCRIPTIONS.put("64", "Original amount incorrect");
        DESCRIPTIONS.put("65", "Exceeds withdrawal frequency limit");
        DESCRIPTIONS.put("68", "Response received too late");
        DESCRIPTIONS.put("75", "Allowable PIN tries exceeded");
        DESCRIPTIONS.put("76", "Invalid or missing substitution");
        DESCRIPTIONS.put("77", "Inconsistent with original");
        DESCRIPTIONS.put("78", "Blocked — first used");
        DESCRIPTIONS.put("79", "Lifecycle (Mastercard)");
        DESCRIPTIONS.put("80", "Network error");
        DESCRIPTIONS.put("85", "No reason to decline");
        DESCRIPTIONS.put("88", "Cryptographic failure");
        DESCRIPTIONS.put("89", "Unacceptable PIN — transaction declined");
        DESCRIPTIONS.put("91", "Issuer or switch inoperative");
        DESCRIPTIONS.put("92", "Financial institution not found for routing");
        DESCRIPTIONS.put("93", "Transaction cannot be completed");
        DESCRIPTIONS.put("94", "Duplicate transmission");
        DESCRIPTIONS.put("95", "Reconcile error");
        DESCRIPTIONS.put("96", "System malfunction");
        DESCRIPTIONS.put("97", "Reconciliation totals reset");
        DESCRIPTIONS.put("Z3", "Unable to go online");
    }

    // ── Public API ────────────────────────────────────────────────────────────

    /**
     * Returns a human-readable description for an ISO 8583 response code.
     * Returns "Unknown RC ({code})" for unrecognised codes.
     */
    public static String describe(String rc) {
        if (rc == null) return "Unknown RC (null)";
        return DESCRIPTIONS.getOrDefault(rc, "Unknown RC (" + rc + ")");
    }

    /**
     * Returns true if the given RC represents an approval.
     */
    public static boolean isApproved(String rc) {
        return RC_APPROVED.equals(rc);
    }

    /**
     * Returns true if the given RC represents a format / validation failure.
     */
    public static boolean isFormatError(String rc) {
        return RC_FORMAT_ERROR.equals(rc)
            || RC_INVALID_AMOUNT.equals(rc)
            || RC_INVALID_PAN.equals(rc)
            || RC_INVALID_TRANSACTION.equals(rc);
    }

    /**
     * Returns the full map (copy) for reporting / diagnostics.
     */
    public static Map<String, String> all() {
        return new HashMap<>(DESCRIPTIONS);
    }

    private ResponseCodeGenerator() { /* utility class — no instances */ }
}
