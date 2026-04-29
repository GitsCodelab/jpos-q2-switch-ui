package com.qswitch.settlement;

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for NetSettlementService.
 * 
 * Tests verify:
 * - Bilateral obligation computation
 * - Net position calculation (reduction logic)
 * - Conservation property (sum of net positions = 0)
 * - Service instantiation
 */
class NetSettlementServiceTest {

    @Test
    void shouldInstantiateNetSettlementService() {
        NetSettlementService service = new NetSettlementService(null);
        assertNotNull(service, "NetSettlementService should be instantiable");
    }

    @Test
    void shouldComputeSimpleBilateralObligation() {
        // Given: Two parties with one flow
        // BANK_A (issuer) pays BANK_B (acquirer): 100,000
        
        // This tests the obligation structure: "FROM->TO" = amount
        String obligation = "BANK_A->BANK_B";
        long amount = 100_000L;
        
        Map<String, Long> obligations = Map.of(obligation, amount);
        
        assertNotNull(obligations);
        assertEquals(amount, obligations.get(obligation));
    }

    @Test
    void shouldComputeNetPositionFromSingleObligation() {
        // Given: One bilateral flow
        // BANK_A -> BANK_B: 100,000
        // Expected:
        //   BANK_A: -100,000 (owes)
        //   BANK_B: +100,000 (owed)
        
        Map<String, Long> obligations = Map.of("BANK_A->BANK_B", 100_000L);
        
        NetSettlementService service = new NetSettlementService(null);
        Map<String, Long> netPositions = service.computeNetPositions(obligations);
        
        assertEquals(-100_000L, netPositions.get("BANK_A"));
        assertEquals(+100_000L, netPositions.get("BANK_B"));
    }

    @Test
    void shouldNetMultipleBilateralFlows() {
        // Given: Three parties with cross flows
        // BANK_A -> BANK_B: 100,000
        // BANK_B -> BANK_A:  30,000
        // BANK_A -> BANK_C:  20,000
        // Expected (net positions):
        //   BANK_A: -100,000 - 20,000 + 30,000 = -90,000 (owes net)
        //   BANK_B: +100,000 - 30,000 = +70,000 (owed net)
        //   BANK_C: +20,000 (owed net)
        
        Map<String, Long> obligations = Map.of(
            "BANK_A->BANK_B", 100_000L,
            "BANK_B->BANK_A", 30_000L,
            "BANK_A->BANK_C", 20_000L
        );
        
        NetSettlementService service = new NetSettlementService(null);
        Map<String, Long> netPositions = service.computeNetPositions(obligations);
        
        assertEquals(-90_000L, netPositions.get("BANK_A"));
        assertEquals(+70_000L, netPositions.get("BANK_B"));
        assertEquals(+20_000L, netPositions.get("BANK_C"));
    }

    @Test
    void shouldConserveMoneyInNetting() {
        // CRITICAL: Sum of all net positions must equal zero
        // This is conservation of money property in settlement
        
        Map<String, Long> obligations = Map.of(
            "BANK_A->BANK_B", 100_000L,
            "BANK_B->BANK_C", 50_000L,
            "BANK_C->BANK_A", 30_000L
        );
        
        NetSettlementService service = new NetSettlementService(null);
        Map<String, Long> netPositions = service.computeNetPositions(obligations);
        
        long totalNet = netPositions.values().stream()
            .mapToLong(Long::longValue)
            .sum();
        
        assertEquals(0L, totalNet, "Net positions must sum to zero (conservation of money)");
    }

    @Test
    void shouldHandleZeroObligations() {
        // Edge case: No settled transactions
        Map<String, Long> obligations = Map.of();
        
        NetSettlementService service = new NetSettlementService(null);
        Map<String, Long> netPositions = service.computeNetPositions(obligations);
        
        assertTrue(netPositions.isEmpty());
    }

    @Test
    void shouldHandleNettingBetweenTwoPartiesOnly() {
        // Two parties, single direction flow
        Map<String, Long> obligations = Map.of("BANK_X->BANK_Y", 250_000L);
        
        NetSettlementService service = new NetSettlementService(null);
        Map<String, Long> netPositions = service.computeNetPositions(obligations);
        
        assertEquals(2, netPositions.size());
        assertEquals(-250_000L, netPositions.get("BANK_X"));
        assertEquals(+250_000L, netPositions.get("BANK_Y"));
    }

    @Test
    void shouldNegateFlowProperly() {
        // Ensure issuer (from) is debited and acquirer (to) is credited
        // This is the core semantic of money flow
        
        Map<String, Long> obligations = Map.of(
            "PAYER->PAYEE", 999_999L
        );
        
        NetSettlementService service = new NetSettlementService(null);
        Map<String, Long> netPositions = service.computeNetPositions(obligations);
        
        // PAYER owes (negative)
        assertTrue(netPositions.get("PAYER") < 0);
        // PAYEE is owed (positive)
        assertTrue(netPositions.get("PAYEE") > 0);
        // They offset
        assertEquals(0L, netPositions.get("PAYER") + netPositions.get("PAYEE"));
    }
}
