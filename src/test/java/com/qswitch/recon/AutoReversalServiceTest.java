package com.qswitch.recon;

import org.jpos.iso.ISOMsg;
import org.jpos.iso.ISOResponseListener;
import org.jpos.iso.MUX;
import org.junit.jupiter.api.Test;

import javax.sql.DataSource;
import java.io.PrintWriter;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLFeatureNotSupportedException;
import java.sql.SQLException;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AutoReversalServiceTest {

    private static final Object TIMEOUT = new Object();

    @Test
    void shouldSkipAlreadyReversedTransactions() {
        StubDataSource ds = new StubDataSource();
        ds.putTransaction("100001", "R1", "REVERSED", true, "00", "AUTO_REVERSAL");

        StubMux mux = new StubMux(List.of(muxResponse("00")));
        AutoReversalService service = new AutoReversalService(ds, mux, 3, 1L, millis -> { });

        int processed = service.processReversals(List.of(new ReconciliationIssue("100001", "R1", "REVERSAL_REQUIRED", "x")));

        assertEquals(0, processed);
        assertEquals(0, mux.requestCalls());
        assertEquals(0, ds.events.size());
    }

    @Test
    void shouldMarkReversedAndPersistEventOnSuccessfulResponse() {
        StubDataSource ds = new StubDataSource();
        ds.putTransaction("100002", "R2", "APPROVED", false, "00", "LOCAL_RESPONSE");

        StubMux mux = new StubMux(List.of(muxResponse("00")));
        AutoReversalService service = new AutoReversalService(ds, mux, 3, 1L, millis -> { });

        int processed = service.processReversals(List.of(new ReconciliationIssue("100002", "R2", "REVERSAL_REQUIRED", "x")));

        assertEquals(1, processed);
        assertEquals(1, mux.requestCalls());

        TxRecord tx = ds.getTransaction("100002", "R2");
        assertNotNull(tx);
        assertEquals("REVERSED", tx.status);
        assertEquals("00", tx.rc);
        assertEquals("AUTO_REVERSAL", tx.finalStatus);
        assertTrue(tx.isReversal);

        assertEquals(1, ds.events.size());
        EventRecord event = ds.events.get(0);
        assertEquals("100002", event.stan);
        assertEquals("R2", event.rrn);
        assertEquals("REVERSAL", event.eventType);
        assertEquals("00", event.rc);
        assertNotNull(event.requestIso);
        assertNotNull(event.responseIso);
    }

    @Test
    void shouldRetryWithBackoffAndMarkFailedOnTimeout() {
        StubDataSource ds = new StubDataSource();
        ds.putTransaction("100003", "R3", "AUTHORIZED", false, null, "PENDING");

        StubMux mux = new StubMux(List.of(TIMEOUT, TIMEOUT, TIMEOUT));
        List<Long> backoffs = new ArrayList<>();
        AutoReversalService service = new AutoReversalService(ds, mux, 3, 5L, backoffs::add);

        int processed = service.processReversals(List.of(new ReconciliationIssue("100003", "R3", "REVERSAL_REQUIRED", "x")));

        assertEquals(1, processed);
        assertEquals(3, mux.requestCalls());
        assertEquals(List.of(5L, 10L), backoffs);

        TxRecord tx = ds.getTransaction("100003", "R3");
        assertNotNull(tx);
        assertEquals("REVERSAL_FAILED", tx.status);
        assertEquals("91", tx.rc);
        assertEquals("AUTO_REVERSAL_FAILED", tx.finalStatus);
        assertFalse(tx.isReversal);

        assertEquals(1, ds.events.size());
        assertEquals("91", ds.events.get(0).rc);
    }

    @Test
    void shouldRetryAfterExceptionThenSucceed() {
        StubDataSource ds = new StubDataSource();
        ds.putTransaction("100004", "R4", "APPROVED", false, "00", "LOCAL_RESPONSE");

        StubMux mux = new StubMux(List.of(new RuntimeException("mux down"), muxResponse("00")));
        List<Long> backoffs = new ArrayList<>();
        AutoReversalService service = new AutoReversalService(ds, mux, 3, 7L, backoffs::add);

        int processed = service.processReversals(List.of(new ReconciliationIssue("100004", "R4", "REVERSAL_REQUIRED", "x")));

        assertEquals(1, processed);
        assertEquals(2, mux.requestCalls());
        assertEquals(List.of(7L), backoffs);

        TxRecord tx = ds.getTransaction("100004", "R4");
        assertEquals("REVERSED", tx.status);
        assertTrue(tx.isReversal);
    }

    @Test
    void shouldSkipDuplicateCandidateInSameRun() {
        StubDataSource ds = new StubDataSource();
        ds.putTransaction("100005", "R5", "APPROVED", false, "00", "LOCAL_RESPONSE");

        StubMux mux = new StubMux(List.of(muxResponse("00")));
        AutoReversalService service = new AutoReversalService(ds, mux, 3, 1L, millis -> { });

        List<ReconciliationIssue> candidates = List.of(
            new ReconciliationIssue("100005", "R5", "REVERSAL_REQUIRED", "x"),
            new ReconciliationIssue("100005", "R5", "REVERSAL_REQUIRED", "x")
        );

        int processed = service.processReversals(candidates);

        assertEquals(1, processed);
        assertEquals(1, mux.requestCalls());
        assertEquals(1, ds.events.size());
    }

    private static ISOMsg muxResponse(String rc) {
        try {
            ISOMsg msg = new ISOMsg();
            msg.setMTI("0430");
            msg.set(39, rc);
            return msg;
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    private record Key(String stan, String rrn) {
    }

    private static final class TxRecord {
        private String status;
        private boolean isReversal;
        private String rc;
        private String finalStatus;

        private TxRecord(String status, boolean isReversal, String rc, String finalStatus) {
            this.status = status;
            this.isReversal = isReversal;
            this.rc = rc;
            this.finalStatus = finalStatus;
        }
    }

    private static final class EventRecord {
        private final String stan;
        private final String rrn;
        private final String eventType;
        private final String requestIso;
        private final String responseIso;
        private final String rc;

        private EventRecord(String stan, String rrn, String eventType, String requestIso, String responseIso, String rc) {
            this.stan = stan;
            this.rrn = rrn;
            this.eventType = eventType;
            this.requestIso = requestIso;
            this.responseIso = responseIso;
            this.rc = rc;
        }
    }

    private static final class StubDataSource implements DataSource {
        private final Map<Key, TxRecord> transactions = new HashMap<>();
        private final List<EventRecord> events = new ArrayList<>();

        private void putTransaction(String stan, String rrn, String status, boolean isReversal, String rc, String finalStatus) {
            transactions.put(new Key(stan, rrn), new TxRecord(status, isReversal, rc, finalStatus));
        }

        private TxRecord getTransaction(String stan, String rrn) {
            return transactions.get(new Key(stan, rrn));
        }

        @Override
        public Connection getConnection() {
            InvocationHandler connectionHandler = (proxy, method, args) -> {
                String name = method.getName();
                if ("prepareStatement".equals(name)) {
                    String sql = (String) args[0];
                    return createPreparedStatement(sql);
                }
                if ("close".equals(name)) {
                    return null;
                }
                if ("setAutoCommit".equals(name) || "commit".equals(name) || "rollback".equals(name)) {
                    return null;
                }
                if ("getAutoCommit".equals(name)) {
                    return true;
                }
                if ("unwrap".equals(name)) {
                    throw new SQLException("Unsupported unwrap");
                }
                if ("isWrapperFor".equals(name)) {
                    return false;
                }
                throw new UnsupportedOperationException("Unsupported Connection method: " + name);
            };

            return (Connection) Proxy.newProxyInstance(
                Connection.class.getClassLoader(),
                new Class<?>[] {Connection.class},
                connectionHandler
            );
        }

        private PreparedStatement createPreparedStatement(String sql) {
            List<Object> params = new ArrayList<>();
            String normalized = sql.toLowerCase();

            InvocationHandler psHandler = (proxy, method, args) -> {
                String name = method.getName();
                if ("setString".equals(name) || "setBoolean".equals(name)) {
                    int index = (int) args[0];
                    while (params.size() < index) {
                        params.add(null);
                    }
                    params.set(index - 1, args[1]);
                    return null;
                }
                if ("executeQuery".equals(name)) {
                    if (normalized.contains("from transactions") && normalized.contains("status = 'reversed'")) {
                        String stan = (String) params.get(0);
                        String rrn = (String) params.get(1);
                        TxRecord tx = transactions.get(new Key(stan, rrn));
                        boolean exists = tx != null && (Objects.equals("REVERSED", tx.status) || tx.isReversal);
                        return createResultSet(exists ? List.of(Map.of("one", "1")) : List.of());
                    }
                    return createResultSet(List.of());
                }
                if ("executeUpdate".equals(name)) {
                    if (normalized.contains("update transactions")) {
                        String status = (String) params.get(0);
                        String finalStatus = (String) params.get(1);
                        String rc = (String) params.get(2);
                        boolean isReversal = (Boolean) params.get(3);
                        String stan = (String) params.get(4);
                        String rrn = (String) params.get(5);
                        transactions.put(new Key(stan, rrn), new TxRecord(status, isReversal, rc, finalStatus));
                        return 1;
                    }
                    if (normalized.contains("insert into transaction_events")) {
                        String stan = (String) params.get(0);
                        String rrn = (String) params.get(1);
                        String eventType = (String) params.get(3);
                        boolean duplicate = events.stream().anyMatch(e -> e.stan.equals(stan) && e.rrn.equals(rrn) && e.eventType.equals(eventType));
                        if (!duplicate) {
                            events.add(new EventRecord(
                                stan,
                                rrn,
                                eventType,
                                (String) params.get(4),
                                (String) params.get(5),
                                (String) params.get(6)
                            ));
                            return 1;
                        }
                        return 0;
                    }
                    return 0;
                }
                if ("close".equals(name)) {
                    return null;
                }
                if ("unwrap".equals(name)) {
                    throw new SQLException("Unsupported unwrap");
                }
                if ("isWrapperFor".equals(name)) {
                    return false;
                }
                throw new UnsupportedOperationException("Unsupported PreparedStatement method: " + name);
            };

            return (PreparedStatement) Proxy.newProxyInstance(
                PreparedStatement.class.getClassLoader(),
                new Class<?>[] {PreparedStatement.class},
                psHandler
            );
        }

        private ResultSet createResultSet(List<Map<String, String>> rows) {
            final int[] cursor = {-1};

            InvocationHandler rsHandler = (proxy, method, args) -> {
                String name = method.getName();
                if ("next".equals(name)) {
                    cursor[0]++;
                    return cursor[0] < rows.size();
                }
                if ("getString".equals(name)) {
                    String column = (String) args[0];
                    return rows.get(cursor[0]).get(column);
                }
                if ("close".equals(name)) {
                    return null;
                }
                if ("unwrap".equals(name)) {
                    throw new SQLException("Unsupported unwrap");
                }
                if ("isWrapperFor".equals(name)) {
                    return false;
                }
                throw new UnsupportedOperationException("Unsupported ResultSet method: " + name);
            };

            return (ResultSet) Proxy.newProxyInstance(
                ResultSet.class.getClassLoader(),
                new Class<?>[] {ResultSet.class},
                rsHandler
            );
        }

        @Override
        public Connection getConnection(String username, String password) {
            throw new UnsupportedOperationException();
        }

        @Override
        public PrintWriter getLogWriter() {
            return null;
        }

        @Override
        public void setLogWriter(PrintWriter out) {
        }

        @Override
        public void setLoginTimeout(int seconds) {
        }

        @Override
        public int getLoginTimeout() {
            return 0;
        }

        @Override
        public Logger getParentLogger() throws SQLFeatureNotSupportedException {
            throw new SQLFeatureNotSupportedException();
        }

        @Override
        public <T> T unwrap(Class<T> iface) {
            throw new UnsupportedOperationException();
        }

        @Override
        public boolean isWrapperFor(Class<?> iface) {
            return false;
        }
    }

    private static final class StubMux implements MUX {
        private final Deque<Object> outcomes;
        private int calls;

        private StubMux(List<Object> outcomes) {
            this.outcomes = new ArrayDeque<>(outcomes);
        }

        private int requestCalls() {
            return calls;
        }

        @Override
        public ISOMsg request(ISOMsg request, long timeout) {
            calls++;
            Object next = outcomes.isEmpty() ? null : outcomes.removeFirst();
            if (next == TIMEOUT) {
                return null;
            }
            if (next instanceof RuntimeException runtimeException) {
                throw runtimeException;
            }
            return (ISOMsg) next;
        }

        @Override
        public void request(ISOMsg m, long timeout, ISOResponseListener rl, Object handBack) {
            throw new UnsupportedOperationException();
        }

        @Override
        public void send(ISOMsg m) {
            throw new UnsupportedOperationException();
        }

        @Override
        public boolean isConnected() {
            return true;
        }
    }
}
