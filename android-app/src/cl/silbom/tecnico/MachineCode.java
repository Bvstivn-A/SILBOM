package cl.silbom.tecnico;

import java.util.regex.Pattern;

/**
 * Regla única de identificadores de máquina SILBOM, compartida por NFC y QR.
 *
 * Un código solo identifica una máquina: nunca es una URL, un comando ni una
 * credencial. El backend confirma después que la máquina existe.
 */
public final class MachineCode {
    /** Mismo formato que la web (nfc-code.js) y el backend. */
    public static final Pattern PATTERN = Pattern.compile("^EQ-[A-Z]{2,4}-[0-9]{2}$");

    public static final String ERROR_EMPTY = "empty_code";
    public static final String ERROR_URL = "url_not_allowed";
    public static final String ERROR_INVALID = "invalid_code";

    private static final Pattern URL_LIKE = Pattern.compile(
            "^(?:[A-Za-z][A-Za-z0-9+.-]*:|www\\.|\\d{1,3}(?:\\.\\d{1,3}){3}).*|.*://.*",
            Pattern.DOTALL);

    private MachineCode() {}

    public static boolean isValid(String code) {
        return code != null && PATTERN.matcher(code).matches();
    }

    /** Quita solo espacios externos y la marca BOM; no corrige mayúsculas ni caracteres internos. */
    public static String normalize(String raw) {
        if (raw == null) return "";
        String value = raw;
        while (value.startsWith("\uFEFF")) value = value.substring(1);
        return value.trim();
    }

    /** @return null si el texto es un identificador válido; si no, el motivo del rechazo. */
    public static String rejectionReason(String raw) {
        String code = normalize(raw);
        if (code.isEmpty()) return ERROR_EMPTY;
        if (isValid(code)) return null;
        if (URL_LIKE.matcher(code).matches()) return ERROR_URL;
        return ERROR_INVALID;
    }
}
