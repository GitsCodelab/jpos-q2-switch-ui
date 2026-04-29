package com.qswitch.fraud;

import org.jpos.iso.ISOMsg;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class FraudEngineTest {

    @AfterEach
    void cleanup() {
        System.clearProperty("switch.fraud.enabled");
        System.clearProperty("switch.fraud.blacklist.terminals");
        System.clearProperty("switch.fraud.blacklist.bins");
        System.clearProperty("switch.fraud.high-amount-minor");
        System.clearProperty("switch.fraud.velocity.limit");
        System.clearProperty("switch.fraud.velocity.window-seconds");
        System.clearProperty("switch.fraud.flag-threshold");
        System.clearProperty("switch.fraud.decline-threshold");
    }

    // ── EXISTING TESTS ────────────────────────────────────────────────────────

    @Test
    void shouldDeclineWhenTerminalBlacklisted() throws Exception {
        System.setProperty("switch.fraud.blacklist.terminals", "TERM-BAD");
        FraudEngine engine = new FraudEngine();

        ISOMsg request = request("444444", "000000000100", "TERM-BAD", "1234569999999999");
        FraudDecision decision = engine.evaluate(request, 100L);

        assertEquals(FraudDecision.Action.DECLINE, decision.getAction());
        assertTrue(decision.getReasons().contains("BLACKLIST_TERMINAL"));
    }

    @Test
    void shouldFlagHighAmount() throws Exception {
        System.setProperty("switch.fraud.high-amount-minor", "1000");
        System.setProperty("switch.fraud.flag-threshold", "50");
        System.setProperty("switch.fraud.decline-threshold", "95");
        FraudEngine engine = new FraudEngine();

        ISOMsg request = request("555555", "000000001500", "TERM-A", "1234560000001111");
        FraudDecision decision = engine.evaluate(request, 1500L);

        assertEquals(FraudDecision.Action.FLAG, decision.getAction());
        assertTrue(decision.getReasons().contains("HIGH_AMOUNT"));
    }

    @Test
    void shouldTriggerVelocityRule() throws Exception {
        System.setProperty("switch.fraud.velocity.limit", "2");
        System.setProperty("switch.fraud.velocity.window-seconds", "60");
        FraudEngine engine = new FraudEngine();

        ISOMsg request = request("666666", "000000000100", "TERM-V", "1234560000002222");
        engine.evaluate(request, 100L);
        engine.evaluate(request, 100L);
        FraudDecision decision = engine.evaluate(request, 100L);

        assertTrue(decision.getReasons().contains("VELOCITY"));
    }

    // ── NEW TESTS ─────────────────────────────────────────────────────────────

    @Test
    void shouldApproveNormalTransaction() throws Exception {
        System.setProperty("switch.fraud.high-amount-minor", "99999");
        FraudEngine engine = new FraudEngine();

        ISOMsg request = request("100001", "000000000100", "TERM-OK", "4111111111111111");
        FraudDecision decision = engine.evaluate(request, 100L);

        assertEquals(FraudDecision.Action.APPROVE, decision.getAction());
        assertTrue(decision.getRiskScore() < 50);
        assertFalse(decision.isDecline());
        assertFalse(decision.isFlag());
    }

    @Test
    void shouldDeclineWhenBinBlacklisted() throws Exception {
        System.setProperty("switch.fraud.blacklist.bins", "999999");
        FraudEngine engine = new FraudEngine();

        // PAN starts with 999999 → BIN = 999999
        ISOMsg request = request("111111", "000000000500", "TERM-OK", "9999991234567890");
        FraudDecision decision = engine.evaluate(request, 500L);

        assertEquals(FraudDecision.Action.DECLINE, decision.getAction());
        assertTrue(decision.getReasons().contains("BLACKLIST_BIN"));
    }

    @Test
    void shouldReturnApproveWhenEngineIsDisabled() throws Exception {
        System.setProperty("switch.fraud.enabled", "false");
        FraudEngine engine = new FraudEngine();

        // Even blacklisted terminal → APPROVE because engine is off
        System.setProperty("switch.fraud.blacklist.terminals", "TERM-X");
        ISOMsg request = request("222222", "000000100000", "TERM-X", "4111110000001111");
        FraudDecision decision = engine.evaluate(request, 100000L);

        assertEquals(FraudDecision.Action.APPROVE, decision.getAction());
        assertTrue(decision.getReasons().contains("FRAUD_DISABLED"));
    }

    @Test
    void shouldAccumulateScoreAndDecline() throws Exception {
        // HIGH_AMOUNT (+60) + explicit TERMINAL blacklist (→ max=80) = DECLINE
        System.setProperty("switch.fraud.high-amount-minor", "1000");
        System.setProperty("switch.fraud.blacklist.terminals", "TERM-Z");
        System.setProperty("switch.fraud.decline-threshold", "80");
        FraudEngine engine = new FraudEngine();

        ISOMsg request = request("333333", "000000002000", "TERM-Z", "4111110000009999");
        FraudDecision decision = engine.evaluate(request, 2000L);

        assertEquals(FraudDecision.Action.DECLINE, decision.getAction());
        assertTrue(decision.getReasons().contains("BLACKLIST_TERMINAL"));
        assertTrue(decision.getReasons().contains("HIGH_AMOUNT"));
        assertEquals(100, decision.getRiskScore()); // capped at 100
    }

    @Test
    void shouldNotFlagAmountBelowThreshold() throws Exception {
        System.setProperty("switch.fraud.high-amount-minor", "50000");
        System.setProperty("switch.fraud.flag-threshold", "50");
        FraudEngine engine = new FraudEngine();

        ISOMsg request = request("444444", "000000001000", "TERM-OK", "4111111111111111");
        FraudDecision decision = engine.evaluate(request, 1000L); // 1000 < 50000 threshold

        assertFalse(decision.getReasons().contains("HIGH_AMOUNT"));
        assertEquals(FraudDecision.Action.APPROVE, decision.getAction());
    }

    @Test
    void shouldIgnoreMissingTerminalFieldForBlacklist() throws Exception {
        System.setProperty("switch.fraud.blacklist.terminals", "TERM-ABSENT");
        FraudEngine engine = new FraudEngine();

        // No field 41 set → no terminal → should not trigger blacklist
        ISOMsg request = new ISOMsg();
        request.setMTI("0200");
        request.set(11, "555000");
        request.set(2, "4111111111111111");

        FraudDecision decision = engine.evaluate(request, 100L);

        assertFalse(decision.getReasons().contains("BLACKLIST_TERMINAL"));
    }

    @Test
    void shouldIgnorePanShorterThanSixForBinCheck() throws Exception {
        System.setProperty("switch.fraud.blacklist.bins", "123456");
        FraudEngine engine = new FraudEngine();

        // PAN only 4 chars → no BIN extraction
        ISOMsg request = new ISOMsg();
        request.setMTI("0200");
        request.set(11, "666000");
        request.set(41, "TERM-OK");
        request.set(2, "1234");

        FraudDecision decision = engine.evaluate(request, 100L);

        assertFalse(decision.getReasons().contains("BLACKLIST_BIN"));
    }

    private ISOMsg request(String stan, String amount, String terminal, String pan) throws Exception {
        ISOMsg msg = new ISOMsg();
        msg.setMTI("0200");
        msg.set(11, stan);
        msg.set(4, amount);
        msg.set(41, terminal);
        msg.set(2, pan);
        return msg;
    }
}
