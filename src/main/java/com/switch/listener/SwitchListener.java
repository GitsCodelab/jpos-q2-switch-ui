package com.qswitch.listener;

import com.qswitch.dao.EventDAO;
import com.qswitch.dao.TransactionDAO;
import com.qswitch.model.Transaction;
import com.qswitch.service.SecurityService;
import com.qswitch.service.TransactionService;
import org.jpos.iso.ISOException;
import org.jpos.iso.ISOMsg;
import org.jpos.iso.ISORequestListener;
import org.jpos.iso.ISOSource;
import org.jpos.q2.QBeanSupport;
import org.jpos.q2.iso.QMUX;
import org.jpos.util.NameRegistrar;

public class SwitchListener extends QBeanSupport implements ISORequestListener {
    private final TransactionService transactionService;
    private final SecurityService securityService;

    public SwitchListener() {
        this(new TransactionService(new TransactionDAO(), new EventDAO()), new SecurityService());
    }

    public SwitchListener(TransactionService transactionService) {
        this(transactionService, new SecurityService());
    }

    public SwitchListener(TransactionService transactionService, SecurityService securityService) {
        this.transactionService = transactionService;
        this.securityService = securityService;
    }

    @Override
    public boolean process(ISOSource source, ISOMsg request) {
        try {
            String stan = request.hasField(11) ? request.getString(11) : "000000";
            String rrn = request.hasField(37) ? request.getString(37) : "000000000000";
            long amount = parseAmount(request.hasField(4) ? request.getString(4) : "0");

            SecurityService.ValidationResult security = securityService.validateRequestSecurity(request);
            if (!security.isValid()) {
                ISOMsg securityDecline = (ISOMsg) request.clone();
                securityDecline.setMTI(buildResponseMTI(request.getMTI()));
                securityDecline.set(39, security.getResponseCode());
                securityDecline.set(11, stan);
                securityDecline.set(37, rrn);
                source.send(securityDecline);
                return true;
            }

            ISOMsg muxResponse = requestThroughMux(request);
            if (muxResponse != null) {
                source.send(muxResponse);
                return true;
            }

            Transaction result = transactionService.handleAuthorization(stan, rrn, amount);

            ISOMsg response = (ISOMsg) request.clone();
            response.setMTI(buildResponseMTI(request.getMTI()));
            response.set(39, result.getResponseCode());
            response.set(11, result.getStan());
            response.set(37, result.getRrn());

            if (securityService.hasAnySecurityField(request)) {
                response.set(64, securityService.generateResponseMac(request, response));
            }

            source.send(response);
            return true;
        } catch (Exception e) {
            // return false;
            try {
                ISOMsg resp = (ISOMsg) request.clone();
                resp.setMTI(buildResponseMTI(request.getMTI()));
                resp.set(39, "96");
                source.send(resp);
            } catch (Exception ignored) {
                return false;
            }
            return true;

        }
    }

    private ISOMsg requestThroughMux(ISOMsg request) {
        try {
            QMUX mux = (QMUX) NameRegistrar.get("mux.acquirer-mux");
            ISOMsg response = mux.request((ISOMsg) request.clone(), 30000);
            if (response == null) {
                ISOMsg timeout = (ISOMsg) request.clone();
                timeout.setMTI(buildResponseMTI(request.getMTI()));
                timeout.set(39, "91");
                return timeout;
            }
            return response;
        } catch (NameRegistrar.NotFoundException ignored) {
            return null;
        } catch (Exception e) {
            return null;
        }
    }

    private String buildResponseMTI(String requestMti) {
        if (requestMti == null || requestMti.length() != 4) {
            return "0210";
        }
        char[] value = requestMti.toCharArray();
        value[2] = '1';
        return new String(value);
    }

    private long parseAmount(String amountField) throws ISOException {
        try {
            return Long.parseLong(amountField.trim());
        } catch (NumberFormatException e) {
            throw new ISOException("Invalid field 4 amount", e);
        }
    }
}
