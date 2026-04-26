package com.qswitch.service;

import com.qswitch.model.Transaction;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

class ReversalServiceTest {
    @Test
    void shouldBuildReversalFromOriginal() {
        Transaction original = new Transaction();
        original.setMti("0200");
        original.setStan("123456");
        original.setRrn("250011223344");
        original.setAmount(5500L);
        original.setCurrency("840");

        ReversalService service = new ReversalService();
        Transaction reversal = service.buildReversal(original);

        assertEquals("0400", reversal.getMti());
        assertEquals(original.getStan(), reversal.getStan());
        assertEquals(original.getRrn(), reversal.getRrn());
        assertFalse(reversal.isApproved());
        assertEquals("00", reversal.getResponseCode());
    }
}
