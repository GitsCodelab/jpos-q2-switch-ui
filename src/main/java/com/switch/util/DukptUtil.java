package com.qswitch.util;

public final class DukptUtil {
    private DukptUtil() {
    }

    // This is a deterministic placeholder suitable for scaffolding and tests.
    public static String deriveWorkingKey(String baseDerivationKey, String ksn) {
        String material = baseDerivationKey + ":" + ksn;
        return MacUtil.hmacSha256Hex(material, baseDerivationKey).substring(0, 32);
    }
}
