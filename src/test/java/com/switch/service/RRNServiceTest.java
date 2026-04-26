package com.qswitch.service;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RRNServiceTest {
    @Test
    void shouldGenerateTwelveDigitRrn() {
        RRNService service = new RRNService();

        String one = service.nextRRN();
        String two = service.nextRRN();

        assertEquals(12, one.length());
        assertTrue(one.matches("\\d{12}"));
        assertNotEquals(one, two);
    }

    @Test
    void shouldIncreaseThreeDigitSequenceWithinSameServiceInstance() {
        RRNService service = new RRNService();

        String one = service.nextRRN();
        String two = service.nextRRN();

        int seqOne = Integer.parseInt(one.substring(9));
        int seqTwo = Integer.parseInt(two.substring(9));
        assertEquals((seqOne + 1) % 1000, seqTwo);
    }
}
