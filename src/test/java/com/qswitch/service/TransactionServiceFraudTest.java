package com.qswitch.service;

import com.qswitch.dao.EventDAO;
import com.qswitch.dao.TransactionDAO;
import com.qswitch.model.Transaction;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class TransactionServiceFraudTest {

    @Test
    void shouldDeclineWith05WhenAmountExceedsFraudLimit() {
        TransactionService service = new TransactionService(new TransactionDAO(), new EventDAO());

        Transaction tx = service.handleAuthorization("900001", "900001900001", 100_001L);

        assertEquals("05", tx.getResponseCode());
        assertEquals("DECLINED", tx.getStatus());
    }
}
