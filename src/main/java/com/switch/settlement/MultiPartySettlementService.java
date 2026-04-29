package com.qswitch.settlement;

import javax.sql.DataSource;
import java.sql.*;
import java.util.*;

/**
 * Multi-Party Settlement Service
 *
 * Calculates net positions between issuing and acquiring banks based on transaction flows.
 *
 * Example:
 *   Bank A → Bank B = 150,000 (from issuer_id=A, acquirer_id=B transactions)
 *   Bank B → Bank A =  30,000 (from issuer_id=B, acquirer_id=A transactions)
 *
 *   Net result:
 *   Bank A owes Bank B = 150,000 - 30,000 = 120,000
 */
public class MultiPartySettlementService {

    private final DataSource dataSource;

    public MultiPartySettlementService(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    /**
     * Calculate and display net positions between all issuer-acquirer pairs.
     *
     * Aggregates settled transactions by (issuer_id, acquirer_id) to determine
     * the financial obligation of one bank to another.
     */
    public void runNetSettlement() {
        String sql = """
            SELECT issuer_id, acquirer_id, SUM(amount) AS total_amount
            FROM transactions
            WHERE settled = TRUE AND issuer_id IS NOT NULL AND acquirer_id IS NOT NULL
            GROUP BY issuer_id, acquirer_id
            """;

        Map<String, Map<String, Long>> netMap = new TreeMap<>();

        try (Connection c = dataSource.getConnection();
             PreparedStatement ps = c.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {

            while (rs.next()) {
                String issuer = rs.getString("issuer_id");
                String acquirer = rs.getString("acquirer_id");
                long amount = rs.getLong("total_amount");

                netMap.computeIfAbsent(issuer, k -> new TreeMap<>())
                      .put(acquirer, amount);
            }

        } catch (Exception e) {
            throw new RuntimeException("Failed to run net settlement", e);
        }

        printNetPositions(netMap);
    }

    /**
     * Calculate net position (netting) between two specific banks.
     *
     * @param bankA First bank ID
     * @param bankB Second bank ID
     * @return Positive value if A owes B; negative if B owes A
     */
    public long getNetPosition(String bankA, String bankB) {
        String sql = """
            SELECT SUM(CASE WHEN issuer_id = ? THEN amount ELSE 0 END) AS outflow,
                   SUM(CASE WHEN issuer_id = ? THEN amount ELSE 0 END) AS inflow
            FROM transactions
            WHERE settled = TRUE
              AND ((issuer_id = ? AND acquirer_id = ?) OR (issuer_id = ? AND acquirer_id = ?))
            """;

        try (Connection c = dataSource.getConnection();
             PreparedStatement ps = c.prepareStatement(sql)) {

            ps.setString(1, bankA);
            ps.setString(2, bankB);
            ps.setString(3, bankA);
            ps.setString(4, bankB);
            ps.setString(5, bankB);
            ps.setString(6, bankA);

            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    long outflow = rs.getLong("outflow");
                    long inflow = rs.getLong("inflow");
                    return outflow - inflow;
                }
            }

        } catch (Exception e) {
            throw new RuntimeException("Failed to calculate net position", e);
        }

        return 0;
    }

    /**
     * Get all bilaterals (directional flows) for a specific bank.
     *
     * @param bankId The bank to query
     * @return Map of counterparty → amount
     */
    public Map<String, Long> getBilaterals(String bankId) {
        String sql = """
            SELECT
                CASE WHEN issuer_id = ? THEN acquirer_id ELSE issuer_id END AS counterparty,
                SUM(CASE WHEN issuer_id = ? THEN amount ELSE -amount END) AS flow
            FROM transactions
            WHERE settled = TRUE AND (issuer_id = ? OR acquirer_id = ?)
            GROUP BY counterparty
            """;

        Map<String, Long> bilaterals = new TreeMap<>();

        try (Connection c = dataSource.getConnection();
             PreparedStatement ps = c.prepareStatement(sql)) {

            ps.setString(1, bankId);
            ps.setString(2, bankId);
            ps.setString(3, bankId);
            ps.setString(4, bankId);

            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    String counterparty = rs.getString("counterparty");
                    long flow = rs.getLong("flow");
                    bilaterals.put(counterparty, flow);
                }
            }

        } catch (Exception e) {
            throw new RuntimeException("Failed to get bilaterals", e);
        }

        return bilaterals;
    }

    private void printNetPositions(Map<String, Map<String, Long>> netMap) {
        System.out.println("=".repeat(60));
        System.out.println("MULTI-PARTY NET SETTLEMENT POSITIONS");
        System.out.println("=".repeat(60));

        if (netMap.isEmpty()) {
            System.out.println("No settled transactions found.");
            System.out.println("=".repeat(60));
            return;
        }

        for (var issuerEntry : netMap.entrySet()) {
            String issuer = issuerEntry.getKey();
            var acquirers = issuerEntry.getValue();

            System.out.printf("%nIssuer: %s%n", issuer);
            System.out.println("-".repeat(60));

            for (var acquirerEntry : acquirers.entrySet()) {
                String acquirer = acquirerEntry.getKey();
                long amount = acquirerEntry.getValue();

                System.out.printf("  → %s: %,d%n", acquirer, amount);
            }
        }

        System.out.println("=".repeat(60));
    }
}
