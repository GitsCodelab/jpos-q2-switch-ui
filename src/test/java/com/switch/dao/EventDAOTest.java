package com.qswitch.dao;

import com.qswitch.model.Event;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class EventDAOTest {
    @Test
    void shouldStoreEventsInInsertionOrder() {
        EventDAO dao = new EventDAO();
        dao.save(new Event("A", "first"));
        dao.save(new Event("B", "second"));

        List<Event> events = dao.findAll();

        assertEquals(2, dao.count());
        assertEquals("A", events.get(0).getType());
        assertEquals("B", events.get(1).getType());
    }

    @Test
    void findAllShouldReturnImmutableCopy() {
        EventDAO dao = new EventDAO();
        dao.save(new Event("A", "first"));

        List<Event> events = dao.findAll();

        assertThrows(UnsupportedOperationException.class, () -> events.add(new Event("B", "second")));
    }
}
