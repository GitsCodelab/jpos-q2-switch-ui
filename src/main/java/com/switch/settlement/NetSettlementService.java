package com.qswitch.settlement;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;

/**
 * Net Settlement Service: Computes bilateral obligations and net positions.
 * 
 * Flow:
 * 1. Bilateral Obligations: issuer → acquirer flows (raw transaction sums)
 * 2. Net Positions: reduces to net amount per bank (who owes how much)
 * 3. Persistence: saves net positions to net_settlement table
 */
public class NetSettlementService {

    private final DataSource ds;

    public NetSettlementService(DataSource ds) {
        this.ds = ds;
    }

    /**
     * Compute bilateral obligations from settled transactions.
     * Result: "BANK_A->BANK_B" = 100000 means BANK_A owes BANK_B 100,000
     */
    public Map<String, Long> computeObligations() {
        String sql = """
            SELECT issuer_id, acquirer_id, SUM(amount) AS total
            FROM transactions
            WHERE settled = TRUE AND issuer_id IS NOT NULL AND acquirer_id IS NOT NULL
            GROUP BY issuer_id, acquirer_id
            """;

        Map<String, Long> obligations = new TreeMap<>();

        try (Connection c = ds.getConnection();
             PreparedStatement ps = c.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {

            while (rs.next()) {
                String issuer = rs.getString("issuer_id");
                String acquirer = rs.getString("acquirer_id");
                long amount = rs.getLong("total");

                String key = issuer + "->" + acquirer;
                obligations.put(key, amount);
            }

        } catch (Exception e) {
            throw new RuntimeException("Failed to compute bilateral obligations", e);
        }

        return obligations;
    }

    /**
     * Compute net positions from bilateral obligations.
     * Reduces multiple flows into net amount per bank.
     * 
     * Example:
     *   BANK_A -> BANK_B: 100,000
     *   BANK_B -> BANK_A:  30,000
     *   Result:
     *     BANK_A: -70,000 (owes 70k)
     *     BANK_B: +70,000 (owed 70k)
     */
    public Map<String, Long> computeNetPositions(Map<String, Long> obligations) {
        Map<String, Long> net = new HashMap<>();

        for (var entry : obligations.entrySet()) {
            String[] parts = entry.getKey().split("->");
            String from = parts[0];      // issuer (payer)
            String to = parts[1];        // acquirer (payee)
            long amount = entry.getValue();

            // from (issuer) pays: decreases their balance
            net.put(from, net.getOrDefault(from, 0L) - amount);
            // to (acquirer) receives: increases their balance
            net.put(to, net.getOrDefault(to, 0L) + amount);
        }

        return net;
    }

    /**
     * Persist net positions to net_settlement table.
     * Each party gets one row with their net amount and batch reference.
     */
    public void persistNetSettlement(Map<String, Long> netPositions, String batchId) {
        String sql = """
            INSERT INTO net_settlement (party_id, net_amount, settlement_date, batch_id)
            VALUES (?, ?, CURRENT_DATE, ?)
            ON CONFLICT (party_id, batch_id) DO UPDATE
            SET net_amount = EXCLUDED.net_amount
            """;

        try (Connection c = ds.getConnection();
             PreparedStatement ps = c.prepareStatement(sql)) {

            for (var entry : netPositions.entrySet()) {
                ps.setString(1, entry.getKey());      // party_id
                ps.setLong(2, entry.getValue());      // net_amount
                ps.setString(3, batchId);             // batch_id
                ps.addBatch();
            }

            ps.executeBatch();

        } catch (Exception e) {
            throw new RuntimeException("Failed to persist net settlement", e);
        }
    }

    /**
     * Full settlement computation: obligations → net → persist.
     */
    public Map<String, Long> runFullSettlement(String batchId) {
        Map<String, Long> obligations = computeObligations();
        Map<String, Long> netPositions = computeNetPositions(obligations);
        persistNetSettlement(netPositions, batchId);
        return netPositions;
    }

    /**
     * Print net positions in human-readable format.
     */
    public void printNetPositions(Map<String, Long> netPositions) {
        System.out.println("\n=== Net Settlement Positions ===");
        for (var entry : netPositions.entrySet()) {
            String party = entry.getKey();
            long amount = entry.getValue();
            String direction = amount < 0 ? "OWES" : "OWED";
            System.out.printf("%s %s %,d%n", party, direction, Math.abs(amount));
        }
        System.out.println("=== Total (must be 0) ===");
        long total = netPositions.values().stream().mapToLong(Long::longValue).sum();
        System.out.printf("Sum = %,d%n%n", total);
    }
}
