package com.qswitch.dao;

import com.qswitch.model.Transaction;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

public class TransactionDAO {
    private final Map<String, Transaction> transactions = new ConcurrentHashMap<>();
    private final boolean jdbcEnabled = DatabaseSupport.isJdbcEnabled();
    private final boolean mirrorInMemory = DatabaseSupport.isInMemoryMirrorEnabled();

    public Transaction save(Transaction transaction) {
        if (jdbcEnabled) {
            try (Connection connection = DatabaseSupport.getConnection()) {
                save(connection, transaction);
            } catch (SQLException e) {
                throw new IllegalStateException("Failed to persist transaction", e);
            }
            if (mirrorInMemory) {
                transactions.put(buildKey(transaction.getStan(), transaction.getRrn()), transaction);
            }
            return transaction;
        }
        transactions.put(buildKey(transaction.getStan(), transaction.getRrn()), transaction);
        return transaction;
    }

    public Transaction save(Connection connection, Transaction transaction) {
        if (jdbcEnabled) {
            upsertTransaction(connection, transaction);
        }
        if (!jdbcEnabled || mirrorInMemory) {
            transactions.put(buildKey(transaction.getStan(), transaction.getRrn()), transaction);
        }
        return transaction;
    }

    public Optional<Transaction> findByStanAndRrn(String stan, String rrn) {
        if (jdbcEnabled) {
            Optional<Transaction> fromDb = findByStanAndRrnJdbc(stan, rrn);
            if (fromDb.isPresent()) {
                return fromDb;
            }
        }
        return Optional.ofNullable(transactions.get(buildKey(stan, rrn)));
    }

    public boolean exists(String stan, String rrn) {
        if (jdbcEnabled) {
            try (Connection connection = DatabaseSupport.getConnection()) {
                return exists(connection, stan, rrn);
            } catch (SQLException e) {
                throw new IllegalStateException("Failed to check transaction existence", e);
            }
        }
        return transactions.containsKey(buildKey(stan, rrn));
    }

    public boolean exists(Connection connection, String stan, String rrn) {
        if (!jdbcEnabled) {
            return transactions.containsKey(buildKey(stan, rrn));
        }

        String sql = "SELECT 1 FROM transactions WHERE stan=? AND rrn=? LIMIT 1";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setString(1, stan);
            ps.setString(2, rrn);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next();
            }
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to check transaction existence", e);
        }
    }

    public int count() {
        if (jdbcEnabled) {
            return countJdbc();
        }
        return transactions.size();
    }

    public void updateResponse(String stan, String rrn, String rc, String status, String finalStatus) {
        if (!jdbcEnabled) {
            Transaction tx = transactions.get(buildKey(stan, rrn));
            if (tx != null) {
                tx.setResponseCode(rc);
                tx.setStatus(status);
                tx.setFinalStatus(finalStatus);
            }
            return;
        }

        try (Connection connection = DatabaseSupport.getConnection()) {
            updateResponse(connection, stan, rrn, rc, status, finalStatus);
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to update transaction response", e);
        }
    }

    public void updateResponse(Connection connection, String stan, String rrn, String rc, String status, String finalStatus) {
        if (!jdbcEnabled) {
            Transaction tx = transactions.get(buildKey(stan, rrn));
            if (tx != null) {
                tx.setResponseCode(rc);
                tx.setStatus(status);
                tx.setFinalStatus(finalStatus);
            }
            return;
        }

        String sql = "UPDATE transactions SET rc=?, status=?, final_status=?, updated_at=NOW() "
            + "WHERE stan=? AND rrn=?";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setString(1, rc);
            ps.setString(2, status);
            ps.setString(3, finalStatus);
            ps.setString(4, stan);
            ps.setString(5, rrn);
            ps.executeUpdate();
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to update transaction response", e);
        }
    }

    public void updateRouting(String stan, String rrn, String issuerId, String scheme) {
        if (!jdbcEnabled) {
            Transaction tx = transactions.get(buildKey(stan, rrn));
            if (tx != null) {
                tx.setIssuerId(issuerId);
                tx.setScheme(scheme);
            }
            return;
        }

        try (Connection connection = DatabaseSupport.getConnection()) {
            updateRouting(connection, stan, rrn, issuerId, scheme);
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to update routing metadata", e);
        }
    }

    public void updateRouting(Connection connection, String stan, String rrn, String issuerId, String scheme) {
        if (!jdbcEnabled) {
            Transaction tx = transactions.get(buildKey(stan, rrn));
            if (tx != null) {
                tx.setIssuerId(issuerId);
                tx.setScheme(scheme);
            }
            return;
        }

        String sql = "UPDATE transactions SET issuer_id=COALESCE(?, issuer_id), scheme=COALESCE(?, scheme), updated_at=NOW() "
            + "WHERE stan=? AND rrn=?";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setString(1, issuerId);
            ps.setString(2, scheme);
            ps.setString(3, stan);
            ps.setString(4, rrn);
            ps.executeUpdate();
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to update routing metadata", e);
        }
    }

    public int incrementRetryCount(String stan, String rrn) {
        if (!jdbcEnabled) {
            Transaction tx = transactions.get(buildKey(stan, rrn));
            if (tx == null) {
                return 0;
            }
            tx.setRetryCount(tx.getRetryCount() + 1);
            return tx.getRetryCount();
        }

        try (Connection connection = DatabaseSupport.getConnection()) {
            String updateSql = "UPDATE transactions SET retry_count=COALESCE(retry_count, 0) + 1, updated_at=NOW() WHERE stan=? AND rrn=?";
            try (PreparedStatement update = connection.prepareStatement(updateSql)) {
                update.setString(1, stan);
                update.setString(2, rrn);
                update.executeUpdate();
            }
            String readSql = "SELECT retry_count FROM transactions WHERE stan=? AND rrn=? LIMIT 1";
            try (PreparedStatement read = connection.prepareStatement(readSql)) {
                read.setString(1, stan);
                read.setString(2, rrn);
                try (ResultSet rs = read.executeQuery()) {
                    if (rs.next()) {
                        return rs.getInt("retry_count");
                    }
                }
            }
            return 0;
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to increment retry count", e);
        }
    }

    public void updatePanIfMissing(String stan, String rrn, String pan) {
        if (pan == null || pan.isBlank()) {
            return;
        }

        if (!jdbcEnabled) {
            Transaction tx = transactions.get(buildKey(stan, rrn));
            if (tx != null && (tx.getPan() == null || tx.getPan().isBlank())) {
                tx.setPan(pan);
            }
            return;
        }

        try (Connection connection = DatabaseSupport.getConnection()) {
            updatePanIfMissing(connection, stan, rrn, pan);
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to update transaction PAN", e);
        }
    }

    public void updatePanIfMissing(Connection connection, String stan, String rrn, String pan) {
        if (pan == null || pan.isBlank()) {
            return;
        }

        if (!jdbcEnabled) {
            Transaction tx = transactions.get(buildKey(stan, rrn));
            if (tx != null && (tx.getPan() == null || tx.getPan().isBlank())) {
                tx.setPan(pan);
            }
            return;
        }

        String sql = "UPDATE transactions SET pan=?, updated_at=NOW() WHERE stan=? AND rrn=? AND (pan IS NULL OR pan='')";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setString(1, pan);
            ps.setString(2, stan);
            ps.setString(3, rrn);
            ps.executeUpdate();
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to update transaction PAN", e);
        }
    }

    private void upsertTransaction(Connection connection, Transaction transaction) {
        String sql = "INSERT INTO transactions (stan, rrn, pan, terminal_id, mti, original_mti, amount, currency, rc, status, final_status, is_reversal, issuer_id, scheme, retry_count, settled, settlement_date, batch_id, created_at, updated_at) "
            + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            + "ON CONFLICT (stan, rrn) DO UPDATE SET "
            + "pan=COALESCE(EXCLUDED.pan, transactions.pan), terminal_id=EXCLUDED.terminal_id, mti=EXCLUDED.mti, original_mti=EXCLUDED.original_mti, amount=EXCLUDED.amount, "
            + "currency=EXCLUDED.currency, rc=COALESCE(EXCLUDED.rc, transactions.rc), status=EXCLUDED.status, "
            + "final_status=COALESCE(EXCLUDED.final_status, transactions.final_status), is_reversal=EXCLUDED.is_reversal, "
            + "issuer_id=COALESCE(EXCLUDED.issuer_id, transactions.issuer_id), scheme=COALESCE(EXCLUDED.scheme, transactions.scheme), "
            + "retry_count=COALESCE(EXCLUDED.retry_count, transactions.retry_count), settled=COALESCE(EXCLUDED.settled, transactions.settled), "
            + "settlement_date=COALESCE(EXCLUDED.settlement_date, transactions.settlement_date), batch_id=COALESCE(EXCLUDED.batch_id, transactions.batch_id), updated_at=NOW()";

        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setString(1, transaction.getStan());
            ps.setString(2, transaction.getRrn());
            ps.setString(3, transaction.getPan());
            ps.setString(4, transaction.getTerminalId());
            ps.setString(5, transaction.getMti());
            ps.setString(6, transaction.getOriginalMti());
            ps.setLong(7, transaction.getAmount());
            ps.setString(8, transaction.getCurrency());
            ps.setString(9, transaction.getResponseCode());
            ps.setString(10, transaction.getStatus());
            ps.setString(11, transaction.getFinalStatus());
            ps.setBoolean(12, transaction.isReversal());
            ps.setString(13, transaction.getIssuerId());
            ps.setString(14, transaction.getScheme());
            ps.setInt(15, transaction.getRetryCount());
            ps.setBoolean(16, transaction.isSettled());
            if (transaction.getSettlementDate() != null) {
                ps.setDate(17, java.sql.Date.valueOf(transaction.getSettlementDate()));
            } else {
                ps.setDate(17, null);
            }
            ps.setString(18, transaction.getBatchId());
            ps.setTimestamp(19, Timestamp.from(transaction.getCreatedAt()));
            ps.setTimestamp(20, Timestamp.from(transaction.getCreatedAt()));
            ps.executeUpdate();
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to persist transaction", e);
        }
    }

    private Optional<Transaction> findByStanAndRrnJdbc(String stan, String rrn) {
        String sql = "SELECT mti, stan, rrn, pan, amount, currency, rc, created_at, terminal_id, original_mti, status, final_status, is_reversal, issuer_id, scheme, retry_count, settled, settlement_date, batch_id "
            + "FROM transactions WHERE stan=? AND rrn=? ORDER BY created_at DESC LIMIT 1";
        try (Connection connection = DatabaseSupport.getConnection();
             PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setString(1, stan);
            ps.setString(2, rrn);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return Optional.empty();
                }
                Transaction transaction = new Transaction();
                transaction.setMti(rs.getString("mti"));
                transaction.setStan(rs.getString("stan"));
                transaction.setRrn(rs.getString("rrn"));
                transaction.setPan(rs.getString("pan"));
                transaction.setAmount(rs.getLong("amount"));
                transaction.setCurrency(rs.getString("currency"));
                transaction.setResponseCode(rs.getString("rc"));
                transaction.setTerminalId(rs.getString("terminal_id"));
                transaction.setOriginalMti(rs.getString("original_mti"));
                transaction.setStatus(rs.getString("status"));
                transaction.setFinalStatus(rs.getString("final_status"));
                transaction.setReversal(rs.getBoolean("is_reversal"));
                transaction.setIssuerId(rs.getString("issuer_id"));
                transaction.setScheme(rs.getString("scheme"));
                transaction.setRetryCount(rs.getInt("retry_count"));
                transaction.setSettled(rs.getBoolean("settled"));
                java.sql.Date settlementDate = rs.getDate("settlement_date");
                if (settlementDate != null) {
                    transaction.setSettlementDate(settlementDate.toLocalDate());
                }
                transaction.setBatchId(rs.getString("batch_id"));
                Timestamp createdAt = rs.getTimestamp("created_at");
                if (createdAt != null) {
                    transaction.setCreatedAt(createdAt.toInstant());
                }
                return Optional.of(transaction);
            }
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to query transaction", e);
        }
    }

    private int countJdbc() {
        String sql = "SELECT COUNT(*) FROM transactions";
        try (Connection connection = DatabaseSupport.getConnection();
             PreparedStatement ps = connection.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {
            if (rs.next()) {
                return rs.getInt(1);
            }
            return 0;
        } catch (SQLException e) {
            throw new IllegalStateException("Failed to count transactions", e);
        }
    }

    private String buildKey(String stan, String rrn) {
        return stan + ":" + rrn;
    }
}
