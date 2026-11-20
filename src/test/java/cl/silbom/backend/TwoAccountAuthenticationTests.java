package cl.silbom.backend;

import cl.silbom.backend.config.DataInitializer;
import cl.silbom.backend.dto.*;
import cl.silbom.backend.model.*;
import cl.silbom.backend.repository.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.RequestPostProcessor;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.context.WebApplicationContext;
import static org.junit.jupiter.api.Assertions.*;
import static org.hamcrest.Matchers.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/** Credenciales aleatorias efímeras: nunca utiliza las contraseñas de la demostración real. */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
class TwoAccountAuthenticationTests {
    static String randomSecret() {
        byte[] bytes = new byte[24]; new SecureRandom().nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }
    static final String SUP_SECRET = randomSecret();
    static final String TEC_SECRET = randomSecret();
    static final AtomicInteger ADDRESS = new AtomicInteger();
    static final String PLANTA = "PLANTA-SAN-JOAQUIN";
    @DynamicPropertySource static void configuration(DynamicPropertyRegistry r) {
        String postgres = System.getenv("SILBOM_DEMO_TEST_DB_URL");
        r.add("spring.datasource.url", () -> postgres == null
                ? "jdbc:h2:mem:two_accounts;DB_CLOSE_DELAY=-1;MODE=PostgreSQL" : postgres);
        if (postgres != null) {
            r.add("spring.datasource.driver-class-name", () -> "org.postgresql.Driver");
            r.add("spring.jpa.database-platform", () -> "org.hibernate.dialect.PostgreSQLDialect");
            r.add("spring.jpa.hibernate.ddl-auto", () -> "none");
            r.add("spring.datasource.username", () -> System.getenv("TEST_DB_USERNAME"));
            r.add("spring.datasource.password", () -> System.getenv("TEST_DB_PASSWORD"));
        }
        r.add("silbom.demo.two-users-only", () -> true);
        r.add("silbom.demo.supervisor.username", () -> "supervisor");
        r.add("silbom.demo.technician.username", () -> "tecnico");
        r.add("silbom.demo.supervisor.password", () -> SUP_SECRET);
        r.add("silbom.demo.technician.password", () -> TEC_SECRET);
    }
    @Autowired jakarta.persistence.EntityManager entityManager;
    @Autowired WebApplicationContext context;
    @Autowired ObjectMapper json;
    @Autowired TecnicoRepository users;
    @Autowired BloqueoLotoRepository tickets;
    @Autowired PasswordEncoder encoder;
    @Autowired DataInitializer initializer;
    MockMvc mvc;
    @BeforeEach void setup() {
        if (System.getenv("SILBOM_DEMO_TEST_DB_URL") != null) {
            entityManager.unwrap(org.hibernate.Session.class).doWork(c -> {
                try (var statement = c.prepareStatement("select set_config('app.current_planta_id', ?, true)")) {
                    statement.setString(1, PLANTA);statement.execute();
                }
            });
        }
        String ip = "198.18.0." + ADDRESS.incrementAndGet();
        mvc = MockMvcBuilders.webAppContextSetup(context).apply(springSecurity())
                .defaultRequest(get("/").header("User-Agent", "IntegrationTests/1.0")
                        .header("X-Requested-With", "XMLHttpRequest")
                        .with(req -> { req.setRemoteAddr(ip); return req; })).build();
    }
    RequestPostProcessor sup() { return httpBasic("supervisor", SUP_SECRET); }
    RequestPostProcessor tec() { return httpBasic("tecnico", TEC_SECRET); }
    Tecnico account(String username) { return users.findByUsernameAndPlantaId(username, PLANTA).orElseThrow(); }
    String body(Object value) throws Exception { return json.writeValueAsString(value); }
    BloqueoCreateDTO payload() {
        return new BloqueoCreateDTO("EQ-PR-04", TipoIntervencion.PREVENTIVA,
                "Inspección de prueba aislada", null, true, "Nota de prueba", null, null);
    }
    long create(RequestPostProcessor auth) throws Exception {
        var response = mvc.perform(post("/api/v1/bloqueos").with(auth)
                .contentType(MediaType.APPLICATION_JSON).content(body(payload())))
                .andExpect(status().isCreated()).andReturn().getResponse();
        return json.readTree(response.getContentAsString()).get("id").asLong();
    }
    BloqueoLoto activeTicket(Long owner) {
        var t = new BloqueoLoto("EQ-PR-04", TipoIntervencion.PREVENTIVA,
                "Bloqueo de prueba aislada", "Identidad histórica", true, PLANTA);
        if (owner != null) t.asignarResponsable(owner, null);
        return tickets.saveAndFlush(t);
    }
    @Test void supervisorYTecnicoAutenticanConRolesDelServidorSinSecretos() throws Exception {
        for (var entry : List.of(new Object[]{"supervisor", SUP_SECRET, "SUPERVISOR"},
                new Object[]{"tecnico", TEC_SECRET, "TECNICO"})) {
            var response = mvc.perform(get("/api/v1/sesion")
                    .with(httpBasic((String)entry[0], (String)entry[1])))
                    .andExpect(status().isOk()).andExpect(header().string("Cache-Control", containsString("no-store")))
                    .andExpect(jsonPath("$.username", is(entry[0])))
                    .andExpect(jsonPath("$.rol", is(entry[2])))
                    .andExpect(jsonPath("$.nombre", is(entry[0].equals("supervisor")
                            ? "Supervisor SILBOM" : "Técnico SILBOM")))
                    .andExpect(jsonPath("$.modoDosCuentas", is(true)))
                    .andExpect(jsonPath("$.identidadesSoloLectura", is(true)))
                    .andReturn().getResponse().getContentAsString();
            var tree = json.readTree(response);
            assertEquals(6, tree.size());
            assertFalse(response.contains(SUP_SECRET));assertFalse(response.contains(TEC_SECRET));
            assertFalse(response.contains("$2"));assertFalse(tree.has("password"));assertFalse(tree.has("passwordHash"));
        }
    }
    @Test void clavesIncorrectasInexistenteYSinSesionSon401() throws Exception {
        for (String name : List.of("supervisor", "tecnico", "no-existe")) {
            mvc.perform(get("/api/v1/sesion").with(httpBasic(name, randomSecret())))
                    .andExpect(status().isUnauthorized());
        }
        mvc.perform(get("/api/v1/sesion")).andExpect(status().isUnauthorized());
        mvc.perform(post("/api/v1/maquinas").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isUnauthorized());
    }
    @Test void terceraCuentaValidaEsRechazadaSinEliminarla() throws Exception {
        String secret = randomSecret();
        var third = users.saveAndFlush(new Tecnico("tercero", "Histórico", encoder.encode(secret), Rol.SUPERVISOR, PLANTA));
        mvc.perform(get("/api/v1/sesion").with(httpBasic("tercero", secret))).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/v1/tecnicos").with(sup())).andExpect(status().isOk());
        assertTrue(users.findById(third.getId()).orElseThrow().isActivo());
    }
    @Test void identidadPermitidaDesactivadaNoAutentica() throws Exception {
        account("tecnico").desactivar();users.flush();
        mvc.perform(get("/api/v1/sesion").with(tec())).andExpect(status().isUnauthorized());
    }
    @Test void rolInesperadoNoObtieneAccesoAunqueUsernameCoincida() throws Exception {
        account("tecnico").actualizar("Rol alterado", Rol.SUPERVISOR, null);users.flush();
        mvc.perform(get("/api/v1/sesion").with(tec())).andExpect(status().isUnauthorized());
    }
    @Test void tecnicoNoAdministraMaquinasNiIdentidades() throws Exception {
        mvc.perform(post("/api/v1/maquinas").with(tec()).contentType(MediaType.APPLICATION_JSON)
                .content(body(new MaquinaCreateDTO("EQ-AUT-01", "Equipo prueba", "Pruebas", "X", 0.0, 0, null))))
                .andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/tecnicos").with(tec())).andExpect(status().isForbidden());
        mvc.perform(post("/api/v1/tecnicos").with(tec()).contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isForbidden());
    }
    @Test void supervisorConservaAdministracionDeMaquinasYConsultas() throws Exception {
        mvc.perform(post("/api/v1/maquinas").with(sup()).contentType(MediaType.APPLICATION_JSON)
                .content(body(new MaquinaCreateDTO("EQ-AUT-01", "Equipo prueba", "Pruebas", "X", 0.0, 0, null))))
                .andExpect(status().isCreated());
        mvc.perform(get("/api/v1/tecnicos").with(sup())).andExpect(status().isOk())
                .andExpect(jsonPath("$[*].passwordHash").doesNotExist());
        mvc.perform(get("/api/v1/bloqueos").with(sup())).andExpect(status().isOk());
    }
    @Test void altasCambiosYBajasDeIdentidadesProhibidosInclusoSupervisor() throws Exception {
        long count = users.count(); var t = account("tecnico");
        mvc.perform(post("/api/v1/tecnicos").with(sup()).contentType(MediaType.APPLICATION_JSON)
                .content(body(new TecnicoCreateDTO("nuevo", "No crear", randomSecret(), Rol.TECNICO))))
                .andExpect(status().isForbidden());
        mvc.perform(put("/api/v1/tecnicos/" + t.getId()).with(sup()).contentType(MediaType.APPLICATION_JSON)
                .content(body(new TecnicoUpdateDTO("No cambiar", Rol.SUPERVISOR, randomSecret()))))
                .andExpect(status().isForbidden());
        mvc.perform(delete("/api/v1/tecnicos/" + t.getId()).with(sup())).andExpect(status().isForbidden());
        assertEquals(count, users.count());assertTrue(t.isActivo());assertEquals(Rol.TECNICO,t.getRol());
        assertTrue(encoder.matches(TEC_SECRET, t.getPasswordHash()));
    }
    @Test void multilotoYCierreExclusivoConservanHistorial() throws Exception {
        long before = tickets.count();long a = create(sup());long b = create(tec());
        mvc.perform(put("/api/v1/bloqueos/" + a + "/liberar").with(tec())).andExpect(status().isForbidden());
        mvc.perform(put("/api/v1/bloqueos/" + b + "/liberar").with(sup())).andExpect(status().isForbidden());
        mvc.perform(put("/api/v1/bloqueos/" + b + "/liberar").with(tec())).andExpect(status().isOk());
        mvc.perform(get("/api/v1/maquinas/EQ-PR-04").with(tec()))
                .andExpect(status().isOk()).andExpect(jsonPath("$.bloqueosActivos", is(1)))
                .andExpect(jsonPath("$.bloqueada", is(true)));
        mvc.perform(get("/api/v1/bloqueos/" + b).with(tec()))
                .andExpect(status().isOk()).andExpect(jsonPath("$.estado", is("CERRADO")));
        assertEquals(before + 2, tickets.count());
    }
    @Test void excluidoConTicketActivoImpideActivacion() {
        var third = users.saveAndFlush(new Tecnico("historico", "Histórico", encoder.encode(randomSecret()), Rol.TECNICO, PLANTA));
        var t = activeTicket(third.getId());
        assertThrows(IllegalStateException.class, () -> initializer.run());
        assertEquals(EstadoBloqueo.ACTIVO, tickets.findById(t.getId()).orElseThrow().getEstado());
    }
    @Test void excluidoInactivoConTicketActivoTambienImpideActivacion() {
        var third = new Tecnico("inactivo", "Histórico", encoder.encode(randomSecret()), Rol.TECNICO, PLANTA);
        third.desactivar();third = users.saveAndFlush(third);activeTicket(third.getId());
        assertThrows(IllegalStateException.class, () -> initializer.run());
    }
    @Test void ticketLegadoActivoImpideActivacionSinAsignarResponsableFalso() {
        var t = activeTicket(null);
        assertThrows(IllegalStateException.class, () -> initializer.run());
        assertNull(t.getTecnicoId());assertEquals(EstadoBloqueo.ACTIVO,t.getEstado());
    }
    @Test void reiniciarConservaIdsHashesYHistorial() {
        var a = account("supervisor");var b = account("tecnico");
        String hashA = a.getPasswordHash(), hashB = b.getPasswordHash();
        a.actualizar("Nombre anterior", a.getRol(), null);
        long before = tickets.count();initializer.run();users.flush();
        assertEquals("Supervisor SILBOM", account("supervisor").getNombre());
        assertTrue(hashA.equals(account("supervisor").getPasswordHash()));
        assertTrue(hashB.equals(account("tecnico").getPasswordHash()));
        assertEquals(before,tickets.count());assertEquals(2,users.count());
        assertTrue(hashA.startsWith("$2"));assertTrue(encoder.matches(SUP_SECRET,hashA));
    }
    @Test void noReactivaCuentaNiCambiaRolExistenteAlConfigurar() {
        var t=account("tecnico");t.desactivar();users.flush();
        assertThrows(IllegalStateException.class, () -> initializer.run());
        assertFalse(t.isActivo());
    }
}
