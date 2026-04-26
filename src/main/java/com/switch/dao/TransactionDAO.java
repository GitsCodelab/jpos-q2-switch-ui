package com.qswitch.dao;

import com.qswitch.model.Transaction;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

public class TransactionDAO {
    private final Map<String, Transaction> transactions = new ConcurrentHashMap<>();

    public Transaction save(Transaction transaction) {
        transactions.put(buildKey(transaction.getStan(), transaction.getRrn()), transaction);
        return transaction;
    }

    public Optional<Transaction> findByStanAndRrn(String stan, String rrn) {
        return Optional.ofNullable(transactions.get(buildKey(stan, rrn)));
    }

    public int count() {
        return transactions.size();
    }

    private String buildKey(String stan, String rrn) {
        return stan + ":" + rrn;
    }
}
