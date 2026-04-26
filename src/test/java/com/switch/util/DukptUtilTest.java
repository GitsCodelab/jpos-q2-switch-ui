package com.qswitch.util;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DukptUtilTest {
    @Test
    void shouldDeriveStableWorkingKey() {
        String result = DukptUtil.deriveWorkingKey("ABCDEF1234567890", "FFFF9876543210E00001");
        assertEquals(32, result.length());
        assertEquals("c040a4696bf084dc675e0bf4ab8c8ad1", result);
    }
}
