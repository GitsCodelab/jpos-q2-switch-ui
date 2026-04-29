package com.qswitch.routing;

import org.jpos.iso.ISOMsg;
import org.jpos.iso.ISOResponseListener;
import org.jpos.iso.MUX;
import org.junit.jupiter.api.Test;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RoutingEngineTest {

    private static final Object TIMEOUT = new Object();

    @Test
    void shouldReturnNoDecisionWhenPanMissing() throws Exception {
        RoutingEngine engine = new RoutingEngine(stubBinDao(), new StubMux(List.of()));
        ISOMsg request = request("0200", null, "000000000100");

        RoutingEngine.RouteResult result = engine.routeDetailed(request);

        assertFalse(result.isDecisionMade());
        assertFalse(result.hasResponse());
    }

    @Test
    void shouldDeclineWith14WhenBinMissing() throws Exception {
        RoutingEngine engine = new RoutingEngine(stubBinDao(), new StubMux(List.of()));
        ISOMsg request = request("0200", "9999991234567890", "000000000100");

        ISOMsg response = engine.route(request);

        assertEquals("0210", response.getMTI());
        assertEquals("14", response.getString(39));
    }

    @Test
    void shouldApproveLocalBin() throws Exception {
        RoutingEngine engine = new RoutingEngine(stubBinDao(bin("123456", "LOCAL", "BANK_A")), new StubMux(List.of()));
        ISOMsg request = request("0200", "1234561234567890", "000000000100");

        RoutingEngine.RouteResult result = engine.routeDetailed(request);

        assertTrue(result.isDecisionMade());
        assertTrue(result.hasResponse());
        assertFalse(result.isRemote());
        assertEquals("BANK_A", result.getIssuerId());
        assertEquals("00", result.getResponse().getString(39));
    }

    @Test
    void shouldApplyFraudDeclineForLargeLocalAmount() throws Exception {
        RoutingEngine engine = new RoutingEngine(stubBinDao(bin("123456", "LOCAL", "BANK_A")), new StubMux(List.of()));
        ISOMsg request = request("0200", "1234561234567890", "000000100001");

        ISOMsg response = engine.route(request);

        assertEquals("05", response.getString(39));
    }

    @Test
    void shouldRouteVisaToMux() throws Exception {
        ISOMsg muxResponse = new ISOMsg();
        muxResponse.setMTI("0210");
        muxResponse.set(39, "00");

        StubMux mux = new StubMux(List.of(muxResponse));
        RoutingEngine engine = new RoutingEngine(stubBinDao(bin("654321", "VISA", "BANK_B")), mux);
        ISOMsg request = request("0200", "6543211234567890", "000000000100");

        RoutingEngine.RouteResult result = engine.routeDetailed(request);

        assertTrue(result.isDecisionMade());
        assertTrue(result.hasResponse());
        assertTrue(result.isRemote());
        assertEquals("BANK_B", result.getIssuerId());
        assertEquals(1, mux.calls());
        assertEquals("00", result.getResponse().getString(39));
    }

    @Test
    void shouldReturn91OnMuxTimeout() throws Exception {
        StubMux mux = new StubMux(List.of(TIMEOUT));
        RoutingEngine engine = new RoutingEngine(stubBinDao(bin("654321", "MC", "BANK_C")), mux);
        ISOMsg request = request("0200", "6543211234567890", "000000000100");

        RoutingEngine.RouteResult result = engine.routeDetailed(request);

        assertTrue(result.isDecisionMade());
        assertTrue(result.hasResponse());
        assertTrue(result.isRemote());
        assertTrue(result.isTimeout());
        assertEquals("91", result.getResponse().getString(39));
    }

    private static BinDAO stubBinDao(Bin... bins) {
        return new BinDAO(null) {
            @Override
            public Bin findByBin(String bin) {
                for (Bin b : bins) {
                    if (b.getBin().equals(bin)) {
                        return b;
                    }
                }
                return null;
            }
        };
    }

    private static Bin bin(String value, String scheme, String issuerId) {
        Bin b = new Bin();
        b.setBin(value);
        b.setScheme(scheme);
        b.setIssuerId(issuerId);
        return b;
    }

    private static ISOMsg request(String mti, String pan, String amount) throws Exception {
        ISOMsg request = new ISOMsg();
        request.setMTI(mti);
        if (pan != null) {
            request.set(2, pan);
        }
        request.set(4, amount);
        request.set(11, "123456");
        request.set(37, "123456123456");
        return request;
    }

    private static final class StubMux implements MUX {
        private final Deque<Object> outcomes;
        private int callCount;

        private StubMux(List<Object> outcomes) {
            this.outcomes = new ArrayDeque<>(outcomes);
        }

        private int calls() {
            return callCount;
        }

        @Override
        public ISOMsg request(ISOMsg request, long timeout) {
            callCount++;
            Object next = outcomes.isEmpty() ? null : outcomes.removeFirst();
            if (next == TIMEOUT) {
                return null;
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
