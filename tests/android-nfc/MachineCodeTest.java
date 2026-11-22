package cl.silbom.tecnico;

/** Pruebas puras de la validación compartida NFC/QR (sin Android SDK). */
public final class MachineCodeTest {
    private static int checks;

    public static void main(String[] args) {
        for (String code : new String[]{"EQ-COM-03", "EQ-ENV-01", "EQ-EXT-02"}) {
            expect(code, null, MachineCode.rejectionReason(code));
            expect(code, null, MachineCode.rejectionReason("  " + code + "\r\n"));
            expect(code, null, MachineCode.rejectionReason("\uFEFF" + code));
            expect(code, code, MachineCode.normalize("\uFEFF " + code + "\n"));
            // Controles externos se eliminan: el código entregado a la WebView queda limpio.
            expect(code, code, MachineCode.normalize(code + "\u0000\t"));
            expect(code, true, MachineCode.isValid(code));
        }
        expect("vacío", MachineCode.ERROR_EMPTY, MachineCode.rejectionReason(""));
        expect("espacios", MachineCode.ERROR_EMPTY, MachineCode.rejectionReason("   \n"));
        expect("null", MachineCode.ERROR_EMPTY, MachineCode.rejectionReason(null));
        for (String url : new String[]{"https://google.com", "http://192.168.1.50:8080", "https://ejemplo.com",
                "HTTP://EQ-COM-03", "www.google.com", "192.168.1.50", "javascript:alert(1)",
                "intent://scan/#Intent;end", "file:///sdcard/a", "EQ-COM-03://x"}) {
            expect(url, MachineCode.ERROR_URL, MachineCode.rejectionReason(url));
        }
        for (String invalid : new String[]{"HOLA", "EQ-ENV", "eq-com-03", "EQ-COM-3", "EQ-COM-003",
                "EQ-C-01", "EQ-COMPR-01", "EQ-COM-03 EQ-ENV-01", "EQ-COM-03\nEQ-ENV-01", "EQ-\u0000COM-03",
                "EQ\u2011COM\u201103", "EQ-COM-03\u200B", "{\"id\":\"EQ-COM-03\"}", "EQ-COM-03/../"}) {
            expect(invalid, MachineCode.ERROR_INVALID, MachineCode.rejectionReason(invalid));
            expect(invalid, false, MachineCode.isValid(invalid));
        }
        System.out.println("MachineCodeTest: " + checks + " verificaciones OK");
    }

    private static void expect(String label, Object expected, Object actual) {
        checks++;
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + ": esperado " + expected + ", obtenido " + actual);
        }
    }
}
