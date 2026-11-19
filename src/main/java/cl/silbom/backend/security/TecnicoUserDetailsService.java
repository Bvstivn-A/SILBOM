package cl.silbom.backend.security;

import cl.silbom.backend.repository.TecnicoRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * QUÉ HACE: Busca la identidad por username y planta configurada y la adapta a UserDetails.
 *
 * <p>POR QUÉ ESTÁ ESCRITO ASÍ: La consulta transaccional recibe contexto RLS y limita la búsqueda a
 * la planta del servidor. Spring Security valida el hash y rechaza cuentas inactivas al autenticar
 * con HTTP Basic.
 */
@Service
public class TecnicoUserDetailsService implements UserDetailsService {

    private final TecnicoRepository repository;

    private final String planta;

    private final TwoAccountAccess twoAccounts;

    public TecnicoUserDetailsService(
            TecnicoRepository repository, @Value("${silbom.security.planta-id}") String planta,
            TwoAccountAccess twoAccounts) {
        this.repository = repository;
        this.planta = planta;
        this.twoAccounts = twoAccounts;
    }

    /**
     * QUÉ HACE: Carga el principal del usuario solicitado o lanza UsernameNotFoundException.
     *
     * <p>POR QUÉ ESTÁ ESCRITO ASÍ: Mantiene un mensaje genérico ante credenciales inválidas y no
     * devuelve entidades con hashes por los controladores.
     */
    @Override
    @Transactional(readOnly = true)
    public UserDetails loadUserByUsername(String username) {
        if (!twoAccounts.allows(username)) {
            throw new UsernameNotFoundException("Credencial inválida");
        }
        return repository
                .findByUsernameAndPlantaId(username, planta)
                .map(TecnicoPrincipal::new)
                .orElseThrow(() -> new UsernameNotFoundException("Credencial inválida"));
    }
}
