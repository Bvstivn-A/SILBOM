package cl.silbom.backend.security;

import cl.silbom.backend.exception.SecurityAuthException;
import cl.silbom.backend.model.Rol;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import static org.junit.jupiter.api.Assertions.*;

class ActorActualTests {
    @AfterEach void cleanup() { SecurityContextHolder.clearContext(); }
    @Test void servicioNoAceptaPrincipalExcluidoInactivoORolAjeno() {
        String temporary = java.util.UUID.randomUUID().toString();
        var actor = new ActorActual(new TwoAccountAccess(true,"supervisor",temporary,"tecnico",temporary));
        for (var t : java.util.List.of(
                new TecnicoPrincipal(3L,"tercero",null,Rol.SUPERVISOR,"PLANTA",true),
                new TecnicoPrincipal(2L,"tecnico",null,Rol.TECNICO,"PLANTA",false),
                new TecnicoPrincipal(2L,"tecnico",null,Rol.SUPERVISOR,"PLANTA",true))) {
            SecurityContextHolder.getContext().setAuthentication(
                    new UsernamePasswordAuthenticationToken(t,null,t.getAuthorities()));
            assertThrows(SecurityAuthException.class,actor::obtener);
        }
    }
    @Test void modoNormalConservaIdentidadesHistoricasActivas() {
        var actor=new ActorActual(new TwoAccountAccess(false,"supervisor","","tecnico",""));
        var t=new TecnicoPrincipal(3L,"historico",null,Rol.TECNICO,"PLANTA",true);
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(t,null,t.getAuthorities()));
        assertEquals(t,actor.obtener());
    }
}
