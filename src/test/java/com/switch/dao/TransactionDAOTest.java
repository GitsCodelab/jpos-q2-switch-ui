package com.qswitch.dao;

import com.qswitch.model.Transaction;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TransactionDAOTest {
    @Test
    void shouldSaveAndFindByStanAndRrn() {
        TransactionDAO dao = new TransactionDAO();
        Transaction tx = new Transaction();
        tx.setStan("123456");
        tx.setRrn("111122223333");
        tx.setAmount(1000L);

        dao.save(tx);

        assertEquals(1, dao.count());
        assertTrue(dao.findByStanAndRrn("123456", "111122223333").isPresent());
    }

    @Test
    void shouldOverwriteWhenSavingSameStanAndRrnKey() {
        TransactionDAO dao = new TransactionDAO();

        Transaction first = new Transaction();
        first.setStan("222222");
        first.setRrn("333333333333");
        first.setAmount(100L);
        dao.save(first);

        Transaction second = new Transaction();
        second.setStan("222222");
        second.setRrn("333333333333");
        second.setAmount(999L);
        dao.save(second);

        assertEquals(1, dao.count());
        assertEquals(999L, dao.findByStanAndRrn("222222", "333333333333").orElseThrow().getAmount());
    }
}
