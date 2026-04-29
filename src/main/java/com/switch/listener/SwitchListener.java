package com.qswitch.listener;

import com.qswitch.dao.EventDAO;
import com.qswitch.dao.TransactionDAO;
import com.qswitch.model.Transaction;
import com.qswitch.recon.DBConnectionManager;
import com.qswitch.routing.BinDAO;
import com.qswitch.routing.RoutingEngine;
import com.qswitch.service.SecurityService;
import com.qswitch.service.TransactionService;
import org.jpos.iso.ISOException;
import org.jpos.iso.ISOMsg;
import org.jpos.iso.ISORequestListener;
import org.jpos.iso.ISOSource;
import org.jpos.iso.ISOUtil;
import org.jpos.iso.MUX;
import org.jpos.q2.QBeanSupport;
import org.jpos.q2.iso.QMUX;
import org.jpos.util.NameRegistrar;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;

public class SwitchListener extends QBeanSupport implements ISORequestListener {

    private final TransactionService transactionService;
    private final SecurityService securityService;
    private final BinDAO binDAO;
    private boolean debugEnabled;

    public SwitchListener() {
        this(new TransactionService(new TransactionDAO(), new EventDAO()), new SecurityService(), new BinDAO(DBConnectionManager.getDataSource()));
    }

    @Override
    protected void startService() throws Exception {
        super.startService();
        debugEnabled = isHexDebugEnabled();
        getLog().info("SwitchListener initialized with default services");
    }

    public SwitchListener(TransactionService transactionService) {
        this(transactionService, new SecurityService(), new BinDAO(DBConnectionManager.getDataSource()));
    }

    public SwitchListener(TransactionService transactionService, SecurityService securityService) {
        this(transactionService, securityService, new BinDAO(DBConnectionManager.getDataSource()));
    }

    public SwitchListener(TransactionService transactionService, SecurityService securityService, BinDAO binDAO) {
        this.transactionService = transactionService;
        this.securityService = securityService;
        this.binDAO = binDAO;
    }

    @Override
    public boolean process(ISOSource source, ISOMsg request) {
        try {
            logIncomingRequest(request);

            String stan = request.hasField(11) ? request.getString(11) : "000000";
            String rrn  = request.hasField(37) ? request.getString(37) : "000000000000";
            long amount = parseAmount(request.hasField(4) ? request.getString(4) : "0");
            transactionService.persistIncomingRequest(request, stan, rrn, amount);

            // ---------------- SECURITY ----------------
            SecurityService.ValidationResult security = securityService.validateRequestSecurity(request);
            if (!security.isValid()) {
                ISOMsg resp = buildBaseResponse(request, stan, rrn);
                resp.set(39, security.getResponseCode());
                safeSend(source, request, resp, "SECURITY DECLINE", "SECURITY_DECLINE");
                return true;
            }

            // ---------------- BIN ROUTING ----------------
            RoutingEngine.RouteResult routeResult = requestThroughRouting(request);
            if (routeResult.isDecisionMade()) {
                transactionService.updateRoutingMetadata(stan, rrn, routeResult.getIssuerId(), routeResult.getScheme());

                if (routeResult.hasResponse()) {
                    String eventType = resolveRoutedEventType(routeResult);
                    if (routeResult.isTimeout()) {
                        int retryCount = transactionService.incrementRetryCount(stan, rrn);
                        if (retryCount < 2) {
                            getLog().warn("Routing timeout, retrying STAN=" + stan + " retryCount=" + retryCount);
                            routeResult = requestThroughRouting(request);
                            if (routeResult.isDecisionMade()) {
                                transactionService.updateRoutingMetadata(stan, rrn, routeResult.getIssuerId(), routeResult.getScheme());
                                if (routeResult.isTimeout()) {
                                    transactionService.incrementRetryCount(stan, rrn);
                                    getLog().warn("Routing timeout threshold reached, reversal should be triggered for STAN=" + stan);
                                }
                                if (routeResult.hasResponse()) {
                                    safeSend(source, request, routeResult.getResponse(), "ROUTED RESPONSE", resolveRoutedEventType(routeResult));
                                    return true;
                                }
                            }
                        }
                    }

                    safeSend(source, request, routeResult.getResponse(), "ROUTED RESPONSE", eventType);
                    return true;
                }
            }

            // ---------------- LEGACY FALLBACK ----------------
            ISOMsg muxResponse = requestThroughMux(request);
            if (muxResponse != null) {
                String eventType = "91".equals(muxResponse.getString(39)) ? "TIMEOUT" : "MUX_RESPONSE";
                safeSend(source, request, muxResponse, "MUX RESPONSE", eventType);
                return true;
            }

            // ---------------- BUSINESS LOGIC ----------------
            Transaction result = transactionService.handleAuthorization(stan, rrn, amount);

            ISOMsg response = buildBaseResponse(request, result.getStan(), result.getRrn());
            response.set(39, result.getResponseCode());

            if (securityService.hasAnySecurityField(request)) {
                response.set(64, securityService.generateResponseMac(request, response));
            }

            safeSend(source, request, response, "LOCAL RESPONSE", "LOCAL_RESPONSE");
            return true;

        } catch (Exception e) {
            getLog().error("Processing error", e);
            try {
                ISOMsg resp = buildBaseResponse(request, "000000", "000000000000");
                resp.set(39, "96");
                safeSend(source, request, resp, "EXCEPTION RESPONSE", "EXCEPTION_RESPONSE");
            } catch (Exception ignored) {
                return false;
            }
            return true;
        }
    }

    private void logIncomingRequest(ISOMsg m) throws ISOException {
        String stan = m.hasField(11) ? m.getString(11) : "N/A";
        getLog().info("MTI=" + m.getMTI() + " STAN=" + stan);

        ISOMsg safe = (ISOMsg) m.clone();
        safe.unset(2);
        safe.unset(52);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        PrintStream ps = new PrintStream(baos, true, StandardCharsets.UTF_8);
        safe.dump(ps, "");
        getLog().info(">>> REQUEST DUMP START >>>\n" + baos.toString(StandardCharsets.UTF_8) + "\n>>> REQUEST DUMP END >>>");

        if (isHexDebugEnabled()) {
            getLog().info("HEX=" + ISOUtil.hexString(m.pack()));
        }
    }

    private boolean isHexDebugEnabled() {
        return debugEnabled || Boolean.parseBoolean(System.getProperty("switch.listener.debug", "false"));
    }

    // ---------------- SAFE SEND ----------------
    private void safeSend(ISOSource source, ISOMsg request, ISOMsg resp, String label, String eventType) {
        try {
            transactionService.persistOutgoingResponse(request, resp, eventType);
        } catch (Exception e) {
            getLog().error("Failed to persist response", e);
        }

        try {
            source.send(resp);
            getLog().info(
                ">>> SENT [" + label + "] MTI=" + resp.getMTI() +
                " RC=" + resp.getString(39) +
                " STAN=" + (resp.hasField(11) ? resp.getString(11) : "N/A") +
                " RRN=" + (resp.hasField(37) ? resp.getString(37) : "N/A")
            );
        } catch (Exception e) {
            getLog().error("Failed to send response", e);
        }
    }

    // ---------------- BASE RESPONSE BUILDER ----------------
    private ISOMsg buildBaseResponse(ISOMsg request, String stan, String rrn) throws ISOException {
        ISOMsg resp = (ISOMsg) request.clone();
        resp.setMTI(buildResponseMTI(request.getMTI()));
        resp.set(11, stan);
        resp.set(37, rrn);
        return resp;
    }

    // ---------------- MUX ----------------
    protected MUX lookupMux() throws NameRegistrar.NotFoundException {
        return (QMUX) NameRegistrar.get("mux.acquirer-mux");
    }

    private RoutingEngine.RouteResult requestThroughRouting(ISOMsg request) {
        try {
            MUX mux;
            try {
                mux = lookupMux();
            } catch (NameRegistrar.NotFoundException e) {
                mux = null;
            }
            RoutingEngine routingEngine = new RoutingEngine(binDAO, mux);
            return routingEngine.routeDetailed(request);
        } catch (Exception e) {
            getLog().error("Routing engine error", e);
            return RoutingEngine.RouteResult.noDecision();
        }
    }

    private String resolveRoutedEventType(RoutingEngine.RouteResult routeResult) {
        if (routeResult.isTimeout()) {
            return "TIMEOUT";
        }
        return routeResult.isRemote() ? "MUX_RESPONSE" : "LOCAL_RESPONSE";
    }

    private ISOMsg requestThroughMux(ISOMsg request) {
        try {
            MUX mux = lookupMux();
            ISOMsg response = mux.request((ISOMsg) request.clone(), 30000);

            if (response == null) {
                ISOMsg timeout = (ISOMsg) request.clone();
                timeout.setMTI(buildResponseMTI(request.getMTI()));
                timeout.set(39, "91");
                return timeout;
            }
            return response;

        } catch (NameRegistrar.NotFoundException ignored) {
            getLog().warn("MUX not found -> fallback to local processing");
            return null;
        } catch (Exception e) {
            getLog().error("MUX error", e);
            return null;
        }
    }

    // ---------------- MTI ----------------
    private String buildResponseMTI(String requestMti) {
        if (requestMti == null || requestMti.length() != 4) {
            return "0210";
        }
        char[] value = requestMti.toCharArray();
        value[2] = '1';
        return new String(value);
    }

    // ---------------- AMOUNT ----------------
    private long parseAmount(String amountField) throws ISOException {
        try {
            return Long.parseLong(amountField.trim());
        } catch (NumberFormatException e) {
            throw new ISOException("Invalid field 4 amount", e);
        }
    }
}
