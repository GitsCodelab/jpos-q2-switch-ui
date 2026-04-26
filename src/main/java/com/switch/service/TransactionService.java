package com.qswitch.service;

import com.qswitch.dao.EventDAO;
import com.qswitch.dao.TransactionDAO;
import com.qswitch.model.Event;
import com.qswitch.model.Transaction;

import java.util.Optional;

public class TransactionService {
    private final TransactionDAO transactionDAO;
    private final EventDAO eventDAO;

    public TransactionService(TransactionDAO transactionDAO, EventDAO eventDAO) {
        this.transactionDAO = transactionDAO;
        this.eventDAO = eventDAO;
    }

    public Transaction handleAuthorization(String stan, String rrn, long amount) {
        Optional<Transaction> existing = transactionDAO.findByStanAndRrn(stan, rrn);
        if (existing.isPresent()) {
            eventDAO.save(new Event("REPLAY_DETECTED", "Replay detected for stan=" + stan + " rrn=" + rrn));
            return existing.get();
        }

        Transaction transaction = new Transaction();
        transaction.setMti("0200");
        transaction.setStan(stan);
        transaction.setRrn(rrn);
        transaction.setAmount(amount);
        transaction.setCurrency("840");

        if (amount > 0) {
            transaction.setApproved(true);
            transaction.setResponseCode("00");
            eventDAO.save(new Event("AUTH_APPROVED", "Approved amount=" + amount + " stan=" + stan));
        } else {
            transaction.setApproved(false);
            transaction.setResponseCode("13");
            eventDAO.save(new Event("AUTH_DECLINED", "Declined invalid amount=" + amount + " stan=" + stan));
        }

        return transactionDAO.save(transaction);
    }
}
