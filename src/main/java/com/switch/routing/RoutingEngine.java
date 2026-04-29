package com.qswitch.routing;

import org.jpos.iso.ISOMsg;
import org.jpos.iso.MUX;

public class RoutingEngine {

    private static final long REMOTE_TIMEOUT_MS = 5000L;
    private static final long FRAUD_LIMIT_MINOR_UNITS = 100_000L;

    private final BinDAO binDAO;
    private final MUX mux;

    public RoutingEngine(BinDAO binDAO, MUX mux) {
        this.binDAO = binDAO;
        this.mux = mux;
    }

    public ISOMsg route(ISOMsg request) throws Exception {
        return routeDetailed(request).getResponse();
    }

    public RouteResult routeDetailed(ISOMsg request) throws Exception {
        String pan = safeField(request, 2);
        if (pan == null || pan.length() < 6) {
            return RouteResult.noDecision();
        }

        String binValue = pan.substring(0, 6);
        Bin bin = binDAO.findByBin(binValue);

        if (bin == null) {
            return RouteResult.withResponse(buildError(request, "14"), null, null, false, false);
        }

        String scheme = normalizeScheme(bin.getScheme());

        switch (scheme) {
            case "LOCAL":
                return RouteResult.withResponse(processLocal(request), scheme, bin.getIssuerId(), false, false);
            case "VISA":
            case "MC":
                if (mux == null) {
                    return RouteResult.withResponse(buildError(request, "91"), scheme, bin.getIssuerId(), true, true);
                }
                ISOMsg routed = mux.request((ISOMsg) request.clone(), REMOTE_TIMEOUT_MS);
                if (routed == null) {
                    return RouteResult.withResponse(buildError(request, "91"), scheme, bin.getIssuerId(), true, true);
                }
                boolean timeout = "91".equals(safeField(routed, 39));
                return RouteResult.withResponse(routed, scheme, bin.getIssuerId(), timeout, true);
            default:
                return RouteResult.withResponse(buildError(request, "96"), scheme, bin.getIssuerId(), false, false);
        }
    }

    private ISOMsg processLocal(ISOMsg request) throws Exception {
        ISOMsg resp = (ISOMsg) request.clone();
        resp.setMTI(buildResponseMTI(request));

        long amount = parseAmountOrZero(safeField(request, 4));
        if (amount > FRAUD_LIMIT_MINOR_UNITS) {
            resp.set(39, "05");
        } else {
            resp.set(39, "00");
        }
        return resp;
    }

    private ISOMsg buildError(ISOMsg req, String rc) throws Exception {
        ISOMsg resp = (ISOMsg) req.clone();
        resp.setMTI(buildResponseMTI(req));
        resp.set(39, rc);
        return resp;
    }

    private String buildResponseMTI(ISOMsg req) {
        try {
            String mti = req.getMTI();
            if (mti != null && mti.length() == 4) {
                char[] value = mti.toCharArray();
                value[2] = '1';
                return new String(value);
            }
            return "0210";
        } catch (Exception ignored) {
            return "0210";
        }
    }

    private String safeField(ISOMsg msg, int field) {
        try {
            if (!msg.hasField(field)) {
                return null;
            }
            return msg.getString(field);
        } catch (Exception e) {
            return null;
        }
    }

    private long parseAmountOrZero(String amount) {
        if (amount == null || amount.isBlank()) {
            return 0L;
        }
        try {
            return Long.parseLong(amount.trim());
        } catch (NumberFormatException e) {
            return 0L;
        }
    }

    private String normalizeScheme(String scheme) {
        if (scheme == null) {
            return "";
        }
        return scheme.trim().toUpperCase();
    }

    public static final class RouteResult {
        private final ISOMsg response;
        private final String scheme;
        private final String issuerId;
        private final boolean timeout;
        private final boolean remote;
        private final boolean decisionMade;

        private RouteResult(ISOMsg response, String scheme, String issuerId, boolean timeout, boolean remote, boolean decisionMade) {
            this.response = response;
            this.scheme = scheme;
            this.issuerId = issuerId;
            this.timeout = timeout;
            this.remote = remote;
            this.decisionMade = decisionMade;
        }

        public static RouteResult noDecision() {
            return new RouteResult(null, null, null, false, false, false);
        }

        public static RouteResult withResponse(ISOMsg response, String scheme, String issuerId, boolean timeout, boolean remote) {
            return new RouteResult(response, scheme, issuerId, timeout, remote, true);
        }

        public ISOMsg getResponse() {
            return response;
        }

        public String getScheme() {
            return scheme;
        }

        public String getIssuerId() {
            return issuerId;
        }

        public boolean isTimeout() {
            return timeout;
        }

        public boolean isRemote() {
            return remote;
        }

        public boolean isDecisionMade() {
            return decisionMade;
        }

        public boolean hasResponse() {
            return response != null;
        }
    }
}
