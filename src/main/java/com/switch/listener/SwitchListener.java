package com.qswitch.listener;

import com.qswitch.dao.EventDAO;
import com.qswitch.dao.TransactionDAO;
import com.qswitch.dao.ValidationEventDAO;
import com.qswitch.fraud.FraudDecision;
import com.qswitch.fraud.FraudEngine;
import com.qswitch.model.Transaction;
import com.qswitch.recon.DBConnectionManager;
import com.qswitch.routing.BinDAO;
import com.qswitch.routing.RoutingEngine;
import com.qswitch.service.SecurityService;
import com.qswitch.service.TransactionService;
import com.qswitch.validation.AuthorizationRulesEngine;
import com.qswitch.validation.IsoValidationEngine;
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
    private final FraudEngine fraudEngine;
    private final BinDAO binDAO;
    private final IsoValidationEngine isoValidationEngine;
    private final AuthorizationRulesEngine authRulesEngine;
    private final ValidationEventDAO validationEventDAO;
    private boolean debugEnabled;

    public SwitchListener() {
        this(
            new TransactionService(new TransactionDAO(), new EventDAO()),
            new SecurityService(),
            new FraudEngine(),
            new BinDAO(DBConnectionManager.getDataSource()),
            new IsoValidationEngine(),
            new AuthorizationRulesEngine(),
            new ValidationEventDAO()
        );
    }

    @Override
    protected void startService() throws Exception {
        super.startService();
        debugEnabled = isHexDebugEnabled();
        getLog().info("SwitchListener initialized with default services");
    }

    public SwitchListener(TransactionService transactionService) {
        this(transactionService, new SecurityService(), new FraudEngine(), new BinDAO(DBConnectionManager.getDataSource()));
    }

    public SwitchListener(TransactionService transactionService, SecurityService securityService) {
        this(transactionService, securityService, new FraudEngine(), new BinDAO(DBConnectionManager.getDataSource()));
    }

    public SwitchListener(TransactionService transactionService, SecurityService securityService, BinDAO binDAO) {
        this(transactionService, securityService, new FraudEngine(), binDAO);
    }

    public SwitchListener(TransactionService transactionService, SecurityService securityService, FraudEngine fraudEngine, BinDAO binDAO) {
        this(transactionService, securityService, fraudEngine, binDAO, new IsoValidationEngine(), new AuthorizationRulesEngine(), new ValidationEventDAO());
    }

    public SwitchListener(TransactionService transactionService, SecurityService securityService,
                          FraudEngine fraudEngine, BinDAO binDAO,
                          IsoValidationEngine isoValidationEngine, AuthorizationRulesEngine authRulesEngine) {
        this(transactionService, securityService, fraudEngine, binDAO, isoValidationEngine, authRulesEngine, new ValidationEventDAO());
    }

    public SwitchListener(TransactionService transactionService, SecurityService securityService,
                          FraudEngine fraudEngine, BinDAO binDAO,
                          IsoValidationEngine isoValidationEngine, AuthorizationRulesEngine authRulesEngine,
                          ValidationEventDAO validationEventDAO) {
        this.transactionService = transactionService;
        this.securityService = securityService;
        this.fraudEngine = fraudEngine;
        this.binDAO = binDAO;
        this.isoValidationEngine = isoValidationEngine;
        this.authRulesEngine = authRulesEngine;
        this.validationEventDAO = validationEventDAO;
    }

    @Override
    public boolean process(ISOSource source, ISOMsg request) {
        try {
            logIncomingRequest(request);

            String stan = request.hasField(11) ? request.getString(11) : "000000";
            String rrn  = request.hasField(37) ? request.getString(37) : "000000000000";
            long amount = parseAmount(request.hasField(4) ? request.getString(4) : "0");
            transactionService.persistIncomingRequest(request, stan, rrn, amount);

            // ---------------- MANDATORY FIELD VALIDATION ----------------
            String mti = request.getMTI();
            if ("0200".equals(mti) || "0201".equals(mti)) {
                if (!request.hasField(2) || request.getString(2) == null || request.getString(2).trim().isEmpty()) {
                    getLog().warn("REJECTED: 0200 missing mandatory PAN (F2) STAN=" + stan);
                    ISOMsg resp = buildBaseResponse(request, stan, rrn);
                    resp.set(39, "30"); // mandatory data missing
                    safeSend(source, request, resp, "VALIDATION REJECT", "VALIDATION_REJECT");
                    return true;
                }
                if (!request.hasField(4) || request.getString(4) == null || request.getString(4).trim().isEmpty()) {
                    getLog().warn("REJECTED: 0200 missing mandatory Amount (F4) STAN=" + stan);
                    ISOMsg resp = buildBaseResponse(request, stan, rrn);
                    resp.set(39, "30");
                    safeSend(source, request, resp, "VALIDATION REJECT", "VALIDATION_REJECT");
                    return true;
                }
                if (!request.hasField(11) || request.getString(11) == null || request.getString(11).trim().isEmpty()) {
                    getLog().warn("REJECTED: 0200 missing mandatory STAN (F11) STAN=" + stan);
                    ISOMsg resp = buildBaseResponse(request, stan, rrn);
                    resp.set(39, "30");
                    safeSend(source, request, resp, "VALIDATION REJECT", "VALIDATION_REJECT");
                    return true;
                }
                if (!request.hasField(41) || request.getString(41) == null || request.getString(41).trim().isEmpty()) {
                    getLog().warn("REJECTED: 0200 missing mandatory Terminal ID (F41) STAN=" + stan);
                    ISOMsg resp = buildBaseResponse(request, stan, rrn);
                    resp.set(39, "30");
                    safeSend(source, request, resp, "VALIDATION REJECT", "VALIDATION_REJECT");
                    return true;
                }
            }

            // ---------------- PHASE 09: ISO FIELD VALIDATION ----------------
            // Resolve scheme early for validation (may be null before routing, default LOCAL)
            String preRoutingScheme = resolveSchemeForValidation(request);
            IsoValidationEngine.ValidationResult isoValidation = isoValidationEngine.validate(request, preRoutingScheme);
            if (!isoValidation.isValid()) {
                getLog().warn("ISO VALIDATION REJECT STAN=" + stan
                    + " scheme=" + preRoutingScheme
                    + " errors=" + isoValidation.getErrors());
                validationEventDAO.logFail(stan, rrn, mti, preRoutingScheme, "ISO_VALIDATION",
                    isoValidation.getErrors(), isoValidation.getRejectCode());
                ISOMsg resp = buildBaseResponse(request, stan, rrn);
                resp.set(39, isoValidation.getRejectCode());
                safeSend(source, request, resp, "ISO VALIDATION REJECT", "VALIDATION_REJECT");
                return true;
            }
            validationEventDAO.logPass(stan, rrn, mti, preRoutingScheme, "ISO_VALIDATION");

            // ---------------- PHASE 09: AUTHORIZATION RULES ----------------
            AuthorizationRulesEngine.AuthDecision authDecision =
                authRulesEngine.evaluate(request, preRoutingScheme, amount);
            if (!authDecision.isApproved()) {
                getLog().warn("AUTH RULE REJECT STAN=" + stan
                    + " reason=" + authDecision.getReason());
                java.util.List<String> authErrors = java.util.Collections.singletonList(authDecision.getReason());
                validationEventDAO.logFail(stan, rrn, mti, preRoutingScheme, "AUTH_RULES",
                    authErrors, authDecision.getRejectCode());
                ISOMsg resp = buildBaseResponse(request, stan, rrn);
                resp.set(39, authDecision.getRejectCode());
                safeSend(source, request, resp, "AUTH RULE REJECT", "AUTH_RULE_REJECT");
                return true;
            }
            validationEventDAO.logPass(stan, rrn, mti, preRoutingScheme, "AUTH_RULES");

            // ---------------- SECURITY ----------------
            SecurityService.ValidationResult security = securityService.validateRequestSecurity(request);
            if (!security.isValid()) {
                ISOMsg resp = buildBaseResponse(request, stan, rrn);
                resp.set(39, security.getResponseCode());
                safeSend(source, request, resp, "SECURITY DECLINE", "SECURITY_DECLINE");
                return true;
            }

            FraudDecision fraudDecision = fraudEngine.evaluate(request, amount);
            if (fraudDecision.isDecline()) {
                transactionService.persistFraudDecision(request, fraudDecision);
                ISOMsg resp = buildBaseResponse(request, stan, rrn);
                resp.set(39, "05");
                safeSend(source, request, resp, "FRAUD DECLINE", "FRAUD_DECLINE");
                return true;
            }
            if (fraudDecision.isFlag()) {
                transactionService.persistFraudDecision(request, fraudDecision);
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

    // ---------------- PHASE 09 HELPERS ----------------

    /**
     * Quick pre-routing scheme resolution: look up PAN BIN in BinDAO to get the scheme.
     * Falls back to "LOCAL" if BIN not found or PAN absent.
     */
    private String resolveSchemeForValidation(ISOMsg request) {
        try {
            String pan = request.hasField(2) ? request.getString(2) : null;
            if (pan != null && pan.length() >= 6) {
                String bin = pan.substring(0, 6);
                com.qswitch.routing.Bin binEntry = binDAO.findByBin(bin);
                if (binEntry != null && binEntry.getScheme() != null) {
                    return binEntry.getScheme().toUpperCase(java.util.Locale.ROOT);
                }
            }
        } catch (Exception ignored) {}
        return "LOCAL";
    }
}

