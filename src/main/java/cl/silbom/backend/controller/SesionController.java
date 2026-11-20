package cl.silbom.backend.controller;

import cl.silbom.backend.dto.SesionResponseDTO;
import cl.silbom.backend.exception.SecurityAuthException;
import cl.silbom.backend.repository.TecnicoRepository;
import cl.silbom.backend.security.ActorActual;
import cl.silbom.backend.security.TwoAccountAccess;
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class SesionController {
    private final ActorActual actor;
    private final TecnicoRepository tecnicos;
    private final TwoAccountAccess twoAccounts;

    public SesionController(ActorActual actor, TecnicoRepository tecnicos, TwoAccountAccess twoAccounts) {
        this.actor = actor;
        this.tecnicos = tecnicos;
        this.twoAccounts = twoAccounts;
    }

    @GetMapping("/api/v1/sesion")
    @Transactional(readOnly = true)
    public ResponseEntity<SesionResponseDTO> actual() {
        var principal = actor.obtener();
        var t = tecnicos.findByIdAndPlantaIdAndActivoTrue(principal.id(), principal.plantaId())
                .orElseThrow(() -> new SecurityAuthException("Credencial inválida"));
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(new SesionResponseDTO(
                t.getId(), t.getUsername(), t.getNombre(), t.getRol(),
                twoAccounts.enabled(), twoAccounts.enabled()));
    }
}
