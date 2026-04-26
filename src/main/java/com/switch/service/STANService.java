package com.qswitch.service;

import java.util.concurrent.atomic.AtomicInteger;

public class STANService {
    private static final int MAX_STAN = 1_000_000;
    private final AtomicInteger counter = new AtomicInteger(1);

    public String nextSTAN() {
        int value = counter.getAndUpdate(current -> (current + 1) % MAX_STAN);
        if (value <= 0) {
            value = 1;
            counter.set(2);
        }
        return String.format("%06d", value);
    }
}
