package com.qswitch.service;

import com.qswitch.dao.EventDAO;
import com.qswitch.dao.TransactionDAO;
import com.qswitch.model.Event;
import com.qswitch.model.Transaction;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TransactionServiceTest {
    @Test
    void shouldApprovePositiveAmount() {
        TransactionDAO transactionDAO = new TransactionDAO();
        EventDAO eventDAO = new EventDAO();
        TransactionService service = new TransactionService(transactionDAO, eventDAO);

        Transaction result = service.handleAuthorization("000001", "250011223344", 1000L);

        assertTrue(result.isApproved());
        assertEquals("00", result.getResponseCode());
        assertEquals(1, transactionDAO.count());
        assertEquals(1, eventDAO.count());
        assertTrue(transactionDAO.findByStanAndRrn("000001", "250011223344").isPresent());
        assertEquals("AUTH_APPROVED", eventDAO.findAll().get(0).getType());
    }

    @Test
    void shouldDeclineNonPositiveAmount() {
        TransactionDAO transactionDAO = new TransactionDAO();
        EventDAO eventDAO = new EventDAO();
        TransactionService service = new TransactionService(transactionDAO, eventDAO);

        Transaction result = service.handleAuthorization("000001", "250011223344", 0L);

        assertFalse(result.isApproved());
        assertEquals("13", result.getResponseCode());
        assertEquals(1, transactionDAO.count());
        assertEquals(1, eventDAO.count());
        assertEquals("AUTH_DECLINED", eventDAO.findAll().get(0).getType());
    }

    @Test
    void shouldDeclineNegativeAmountAndKeepBusinessFields() {
        TransactionDAO transactionDAO = new TransactionDAO();
        EventDAO eventDAO = new EventDAO();
        TransactionService service = new TransactionService(transactionDAO, eventDAO);

        Transaction result = service.handleAuthorization("654321", "111122223333", -1L);

        assertFalse(result.isApproved());
        assertEquals("13", result.getResponseCode());
        assertEquals("0200", result.getMti());
        assertEquals("840", result.getCurrency());
        assertNotNull(result.getCreatedAt());
        assertEquals("Declined invalid amount=-1 stan=654321", eventDAO.findAll().get(0).getMessage());
    }

    @Test
    void shouldProtectAgainstReplayUsingStanAndRrn() {
        TransactionDAO transactionDAO = new TransactionDAO();
        EventDAO eventDAO = new EventDAO();
        TransactionService service = new TransactionService(transactionDAO, eventDAO);

        Transaction first = service.handleAuthorization("999001", "770011223344", 1000L);
        Transaction replay = service.handleAuthorization("999001", "770011223344", 1000L);

        assertSame(first, replay);
        assertEquals(1, transactionDAO.count());
        assertEquals("00", replay.getResponseCode());

        List<Event> events = eventDAO.findAll();
        assertEquals(2, events.size());
        assertEquals("AUTH_APPROVED", events.get(0).getType());
        assertEquals("REPLAY_DETECTED", events.get(1).getType());
    }
}
