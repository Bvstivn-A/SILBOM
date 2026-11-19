package cl.silbom.backend.dto;

import cl.silbom.backend.model.Rol;

/** Identidad propia verificada por el servidor. Nunca serializa el principal ni su hash. */
public record SesionResponseDTO(Long id, String username, String nombre, Rol rol,
        boolean modoDosCuentas, boolean identidadesSoloLectura) {}
