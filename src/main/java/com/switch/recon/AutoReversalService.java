package com.qswitch.recon;

import org.jpos.iso.ISOMsg;
import org.jpos.iso.MUX;

import javax.sql.DataSource;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class AutoReversalService {

    private static final int DEFAULT_MAX_RETRIES = 3;
    private static final long DEFAULT_INITIAL_BACKOFF_MS = 250L;
    private static final DateTimeFormatter F7_TRANSMISSION_TS = DateTimeFormatter.ofPattern("MMddHHmmss");
    private static final DateTimeFormatter F12_LOCAL_TIME = DateTimeFormatter.ofPattern("HHmmss");
    private static final DateTimeFormatter F13_LOCAL_DATE = DateTimeFormatter.ofPattern("MMdd");

    private final DataSource dataSource;
    private final MUX mux;
    private final int maxRetries;
    private final long initialBackoffMs;
    private final Sleeper sleeper;

    public AutoReversalService(DataSource dataSource, MUX mux) {
        this(dataSource, mux, DEFAULT_MAX_RETRIES, DEFAULT_INITIAL_BACKOFF_MS, millis -> {
            try {
                Thread.sleep(millis);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
    }

    AutoReversalService(DataSource dataSource, MUX mux, int maxRetries, long initialBackoffMs, Sleeper sleeper) {
        this.dataSource = dataSource;
        this.mux = mux;
        this.maxRetries = Math.max(1, maxRetries);
        this.initialBackoffMs = Math.max(0L, initialBackoffMs);
        this.sleeper = sleeper;
    }

    public int processReversals(List<ReconciliationIssue> candidates) {
        int processed = 0;
        Set<String> inRunKeys = new HashSet<>();

        for (ReconciliationIssue issue : candidates) {
            String stan = issue.getStan();
            String rrn = issue.getRrn();
            String key = stan + "|" + rrn;

            if (!inRunKeys.add(key)) {
                System.out.println("Skip duplicate candidate in same run: STAN=" + stan + " RRN=" + rrn);
                continue;
            }

            try {
                if (alreadyReversed(stan, rrn)) {
                    System.out.println("Skip already reversed: STAN=" + stan + " RRN=" + rrn);
                    continue;
                }

                ISOMsg reversal = buildReversal(stan, rrn);
                ISOMsg response = sendWithRetry(reversal, stan, rrn);

                handleResponse(issue, reversal, response);
                processed++;
            } catch (Exception e) {
                System.err.println("Auto-reversal failed for STAN=" + stan + " RRN=" + rrn + " reason=" + e.getMessage());
                try {
                    handleResponse(issue, buildReversal(stan, rrn), null);
                } catch (Exception ignored) {
                    // best effort fallback
                }
            }
        }

        return processed;
    }

    private ISOMsg sendWithRetry(ISOMsg reversal, String stan, String rrn) {
        Exception lastError = null;

        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                ISOMsg response = mux.request((ISOMsg) reversal.clone(), 5000);
                if (response != null) {
                    return response;
                }
                System.err.println("Reversal timeout attempt=" + attempt + " STAN=" + stan + " RRN=" + rrn);
            } catch (Exception e) {
                lastError = e;
                System.err.println("Reversal request error attempt=" + attempt + " STAN=" + stan + " RRN=" + rrn + " reason=" + e.getMessage());
            }

            if (attempt < maxRetries) {
                long backoff = initialBackoffMs * (1L << (attempt - 1));
                sleeper.sleep(backoff);
            }
        }

        if (lastError != null) {
            System.err.println("All reversal attempts exhausted with errors for STAN=" + stan + " RRN=" + rrn);
        }
        return null;
    }

    private ISOMsg buildReversal(String stan, String rrn) throws Exception {
        ISOMsg msg = new ISOMsg();
        ZonedDateTime nowUtc = ZonedDateTime.now(ZoneOffset.UTC);
        msg.setMTI("0400");
        msg.set(11, stan);
        msg.set(37, rrn);
        msg.set(7, nowUtc.format(F7_TRANSMISSION_TS));
        msg.set(12, nowUtc.format(F12_LOCAL_TIME));
        msg.set(13, nowUtc.format(F13_LOCAL_DATE));
        return msg;
    }

    private boolean alreadyReversed(String stan, String rrn) {
        String sql = """
            SELECT 1
            FROM transactions
            WHERE stan = ?
              AND rrn = ?
              AND (status = 'REVERSED' OR COALESCE(is_reversal, FALSE) = TRUE)
            LIMIT 1
        """;

        try (Connection c = dataSource.getConnection();
             PreparedStatement ps = c.prepareStatement(sql)) {

            ps.setString(1, stan);
            ps.setString(2, rrn);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next();
            }
        } catch (Exception e) {
            return false;
        }
    }

    private void handleResponse(ReconciliationIssue issue, ISOMsg reversal, ISOMsg response) throws Exception {
        String rc = response != null && response.hasField(39) ? response.getString(39) : "91";
        boolean success = "00".equals(rc);
        String status = success ? "REVERSED" : "REVERSAL_FAILED";
        String finalStatus = success ? "AUTO_REVERSAL" : "AUTO_REVERSAL_FAILED";

        try (Connection c = dataSource.getConnection()) {
            boolean previousAutoCommit = c.getAutoCommit();
            c.setAutoCommit(false);
            try {
                String updateSql = """
                    UPDATE transactions
                    SET status = ?,
                        final_status = ?,
                        rc = ?,
                        is_reversal = ?,
                        updated_at = NOW()
                    WHERE stan = ?
                      AND rrn = ?
                """;

                try (PreparedStatement ps = c.prepareStatement(updateSql)) {
                    ps.setString(1, status);
                    ps.setString(2, finalStatus);
                    ps.setString(3, rc);
                    ps.setBoolean(4, success);
                    ps.setString(5, issue.getStan());
                    ps.setString(6, issue.getRrn());
                    ps.executeUpdate();
                }

                String eventSql = """
                    INSERT INTO transaction_events (stan, rrn, mti, event_type, request_iso, response_iso, rc)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (stan, rrn, event_type) DO NOTHING
                """;

                try (PreparedStatement ps = c.prepareStatement(eventSql)) {
                    ps.setString(1, issue.getStan());
                    ps.setString(2, issue.getRrn());
                    ps.setString(3, reversal.getMTI());
                    ps.setString(4, "REVERSAL");
                    ps.setString(5, dumpIso(reversal));
                    ps.setString(6, response == null ? null : dumpIso(response));
                    ps.setString(7, rc);
                    ps.executeUpdate();
                }

                c.commit();
            } catch (Exception e) {
                try {
                    c.rollback();
                } catch (SQLException ignored) {
                    // ignore rollback errors in best-effort path
                }
                throw e;
            } finally {
                c.setAutoCommit(previousAutoCommit);
            }
        }
    }

    private String dumpIso(ISOMsg msg) {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        PrintStream ps = new PrintStream(baos, true, StandardCharsets.UTF_8);
        msg.dump(ps, "");
        return baos.toString(StandardCharsets.UTF_8);
    }

    @FunctionalInterface
    interface Sleeper {
        void sleep(long millis);
    }
}
