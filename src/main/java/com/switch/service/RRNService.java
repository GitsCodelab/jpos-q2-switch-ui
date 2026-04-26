package com.qswitch.service;

import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.atomic.AtomicInteger;

public class RRNService {
    private static final DateTimeFormatter PREFIX_FORMAT = DateTimeFormatter.ofPattern("yyDDDHHmm");
    private final AtomicInteger sequence = new AtomicInteger();

    public String nextRRN() {
        LocalDateTime now = LocalDateTime.now(ZoneOffset.UTC);
        int seq = sequence.getAndUpdate(value -> (value + 1) % 1000);
        return now.format(PREFIX_FORMAT) + String.format("%03d", seq);
    }
}
