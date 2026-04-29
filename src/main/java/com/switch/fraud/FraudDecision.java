package com.qswitch.fraud;

import java.util.List;

public class FraudDecision {
    public enum Action {
        APPROVE,
        FLAG,
        DECLINE
    }

    private final Action action;
    private final int riskScore;
    private final List<String> reasons;

    public FraudDecision(Action action, int riskScore, List<String> reasons) {
        this.action = action;
        this.riskScore = riskScore;
        this.reasons = reasons;
    }

    public Action getAction() {
        return action;
    }

    public int getRiskScore() {
        return riskScore;
    }

    public List<String> getReasons() {
        return reasons;
    }

    public boolean isDecline() {
        return action == Action.DECLINE;
    }

    public boolean isFlag() {
        return action == Action.FLAG;
    }
}
