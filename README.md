# SILBOM — Sistema Inteligente de Lectura y Bloqueo Operativo de Maquinarias

> **Una capa de auditoría digital sobre el candado que la ley ya exige.**
> Identifica cada máquina con NFC, registra cada candado LOTO y lo muestra en vivo al supervisor.

- **Video del producto:** [Ver en YouTube](https://youtu.be/L9Cww6cgNoY)
- **Manual de instalación y uso:** [docs/MANUAL_INSTALACION_Y_USO.md](docs/MANUAL_INSTALACION_Y_USO.md)
- **App Android (APK):** [Releases del repositorio](https://github.com/Bvstivn-A/Silbom/releases)
- **Historial del Hito 1:** [github.com/Vicente-PR/SILBOM](https://github.com/Vicente-PR/SILBOM) (ver [Historial del proyecto](#historial-del-proyecto))

Proyecto semestral INGT1003 · Universidad Mayor · 2026

---

## Integrantes

| Integrante | Usuario GitHub |
|---|---|
| Bastián | [@Bvstivn-A](https://github.com/Bvstivn-A) |
| Belén | [@lenbbee](https://github.com/lenbbee) |
| Benjamín | [@BenjaHK](https://github.com/BenjaHK) |
| Vicente | [@Vicente-PR](https://github.com/Vicente-PR) |

---

## ¿Qué es SILBOM?

En una planta industrial, cada mantención exige bloquear la energía de la máquina con un candado (procedimiento **LOTO**, *Lockout/Tagout*). Hoy ese registro suele quedar en papel y nadie sabe, en tiempo real, quién está interviniendo qué máquina.

SILBOM tiene tres partes:

| Parte | Quién la usa | Dónde |
|---|---|---|
| **App del técnico** (Android con NFC, o navegador del celular) | Técnico en terreno | APK o `http://IP-DEL-PC:8080/app/` |
| **Consola del supervisor** | Supervisor en su PC | `http://localhost:8080/` |
| **Servidor** (Java + Spring Boot + PostgreSQL) | Corre en un PC | Puerto `8080` |

1. **Identifica:** el técnico acerca el teléfono a la etiqueta NFC de la máquina.
2. **Registra:** declara su bloqueo (tipo de intervención y candado físico) y queda un ticket con cronómetro.
3. **Supervisa:** la consola marca la máquina en rojo en vivo. Solo el técnico dueño del candado puede liberarlo, y todo queda guardado como historial que no se borra.

> ⚠️ El estado «bloqueada» es un **registro digital**. SILBOM no instala candados, no corta energía ni certifica energía cero; la confirmación del candado es una declaración del técnico autenticado (DS 594).

---

## Instalación y uso

📘 **Manual completo:** [docs/MANUAL_INSTALACION_Y_USO.md](docs/MANUAL_INSTALACION_Y_USO.md). Incluye requisitos, pasos para Windows, macOS y Linux, datos de prueba, uso, app Android y fallas frecuentes.

**Requisitos:** Git, JDK 21, Maven 3.6.3+ y PostgreSQL 15–17.

**Resumen de la instalación:**

1. **Instala** los programas y descarga el proyecto:

   ```bash
   git clone https://github.com/Bvstivn-A/Silbom.git
   cd Silbom
   ```

2. **Crea la base de datos.** En la consola de PostgreSQL como administrador, crea los roles `silbom_owner` y `silbom_app` y la base `silbom_db`. Después crea las tablas:

   ```bash
   psql -h localhost -U silbom_owner -d silbom_db -v ON_ERROR_STOP=1 -f db/schema.sql
   ```

3. **Configura `.env`:** copia `.env.example` a `.env` y completa:
   - `DB_PASSWORD`;
   - `ENCRYPTION_SECRET` (clave Base64 de 32 bytes);
   - `SILBOM_DEMO_TWO_USERS_ONLY=true`;
   - las dos contraseñas de la demo (12+ caracteres).

4. **Compila y arranca:**

   ```bash
   mvn clean package
   java -jar target/silbom-backend-1.0.0.jar
   ```

5. **Pruébalo:**
   - Consola del supervisor: <http://localhost:8080/>, con el usuario `supervisor`.
   - App del técnico: <http://localhost:8080/app/?maquina=EQ-EXT-02>, con el usuario `tecnico`.

**App Android:** descarga el APK en [Releases](https://github.com/Bvstivn-A/Silbom/releases) y conéctalo a `http://IP-DEL-PC:8080`.

**Datos de prueba:**
- Cuentas `supervisor` y `tecnico`.
- 6 máquinas ficticias que se cargan solas.
- Etiquetas NFC con el texto `EQ-EXT-02`, `EQ-COM-03` o `EQ-ENV-01`.

¿Algo falla? Revisa las [fallas frecuentes](docs/MANUAL_INSTALACION_Y_USO.md#6-fallas-frecuentes).

---

## Documentación y entregas

| Documento | Enlace |
|---|---|
| Propuesta Hito 1 | [PDF](docs/SILBOM_Propuesta_Hito1%20%285%29.pdf) |
| Presentación Hito 1 | [PDF](docs/SILBOM_Presentacion_Hito1%20%281%29.pdf) |
| Informe Hito 2 | [PDF](docs/SILBOM_Informe_Hito2.pdf) |
| Informe Hito 3 | [PDF](docs/SILBOM_Informe_Hito3.pdf) |
| Manual de instalación y uso | [docs/MANUAL_INSTALACION_Y_USO.md](docs/MANUAL_INSTALACION_Y_USO.md) |
| Carta Gantt | [PDF](docs/Carta_Gantt_SILBOM.pdf) |
| Video Hito 3 | [YouTube](https://youtu.be/L9Cww6cgNoY) |
| Diagrama de arquitectura | [PNG](docs/diagrama-arquitectura.png) |
| Mapa de producto | [PNG](docs/mapa-producto.png) |
| Modelo de datos y script SQL | [db/modelo_datos.md](db/modelo_datos.md) · [db/schema.sql](db/schema.sql) |
| Controles de seguridad | [docs/controles-seguridad.md](docs/controles-seguridad.md) |
| Auditoría del backend | [docs/auditoria-backend.md](docs/auditoria-backend.md) |
| Colección Postman | [docs/SILBOM_Postman_Collection.json](docs/SILBOM_Postman_Collection.json) |

---

## Datos personales (Ley 21.719)

| Pregunta | Respuesta |
|---|---|
| ¿Qué datos personales trata? | De cada usuario: nombre, nombre de usuario, rol y planta. De cada bloqueo: quién lo hizo, cuándo empezó y terminó, y una nota opcional. |
| ¿Para qué? | Saber quién está interviniendo cada máquina y dejar trazabilidad de seguridad del procedimiento LOTO. |
| ¿Por qué solo esos? | Minimización: no se piden RUT, correo, teléfono, ubicación ni fotos. El nombre y la hora bastan para saber quién tiene un candado puesto. |
| Medidas técnicas | Inicio de sesión individual, permisos por rol, contraseñas con BCrypt (nunca en texto plano), notas cifradas con AES-256-GCM, aislamiento por planta (RLS) y registro de eventos de cada ticket (`eventos_loto`). |
| ¿Y si alguien pide eliminar sus datos? | La cuenta se da de **baja** (no puede volver a entrar). Sus tickets se conservan porque son evidencia de seguridad: borrarlos dejaría sin registro quién bloqueó una máquina. El procedimiento formal para anonimizar o eliminar datos a petición del titular está **pendiente**. |
| Datos de prueba | Solo datos ficticios (cuentas `supervisor` y `tecnico`, máquinas de demostración). Nunca se cargan datos reales al repositorio. |

---

## Uso de inteligencia artificial

El equipo usó asistentes de IA como apoyo, por ejemplo en revisión de código, documentación y material del video. Qué herramienta, en qué parte y cómo se verificó se declara en el anexo de IA del informe del Hito 3. Ver también [docs/REGISTRO_AUDITORIA_GEMINI.md](docs/REGISTRO_AUDITORIA_GEMINI.md).

---

## Historial del proyecto

Este repositorio es la **continuación** del proyecto. El trabajo de los Hitos 1 y 2 empezó en
**[github.com/Vicente-PR/SILBOM](https://github.com/Vicente-PR/SILBOM)**, donde quedan sus commits originales.
En noviembre de 2026 el equipo se cambió a este repositorio (`Bvstivn-A/Silbom`), que es el oficial desde entonces.
El repositorio anterior se mantiene solo como registro histórico.

---

## Para desarrolladores

<details>
<summary><b>Arquitectura</b></summary>

Monolito por capas en `cl.silbom.backend`:

- `controller`: recibe HTTP y valida DTO.
- `service`: autorización, reglas de negocio y transacciones.
- `repository`: consultas parametrizadas y bloqueos de fila.
- `model`: entidades y transiciones de estado.
- `dto`: evita exponer entidades o hashes.
- `exception`: normaliza errores.
- `security`: autentica, autoriza y cifra (AES-256-GCM).
- `config`: contexto RLS por planta y datos iniciales.

Tablas: `maquinas`, `tecnicos`, `fallas`, `bloqueos_loto`, `eventos_loto`, aisladas por planta con Row Level Security.
Stack: Java 21, Spring Boot 3.5.16, Maven, JPA, Spring Security, PostgreSQL 15–17.
</details>

<details>
<summary><b>Variables de entorno (.env)</b></summary>

| Variable | Propósito |
|---|---|
| `DB_URL` | JDBC PostgreSQL (por defecto `localhost:5432/silbom_db`) |
| `DB_USERNAME` / `DB_PASSWORD` | Rol de aplicación (`silbom_app`), nunca el dueño |
| `ENCRYPTION_SECRET` | Base64 de 32 bytes para AES-256-GCM |
| `PLANTA_ID` | Planta definida por el servidor |
| `SERVER_PORT` | Puerto (por defecto 8080) |
| `SILBOM_CORS_ORIGINS` | Solo si el frontend se sirve desde otro origen |
| `SILBOM_DEMO_TWO_USERS_ONLY` | `true` = solo existen las cuentas `supervisor` y `tecnico` |
| `SILBOM_DEMO_SUPERVISOR_PASSWORD` / `SILBOM_DEMO_TECHNICIAN_PASSWORD` | Contraseñas de la demo (12+ caracteres) |
| `SILBOM_BOOTSTRAP_USERNAME` / `SILBOM_BOOTSTRAP_PASSWORD` | Modo normal: crea el primer supervisor si no hay usuarios; retirar después |

`.env` se lee en formato **Java properties** desde la carpeta donde se ejecuta el servidor (sin `source`, sin comillas). Las variables exportadas en el sistema tienen prioridad.
</details>

<details>
<summary><b>API REST</b> (<code>/api/v1</code>, HTTP Basic)</summary>

| Recurso | Rutas | Permiso |
|---|---|---|
| Máquinas | `GET /maquinas`, `GET /maquinas/{id}` | Público |
| | `POST`, `PUT`, `DELETE /maquinas/{id}` | Supervisor (DELETE = baja lógica) |
| Técnicos | `GET/POST /tecnicos`, `GET/PUT/DELETE /tecnicos/{id}` | Supervisor (altas y cambios bloqueados en modo demo) |
| Tickets | `GET/POST /bloqueos`, `GET /bloqueos/{id}` | Técnico o supervisor |
| Liberación | `PUT /bloqueos/{id}/liberar` | **Solo el dueño del ticket** |
| Eventos | `GET /bloqueos/{id}/eventos` | Técnico o supervisor |
| Sesión | `GET /sesion` | Autenticado |
| Borrar ticket | `DELETE /bloqueos/{id}` | Siempre `409`: el historial no se borra |

Ejemplo para registrar un bloqueo:

```json
{"maquinaId":"EQ-EXT-02","tipoIntervencion":"CORRECTIVA","motivo":"Inspección de falla","confirmacionCandadoDs594":true,"referenciaFalla":"FALLA-2026-001"}
```

- `POST /bloqueos` acepta `Idempotency-Key` (UUID) para reintentos seguros.
- `PREVENTIVA` no lleva `referenciaFalla` y no suma fallas.
- MTBF = horas operativas / fallas correctivas (sin fallas: `null`, «no calculable»).
- Códigos de respuesta: 200, 201, 204, 400, 401, 403, 404, 409, 429. Nunca se devuelve SQL ni stack trace.
</details>

<details>
<summary><b>Pruebas automáticas</b></summary>

```bash
mvn test                                         # dominio, seguridad y HTTP (H2 en memoria)
bash scripts/test-postgres.sh                    # integración con PostgreSQL real (base efímera)
bash tests/android-nfc/run-tests.sh              # decodificador NFC (requiere Node.js)
python3 scripts/sync-web-assets.py --check       # copias web/Android sincronizadas
```

`test-postgres.sh` necesita un usuario con `CREATEDB` (variables `PGHOST`, `PGUSER`, `PGPASSWORD`) y `TEST_DB_USERNAME`/`TEST_DB_PASSWORD` del rol de aplicación. Crea y borra su propia base: no apuntarlo a producción.
GitHub Actions ejecuta estas pruebas en cada Pull Request y compila el APK Android (workflow `android-nfc.yml`).
</details>

<details>
<summary><b>Compilar el APK Android</b></summary>

Requiere Android SDK (API 34, Build Tools 35.0.0) en `ANDROID_SDK_ROOT`:

```bash
bash android-app/build-apk.sh    # genera android-app/build/silbom-tecnico.apk
```

También se puede ejecutar el workflow **Android NFC - APK Debug** desde la pestaña *Actions* y descargar el artefacto.
</details>

<details>
<summary><b>Seguridad y pendientes</b></summary>

Detalle en [docs/controles-seguridad.md](docs/controles-seguridad.md) y [docs/auditoria-backend.md](docs/auditoria-backend.md).

Resumen:

- BCrypt (costo 12) y HTTP Basic individual.
- Cifrado AES-256-GCM de notas.
- RLS por planta.
- Historial inmutable.
- Ningún secreto versionado.

Pendientes:

- HTTPS en producción.
- Etiquetas NFC on-metal definitivas.
- Período de medición explícito para el MTBF.
- Rotación de credenciales.
- Paginación y observabilidad.
</details>
