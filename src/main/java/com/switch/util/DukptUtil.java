package com.qswitch.util;

import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;
import java.util.Locale;

public final class DukptUtil {
    private static final byte[] KEY_MASK = hexToBytes("C0C0C0C000000000C0C0C0C000000000");
    private static final byte[] KSN_MASK = hexToBytes("FFFFFFFFFFFFFFE00000");

    private DukptUtil() {
    }

    // Real ANSI X9.24 DUKPT derivation (double-length BDK and 10-byte KSN).
    public static String deriveWorkingKey(String baseDerivationKey, String ksn) {
        byte[] bdk = parseHex(baseDerivationKey, "BDK");
        byte[] ksnBytes = parseHex(ksn, "KSN");

        if (bdk.length != 16) {
            throw new IllegalArgumentException("BDK must be 16 bytes (32 hex chars)");
        }
        if (ksnBytes.length != 10) {
            throw new IllegalArgumentException("KSN must be 10 bytes (20 hex chars)");
        }

        byte[] ipek = deriveIpek(bdk, ksnBytes);
        byte[] sessionKey = deriveSessionKey(ipek, ksnBytes);
        return bytesToHex(sessionKey);
    }

    private static byte[] deriveIpek(byte[] bdk, byte[] ksn) {
        byte[] ksnReg = ksn.clone();
        applyMaskInPlace(ksnReg, KSN_MASK);
        byte[] ksn8 = new byte[8];
        System.arraycopy(ksnReg, 0, ksn8, 0, 8);

        byte[] left = tdesEncrypt(bdk, ksn8);
        byte[] bdkMasked = xor(bdk, KEY_MASK);
        byte[] right = tdesEncrypt(bdkMasked, ksn8);
        return concat(left, right);
    }

    private static byte[] deriveSessionKey(byte[] ipek, byte[] ksn) {
        byte[] key = ipek.clone();
        byte[] ksnReg = ksn.clone();
        applyMaskInPlace(ksnReg, KSN_MASK);

        int counter = ((ksn[7] & 0x1F) << 16) | ((ksn[8] & 0xFF) << 8) | (ksn[9] & 0xFF);
        for (int shift = 0x100000; shift > 0; shift >>= 1) {
            if ((counter & shift) != 0) {
                ksnReg[7] = (byte) ((ksnReg[7] & 0xE0) | ((shift >> 16) & 0x1F));
                ksnReg[8] = (byte) ((shift >> 8) & 0xFF);
                ksnReg[9] = (byte) (shift & 0xFF);
                key = nonReversibleKeyGen(key, ksnReg);
            }
        }
        return key;
    }

    private static byte[] nonReversibleKeyGen(byte[] key, byte[] ksnReg) {
        byte[] data = new byte[8];
        System.arraycopy(ksnReg, 2, data, 0, 8);

        byte[] right = processHalf(key, data);
        byte[] keyMasked = xor(key, KEY_MASK);
        byte[] left = processHalf(keyMasked, data);
        return concat(left, right);
    }

    private static byte[] processHalf(byte[] key, byte[] data) {
        byte[] keyLeft = new byte[8];
        byte[] keyRight = new byte[8];
        System.arraycopy(key, 0, keyLeft, 0, 8);
        System.arraycopy(key, 8, keyRight, 0, 8);

        byte[] xored = xor(data, keyRight);
        byte[] encrypted = desEncrypt(keyLeft, xored);
        return xor(encrypted, keyRight);
    }

    private static byte[] desEncrypt(byte[] key8, byte[] data8) {
        try {
            Cipher cipher = Cipher.getInstance("DES/ECB/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key8, "DES"));
            return cipher.doFinal(data8);
        } catch (Exception e) {
            throw new IllegalStateException("Unable to perform DES encryption for DUKPT", e);
        }
    }

    private static byte[] tdesEncrypt(byte[] key16, byte[] data8) {
        try {
            byte[] key24 = new byte[24];
            System.arraycopy(key16, 0, key24, 0, 16);
            System.arraycopy(key16, 0, key24, 16, 8);
            Cipher cipher = Cipher.getInstance("DESede/ECB/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key24, "DESede"));
            return cipher.doFinal(data8);
        } catch (Exception e) {
            throw new IllegalStateException("Unable to perform 3DES encryption for DUKPT", e);
        }
    }

    private static byte[] parseHex(String value, String label) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(label + " must not be blank");
        }
        String normalized = value.trim().toUpperCase(Locale.ROOT);
        if ((normalized.length() % 2) != 0 || !normalized.matches("[0-9A-F]+")) {
            throw new IllegalArgumentException(label + " must be a valid even-length hex string");
        }
        return hexToBytes(normalized);
    }

    private static void applyMaskInPlace(byte[] target, byte[] mask) {
        for (int i = 0; i < target.length && i < mask.length; i++) {
            target[i] &= mask[i];
        }
    }

    private static byte[] concat(byte[] a, byte[] b) {
        byte[] out = new byte[a.length + b.length];
        System.arraycopy(a, 0, out, 0, a.length);
        System.arraycopy(b, 0, out, a.length, b.length);
        return out;
    }

    private static byte[] xor(byte[] a, byte[] b) {
        byte[] out = new byte[Math.min(a.length, b.length)];
        for (int i = 0; i < out.length; i++) {
            out[i] = (byte) (a[i] ^ b[i]);
        }
        return out;
    }

    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    private static byte[] hexToBytes(String hex) {
        int len = hex.length();
        byte[] data = new byte[len / 2];
        for (int i = 0; i < len; i += 2) {
            data[i / 2] = (byte) ((Character.digit(hex.charAt(i), 16) << 4)
                + Character.digit(hex.charAt(i + 1), 16));
        }
        return data;
    }
}
