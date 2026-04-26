package com.qswitch.listener;

import com.qswitch.dao.EventDAO;
import com.qswitch.dao.TransactionDAO;
import com.qswitch.service.TransactionService;
import org.jpos.iso.ISOMsg;
import org.jpos.iso.ISOSource;
import org.junit.jupiter.api.Test;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

class SwitchListenerTest {
    @Test
    void shouldRespondWithSuccessForValidAuthorization() throws Exception {
        TransactionService transactionService = new TransactionService(new TransactionDAO(), new EventDAO());
        SwitchListener listener = new SwitchListener(transactionService);

        CapturingSource source = new CapturingSource();
        ISOMsg request = new ISOMsg();
        request.setMTI("0200");
        request.set(4, "000000001000");
        request.set(11, "123456");
        request.set(37, "250011223344");

        boolean processed = listener.process(source, request);

        assertTrue(processed);
        assertEquals("0210", source.lastMessage.getMTI());
        assertEquals("00", source.lastMessage.getString(39));
        assertEquals("123456", source.lastMessage.getString(11));
        assertEquals("250011223344", source.lastMessage.getString(37));
    }

    @Test
    void shouldRespondWithDeclineForZeroAmount() throws Exception {
        TransactionService transactionService = new TransactionService(new TransactionDAO(), new EventDAO());
        SwitchListener listener = new SwitchListener(transactionService);

        CapturingSource source = new CapturingSource();
        ISOMsg request = new ISOMsg();
        request.setMTI("0200");
        request.set(4, "000000000000");
        request.set(11, "999999");
        request.set(37, "999999999999");

        boolean processed = listener.process(source, request);

        assertTrue(processed);
        assertEquals("0210", source.lastMessage.getMTI());
        assertEquals("13", source.lastMessage.getString(39));
    }

    @Test
    void shouldUseDefaultStanAndRrnWhenMissing() throws Exception {
        TransactionService transactionService = new TransactionService(new TransactionDAO(), new EventDAO());
        SwitchListener listener = new SwitchListener(transactionService);

        CapturingSource source = new CapturingSource();
        ISOMsg request = new ISOMsg();
        request.setMTI("0200");
        request.set(4, "000000001000");

        boolean processed = listener.process(source, request);

        assertTrue(processed);
        assertEquals("000000", source.lastMessage.getString(11));
        assertEquals("000000000000", source.lastMessage.getString(37));
    }

    @Test
    void shouldReturnFalseWhenAmountIsInvalid() throws Exception {
        TransactionService transactionService = new TransactionService(new TransactionDAO(), new EventDAO());
        SwitchListener listener = new SwitchListener(transactionService);

        CapturingSource source = new CapturingSource();
        ISOMsg request = new ISOMsg();
        request.setMTI("0200");
        request.set(4, "INVALID");
        request.set(11, "101010");
        request.set(37, "101010101010");

        boolean processed = listener.process(source, request);

        assertFalse(processed);
        assertNull(source.lastMessage);
    }

    @Test
    void shouldReturnFalseWhenRequestMtiMissing() throws Exception {
        TransactionService transactionService = new TransactionService(new TransactionDAO(), new EventDAO());
        SwitchListener listener = new SwitchListener(transactionService);

        CapturingSource source = new CapturingSource();
        ISOMsg request = new ISOMsg();
        request.set(4, "000000001000");
        request.set(11, "123456");
        request.set(37, "250011223344");

        boolean processed = listener.process(source, request);

        assertFalse(processed);
        assertNull(source.lastMessage);
    }

    private static class CapturingSource implements ISOSource {
        private ISOMsg lastMessage;

        @Override
        public void send(ISOMsg m) throws IOException {
            this.lastMessage = m;
        }

        @Override
        public boolean isConnected() {
            return true;
        }
    }
}
