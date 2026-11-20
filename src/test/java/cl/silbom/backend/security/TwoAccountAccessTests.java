package cl.silbom.backend.security;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class TwoAccountAccessTests {

    @Test
    void soloDosCuentasCuandoSeHabilita() {
        var policy = new TwoAccountAccess(
                true, "supervisor", "password-supervisor-123",
                "tecnico", "password-tecnico-123");
        assertTrue(policy.enabled());
        assertTrue(policy.allows("supervisor"));
        assertTrue(policy.allows("tecnico"));
        assertFalse(policy.allows("supervisor-test"));
        assertFalse(policy.allows("otro-tecnico"));
        assertFalse(policy.allows(null));
        assertFalse(policy.toString().contains("password-supervisor-123"));
    }

    @Test
    void conservaAutenticacionNormalSiModoApagado() {
        var policy = new TwoAccountAccess(false, "supervisor", "", "tecnico", "");
        assertTrue(policy.allows("cuenta-existente"));
    }

    @Test
    void noAceptaClavesCortasNiCuentasDuplicadas() {
        assertThrows(IllegalArgumentException.class,
                () -> new TwoAccountAccess(true, "supervisor", "corta", "tecnico", "123456789012"));
        assertThrows(IllegalArgumentException.class,
                () -> new TwoAccountAccess(true, "igual", "123456789012", "igual", "123456789012"));
        assertThrows(IllegalArgumentException.class,
                () -> new TwoAccountAccess(true, "supervisor", "123456789012", "tecnico", "á".repeat(40)));
    }
}
