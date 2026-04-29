package com.qswitch.recon;

import org.jpos.iso.MUX;
import org.jpos.util.NameRegistrar;

import javax.sql.DataSource;
import java.util.List;

public final class AutoReversalRunner {

    private AutoReversalRunner() {
    }

    public static void main(String[] args) {
        String muxName = System.getProperty("recon.mux.name", "mux.acquirer-mux");
        int thresholdSeconds = Integer.parseInt(System.getProperty("recon.reversal.threshold.seconds", "60"));

        try {
            DataSource dataSource = DBConnectionManager.getDataSource();
            MUX mux = (MUX) NameRegistrar.get(muxName);

            ReconciliationService recon = new ReconciliationService(dataSource);
            AutoReversalService service = new AutoReversalService(dataSource, mux);

            List<ReconciliationIssue> candidates = recon.findReversalCandidates(thresholdSeconds);
            int processed = service.processReversals(candidates);

            System.out.println("Auto-reversal completed. candidates=" + candidates.size() + " processed=" + processed);
        } catch (Exception e) {
            throw new IllegalStateException("Auto-reversal runner failed", e);
        }
    }
}
