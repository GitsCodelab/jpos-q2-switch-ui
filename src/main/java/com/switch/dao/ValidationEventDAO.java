package com.qswitch.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;
import java.util.logging.Logger;

/**
 * Phase 09 — Validation Event DAO
 *
 * Persists ISO validation and authorization-rules audit records to the
 * {@code validation_events} table so that the UI Validation → Events tab
 * and Stats endpoint have data to display.
 *
 * Inserts are fire-and-forget: a failure to log must never abort a
 * legitimate transaction, so all SQL exceptions are caught and logged.
 */
public class ValidationEventDAO {

    private static final Logger LOG = Logger.getLogger(ValidationEventDAO.class.getName());

    private final boolean jdbcEnabled = DatabaseSupport.isJdbcEnabled();

    private static final String INSERT_SQL =
        "INSERT INTO validation_events " +
        "  (stan, rrn, mti, scheme, validation_type, result, errors, reject_code, created_at) " +
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)";

    /**
     * Log a single validation event.
     *
     * @param stan           System Trace Audit Number (F11)
     * @param rrn            Retrieval Reference Number (F37) — may be null
     * @param mti            Message Type Identifier, e.g. "0200"
     * @param scheme         Resolved scheme ("LOCAL", "VISA", "MC") — may be null
     * @param validationType "ISO_VALIDATION" or "AUTH_RULES"
     * @param result         "PASS" or "FAIL"
     * @param errors         Human-readable error list, joined with "; " — may be null
     * @param rejectCode     ISO RC if FAIL, null if PASS
     */
    public void logEvent(String stan, String rrn, String mti, String scheme,
                         String validationType, String result,
                         List<String> errors, String rejectCode) {
        if (!jdbcEnabled) {
            return;
        }
        String errorText = (errors != null && !errors.isEmpty())
            ? String.join("; ", errors)
            : null;

        try (Connection conn = DatabaseSupport.getConnection();
             PreparedStatement ps = conn.prepareStatement(INSERT_SQL)) {
            ps.setString(1, stan);
            ps.setString(2, rrn);
            ps.setString(3, mti);
            ps.setString(4, scheme);
            ps.setString(5, validationType);
            ps.setString(6, result);
            ps.setString(7, errorText);
            ps.setString(8, rejectCode);
            ps.setTimestamp(9, Timestamp.from(Instant.now()));
            ps.executeUpdate();
        } catch (SQLException e) {
            // Must not propagate — audit log failure should never block a transaction
            LOG.warning("Failed to persist validation event STAN=" + stan
                + " type=" + validationType + " result=" + result
                + ": " + e.getMessage());
        }
    }

    /**
     * Convenience: log a passing validation.
     */
    public void logPass(String stan, String rrn, String mti, String scheme,
                        String validationType) {
        logEvent(stan, rrn, mti, scheme, validationType, "PASS", null, null);
    }

    /**
     * Convenience: log a failing validation.
     */
    public void logFail(String stan, String rrn, String mti, String scheme,
                        String validationType, List<String> errors, String rejectCode) {
        logEvent(stan, rrn, mti, scheme, validationType, "FAIL", errors, rejectCode);
    }
}
