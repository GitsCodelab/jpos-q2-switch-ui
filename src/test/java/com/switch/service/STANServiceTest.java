package com.qswitch.service;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class STANServiceTest {
    @Test
    void shouldGenerateSixDigitValues() {
        STANService service = new STANService();

        String first = service.nextSTAN();
        String second = service.nextSTAN();

        assertEquals(6, first.length());
        assertEquals(6, second.length());
        assertNotEquals(first, second);
        assertTrue(first.matches("\\d{6}"));
        assertTrue(second.matches("\\d{6}"));
    }

    @Test
    void shouldIncrementSequentiallyFromInitialValue() {
        STANService service = new STANService();

        assertEquals("000001", service.nextSTAN());
        assertEquals("000002", service.nextSTAN());
        assertEquals("000003", service.nextSTAN());
    }
}
