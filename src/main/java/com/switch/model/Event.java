package com.qswitch.model;

import java.time.Instant;

public class Event {
    private final String type;
    private final String message;
    private final Instant createdAt;

    public Event(String type, String message) {
        this.type = type;
        this.message = message;
        this.createdAt = Instant.now();
    }

    public String getType() {
        return type;
    }

    public String getMessage() {
        return message;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
