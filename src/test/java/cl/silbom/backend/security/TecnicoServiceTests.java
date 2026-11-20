package cl.silbom.backend.security;
import cl.silbom.backend.dto.TecnicoCreateDTO;
import cl.silbom.backend.exception.ForbiddenOperationException;
import cl.silbom.backend.model.Rol;
import cl.silbom.backend.repository.*;
import cl.silbom.backend.service.TecnicoService;
import org.junit.jupiter.api.Test;
import org.springframework.security.crypto.password.PasswordEncoder;
import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

class TecnicoServiceTests {
    @Test void servicioRechazaNoSupervisorAntesDePersistir() {
        var repo=mock(TecnicoRepository.class);var bloqueos=mock(BloqueoLotoRepository.class);
        var encoder=mock(PasswordEncoder.class);var actor=mock(ActorActual.class);
        doThrow(new ForbiddenOperationException("No autorizado")).when(actor).exigirSupervisor();
        var service=new TecnicoService(repo,bloqueos,encoder,actor,"PLANTA",mock(TwoAccountAccess.class));
        assertThrows(ForbiddenOperationException.class,()->service.crear(new TecnicoCreateDTO("prueba","Nombre","test-only-password",Rol.TECNICO)));
        verifyNoInteractions(repo,bloqueos,encoder);
    }
    @org.junit.jupiter.params.ParameterizedTest
    @org.junit.jupiter.params.provider.ValueSource(strings={"crear","actualizar","eliminar"})
    void modoDemoImpideTodaMutacionTambienAlInvocarServicio(String operation) {
        var repo=mock(TecnicoRepository.class);var locks=mock(BloqueoLotoRepository.class);
        var encoder=mock(PasswordEncoder.class);var actor=mock(ActorActual.class);
        var policy=mock(TwoAccountAccess.class);when(policy.enabled()).thenReturn(true);
        var service=new TecnicoService(repo,locks,encoder,actor,"PLANTA",policy);
        String temporarySecret=java.util.UUID.randomUUID().toString();
        assertThrows(ForbiddenOperationException.class,()->{
            switch(operation) {
                case "crear" -> service.crear(new TecnicoCreateDTO("prueba","Nombre",temporarySecret,Rol.TECNICO));
                case "actualizar" -> service.actualizar(1L,new cl.silbom.backend.dto.TecnicoUpdateDTO("Nombre",Rol.SUPERVISOR,temporarySecret));
                case "eliminar" -> service.eliminar(1L);
            }
        });
        verify(actor).exigirSupervisor();verifyNoInteractions(repo,locks,encoder);
    }
}
