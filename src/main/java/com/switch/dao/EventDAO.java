package com.qswitch.dao;

import com.qswitch.model.Event;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class EventDAO {
    private final List<Event> events = Collections.synchronizedList(new ArrayList<>());

    public void save(Event event) {
        events.add(event);
    }

    public List<Event> findAll() {
        return List.copyOf(events);
    }

    public int count() {
        return events.size();
    }
}
