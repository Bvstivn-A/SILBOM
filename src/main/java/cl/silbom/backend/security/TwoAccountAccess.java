package cl.silbom.backend.security;

import java.nio.charset.StandardCharsets;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Restricción opcional de acceso para demostraciones académicas.
 *
 * <p>Con el modo activo, solo estos dos usernames pueden autenticarse y las
 * credenciales iniciales se toman del entorno local, nunca del repositorio.
 * El modo desactivado conserva la gestión normal de usuarios del sistema.
 */
@Component
public final class TwoAccountAccess {

    private final boolean enabled;
    private final String supervisorUsername;
    private final String supervisorPassword;
    private final String technicianUsername;
    private final String technicianPassword;

    public TwoAccountAccess(
            @Value("${silbom.demo.two-users-only:false}") boolean enabled,
            @Value("${silbom.demo.supervisor.username:supervisor}") String supervisorUsername,
            @Value("${silbom.demo.supervisor.password:}") String supervisorPassword,
            @Value("${silbom.demo.technician.username:tecnico}") String technicianUsername,
            @Value("${silbom.demo.technician.password:}") String technicianPassword) {
        this.enabled = enabled;
        this.supervisorUsername = supervisorUsername;
        this.supervisorPassword = supervisorPassword;
        this.technicianUsername = technicianUsername;
        this.technicianPassword = technicianPassword;
        if (enabled) {
            validateUsername(supervisorUsername);
            validateUsername(technicianUsername);
            if (supervisorUsername.equals(technicianUsername)) {
                throw new IllegalArgumentException("Los dos usuarios de demostración deben ser distintos");
            }
            validatePassword(supervisorPassword);
            validatePassword(technicianPassword);
        }
    }

    private static void validateUsername(String username) {
        if (username == null || !username.matches("[A-Za-z0-9._-]{3,50}")) {
            throw new IllegalArgumentException("Username de demostración no válido");
        }
    }

    private static void validatePassword(String password) {
        if (password == null || password.length() < 12
                || password.getBytes(StandardCharsets.UTF_8).length > 72
                || password.startsWith("CAMBIAR_")) {
            throw new IllegalArgumentException(
                    "La contraseña de demostración debe tener al menos 12 caracteres"
                        + " y no superar 72 bytes UTF-8");
        }
    }

    public boolean enabled() {
        return enabled;
    }

    public boolean allows(String username) {
        return !enabled || (username != null
                && (username.equals(supervisorUsername) || username.equals(technicianUsername)));
    }

    public String supervisorUsername() {
        return supervisorUsername;
    }

    public String supervisorPassword() {
        return supervisorPassword;
    }

    public String technicianUsername() {
        return technicianUsername;
    }

    public String technicianPassword() {
        return technicianPassword;
    }

    @Override
    public String toString() {
        return "TwoAccountAccess[enabled=" + enabled + ", credentials=redacted]";
    }
}
