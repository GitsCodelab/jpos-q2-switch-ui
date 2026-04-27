package com.qswitch.util;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class DukptUtilTest {

    private static final String BDK = "0123456789ABCDEFFEDCBA9876543210";
    private static final String KSN = "FFFF9876543210E00001";

    @Test
    void shouldDeriveStableWorkingKey() {
        String key = DukptUtil.deriveWorkingKey(BDK, KSN);

        assertEquals(32, key.length());
        assertTrue(key.matches("[0-9a-f]{32}"));

        // Implementation regression vector (NOT official)
        assertEquals("042666b49184cfa368de9628d0397bc9", key);
    }

    @Test
    void shouldDeriveIPEK() {
        String ipek = DukptUtil.deriveIpekHex(BDK, KSN);

        assertEquals(32, ipek.length());
        assertTrue(ipek.matches("[0-9a-f]{32}"));
    }

    @Test
    void shouldChangeWithCounter() {
        String key1 = DukptUtil.deriveWorkingKey(BDK, KSN);
        String key2 = DukptUtil.deriveWorkingKey(BDK, "FFFF9876543210E00002");

        assertNotEquals(key1, key2);
    }

    @Test
    void shouldDeriveVariants() {
        String base = DukptUtil.deriveWorkingKey(BDK, KSN);
        String pin = DukptUtil.derivePinKey(BDK, KSN);
        String mac = DukptUtil.deriveMacKey(BDK, KSN);

        assertNotEquals(base, pin);
        assertNotEquals(base, mac);
        assertNotEquals(pin, mac);
    }

    @Test
    void shouldRejectInvalidInput() {
        assertThrows(IllegalArgumentException.class,
            () -> DukptUtil.deriveWorkingKey("BAD", KSN));

        assertThrows(IllegalArgumentException.class,
            () -> DukptUtil.deriveWorkingKey(BDK, "BAD"));
    }
}