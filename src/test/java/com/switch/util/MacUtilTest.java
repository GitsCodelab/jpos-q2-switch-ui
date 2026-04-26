package com.qswitch.util;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class MacUtilTest {
    @Test
    void shouldComputeDeterministicHmacSha256() {
        String actual = MacUtil.hmacSha256Hex("hello", "secret");
        assertEquals("88aab3ede8d3adf94d26ab90d3bafd4a2083070c3bcce9c014ee04a443847c0b", actual);
    }
}
