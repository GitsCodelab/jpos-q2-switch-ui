package com.qswitch.util;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;

public final class MacUtil {
    private MacUtil() {
    }

    public static String hmacSha256Hex(String data, String key) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(key.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            byte[] result = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
            return toHex(result);
        } catch (Exception e) {
            throw new IllegalStateException("Unable to compute HMAC", e);
        }
    }

    private static String toHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
}
