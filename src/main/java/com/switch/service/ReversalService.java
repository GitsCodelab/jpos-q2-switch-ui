package com.qswitch.service;

import com.qswitch.model.Transaction;

public class ReversalService {
    public Transaction buildReversal(Transaction original) {
        Transaction reversal = new Transaction();
        reversal.setMti("0400");
        reversal.setStan(original.getStan());
        reversal.setRrn(original.getRrn());
        reversal.setAmount(original.getAmount());
        reversal.setCurrency(original.getCurrency());
        reversal.setApproved(false);
        reversal.setResponseCode("00");
        return reversal;
    }
}
