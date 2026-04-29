package com.qswitch.routing;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

public class BinDAO {

    private final DataSource dataSource;

    public BinDAO(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    public Bin findByBin(String bin) {
        String sql = "SELECT bin, scheme, issuer_id FROM bins WHERE bin = ?";

        try (Connection c = dataSource.getConnection();
             PreparedStatement ps = c.prepareStatement(sql)) {

            ps.setString(1, bin);

            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return null;
                }

                Bin b = new Bin();
                b.setBin(rs.getString("bin"));
                b.setScheme(rs.getString("scheme"));
                b.setIssuerId(rs.getString("issuer_id"));
                return b;
            }
        } catch (Exception e) {
            throw new RuntimeException("Failed to query BIN", e);
        }
    }
}
