# SILBOM — Seguridad LOTO con NFC

> **Una capa de auditoría digital sobre el candado que la ley ya exige.**
> Identifica cada máquina con NFC, registra cada candado LOTO y lo muestra en vivo al supervisor.

**Video del producto:** [Ver en YouTube](PEGAR_AQUI_EL_ENLACE_DEL_VIDEO)
**App Android (APK):** [Releases del repositorio](https://github.com/Bvstivn-A/Silbom/releases)
**Historial del Hito 1:** [github.com/Vicente-PR/SILBOM](https://github.com/Vicente-PR/SILBOM) (ver la sección [Historial del proyecto](#historial-del-proyecto))

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

## Instalación rápida (Windows, macOS o Linux)

Tiempo estimado: 20–30 minutos la primera vez. Todos los comandos se ejecutan en una terminal (en Windows: **PowerShell**).

### Paso 1 · Instalar los programas

Necesitas **Git**, **JDK 21** (el kit completo, no solo Java), **Maven 3.9+** y **PostgreSQL 15, 16 o 17**.

<details>
<summary><b>Windows</b></summary>

```powershell
winget install Git.Git
winget install EclipseAdoptium.Temurin.21.JDK
winget install PostgreSQL.PostgreSQL.17
```

- Durante la instalación de PostgreSQL se te pide una **contraseña para el usuario `postgres`**: anótala.
- **Maven:** descarga el *Binary zip archive* desde <https://maven.apache.org/download.cgi>, descomprímelo (por ejemplo en `C:\maven`) y agrega `C:\maven\bin` a la variable de entorno `Path`.
- Agrega también `C:\Program Files\PostgreSQL\17\bin` al `Path` para poder usar `psql`.
- Cierra y vuelve a abrir PowerShell después de cambiar el `Path`.
</details>

<details>
<summary><b>macOS</b> (con <a href="https://brew.sh">Homebrew</a>)</summary>

```bash
brew install git openjdk@21 maven postgresql@17
brew services start postgresql@17
```
</details>

<details>
<summary><b>Linux — Ubuntu / Debian / Mint</b></summary>

```bash
sudo apt update
sudo apt install git openjdk-21-jdk maven postgresql
sudo systemctl enable --now postgresql
```
</details>

<details>
<summary><b>Linux — Fedora</b></summary>

```bash
sudo dnf install git java-21-openjdk-devel maven postgresql-server
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

Fedora trae PostgreSQL configurado para no aceptar contraseñas en `localhost`. Si más adelante ves `Ident authentication failed`, revisa la sección [Problemas frecuentes](#problemas-frecuentes).
</details>

Comprueba que todo quedó instalado (cada comando debe mostrar una versión):

```bash
git --version
java -version
javac -version
mvn -version
psql --version
```

`java` y `javac` deben decir **21**.

### Paso 2 · Descargar el proyecto

```bash
git clone https://github.com/Bvstivn-A/Silbom.git
cd Silbom
```

Desde aquí, **todos los comandos se ejecutan dentro de la carpeta `Silbom`**.

### Paso 3 · Crear la base de datos

Abre la consola de PostgreSQL como administrador:

| Sistema | Comando |
|---|---|
| Windows | `psql -U postgres -h localhost` (pide la contraseña del Paso 1) |
| macOS | `psql postgres` |
| Linux | `sudo -u postgres psql` |

Dentro de esa consola pega lo siguiente. **Cambia las dos contraseñas** por unas tuyas (solo letras y números) y anótalas:

```sql
CREATE ROLE silbom_owner LOGIN PASSWORD 'ClaveDueno2026';
CREATE ROLE silbom_app   LOGIN PASSWORD 'ClaveApp2026';
CREATE DATABASE silbom_db OWNER silbom_owner;
\q
```

Ahora crea las tablas (te pedirá la contraseña de `silbom_owner`):

```bash
psql -h localhost -U silbom_owner -d silbom_db -v ON_ERROR_STOP=1 -f db/schema.sql
```

Es normal ver algunos mensajes `NOTICE: ... does not exist, skipping`. El script se puede ejecutar más de una vez sin borrar datos.

> ¿Por qué dos usuarios? `silbom_owner` crea las tablas; `silbom_app` es el que usa el servidor y **no puede borrar historial**. Así se protege la trazabilidad.

### Paso 4 · Configurar el archivo `.env`

Copia la plantilla:

| Sistema | Comando |
|---|---|
| Windows | `copy .env.example .env` |
| macOS / Linux | `cp .env.example .env` |

Genera una **clave de cifrado** (sirve para cifrar las notas confidenciales):

| Sistema | Comando |
|---|---|
| Windows (PowerShell) | `$b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); [Convert]::ToBase64String($b)` |
| macOS / Linux | `openssl rand -base64 32` |

Abre `.env` con cualquier editor de texto (Bloc de notas, VS Code, nano…) y cambia **solo estas líneas**:

```properties
DB_PASSWORD=ClaveApp2026                     # la contraseña de silbom_app del Paso 3
ENCRYPTION_SECRET=pega_aqui_la_clave_generada # el texto que generó el comando anterior

SILBOM_DEMO_TWO_USERS_ONLY=true
SILBOM_DEMO_SUPERVISOR_PASSWORD=EligeUnaClave1  # contraseña para entrar como "supervisor"
SILBOM_DEMO_TECHNICIAN_PASSWORD=EligeOtraClave2 # contraseña para entrar como "tecnico"
```

Reglas importantes:

- Las contraseñas de la demo deben tener **al menos 12 caracteres**. Usa solo letras y números.
- **No uses comillas** y no dejes espacios alrededor del `=`.
- Ninguna línea puede quedar con un valor que empiece con `CAMBIAR_`.
- **Nunca subas `.env` a GitHub** (ya está en `.gitignore`).
- Guarda la clave de cifrado: si la cambias, las notas antiguas ya no se podrán leer.

Con esto quedan creadas dos cuentas: **`supervisor`** y **`tecnico`**.

<details>
<summary>Opcional (macOS / Linux): configurar las contraseñas de la demo con un asistente</summary>

```bash
python3 scripts/configurar-demo.py
```

Pide las dos contraseñas sin mostrarlas en pantalla y las escribe en `.env`. Más detalles en [docs/DEMO_DOS_CUENTAS.md](docs/DEMO_DOS_CUENTAS.md).
</details>

### Paso 5 · Compilar y arrancar

```bash
mvn clean package
java -jar target/silbom-backend-1.0.0.jar
```

La primera compilación descarga dependencias y ejecuta las pruebas automáticas (puede tardar unos minutos). Cuando veas `Started SilbomApplication`, el servidor está listo. **Deja esa terminal abierta** (para detenerlo: `Ctrl + C`).

En el primer arranque se cargan automáticamente **6 máquinas de demostración** de la «Planta San Joaquín».

### Paso 6 · Probarlo

1. Abre **<http://localhost:8080/>** → consola del supervisor. Inicia sesión con `supervisor` y su contraseña.
2. En otra pestaña abre **<http://localhost:8080/app/?maquina=EQ-EXT-02>** → app del técnico. El `?maquina=EQ-EXT-02` simula haber leído la etiqueta NFC de la Extrusora. Inicia sesión con `tecnico`.
3. Registra un bloqueo: elige el tipo de intervención, escribe una referencia de falla (ejemplo `FALLA-2026-001`), confirma el candado físico y aplica el bloqueo.
4. Vuelve a la consola: en máximo 10 segundos la Extrusora aparece **en rojo** con su bloqueo activo. Aunque recargues la página (F5), sigue ahí: está guardado en PostgreSQL.
5. Desde la app del técnico, **libera** el bloqueo. La consola vuelve a mostrar la máquina disponible y el ticket queda en el historial.

> El supervisor **no puede** liberar el candado de un técnico: solo su dueño puede hacerlo (el servidor responde `403`).

---

## App Android con NFC (opcional)

Para probar con un celular real y etiquetas NFC:

1. **PC y celular en la misma red Wi-Fi.** Averigua la IP del PC:
   - Windows: `ipconfig` (línea «Dirección IPv4»)
   - macOS: `ipconfig getifaddr en0`
   - Linux: `hostname -I`
2. Instala la app: descarga `silbom-tecnico.apk` desde [Releases](https://github.com/Bvstivn-A/Silbom/releases), ábrelo en el celular y permite instalar apps de «orígenes desconocidos».
3. En la app, toca **⚙️ Conectar a IP del Servidor** y escribe `http://IP-DEL-PC:8080` (por ejemplo `http://192.168.1.20:8080`). Inicia sesión con `tecnico`.
4. Escribe las etiquetas con la app gratuita **NFC Tools**: *Escribir → Añadir registro → Texto*, con **un solo registro** por etiqueta:

   | Texto de la etiqueta | Máquina |
   |---|---|
   | `EQ-EXT-02` | Extrusora de Polímeros |
   | `EQ-COM-03` | Compresor de Tornillo |
   | `EQ-ENV-01` | Envasadora Rotativa Automática |

5. Activa NFC en el celular, toca **Escanear etiqueta NFC** y acerca el teléfono a la etiqueta.

¿No tienes Android ni etiquetas? Desde el navegador de cualquier celular (también iPhone) entra a `http://IP-DEL-PC:8080/app/` y elige la máquina manualmente.

Guías detalladas: [Android y NFC](docs/ANDROID_NFC_PRUEBAS.md) · [Pruebas móviles con HTTPS y QR](docs/PRUEBAS_MOVILES.md) · [iPhone y Safari](docs/IPHONE_SAFARI.md).

> Las contraseñas viajan por HTTP dentro de tu red local: úsalo solo para demostraciones. Para un uso real se necesita HTTPS ([deploy/Caddyfile.local](deploy/Caddyfile.local)).

---

## Problemas frecuentes

| Mensaje o síntoma | Solución |
|---|---|
| `javac` no se reconoce o no dice 21 | Instalaste solo Java (JRE). Instala el **JDK 21** (Paso 1). |
| `mvn` / `psql` no se reconoce (Windows) | Falta agregar su carpeta `bin` al `Path`. Luego cierra y abre PowerShell. |
| `Unable to determine Dialect` o `password authentication failed` | `DB_PASSWORD` en `.env` no coincide con la contraseña de `silbom_app`, o PostgreSQL no está iniciado. |
| `Ident authentication failed` (Fedora/RHEL) | En `/var/lib/pgsql/data/pg_hba.conf` cambia `ident` por `scram-sha-256` en las líneas `host`, y luego `sudo systemctl restart postgresql`. |
| `encryption-secret debe decodificar a exactamente 32 bytes` | Genera de nuevo la clave del Paso 4 y pégala completa, sin comillas ni espacios. |
| `Bootstrap requiere usuario válido y contraseña de 12 caracteres` | Revisa que `SILBOM_DEMO_TWO_USERS_ONLY=true` esté escrito así, o borra las líneas `SILBOM_BOOTSTRAP_…`. |
| `Port 8080 was already in use` | Ya hay otro SILBOM abierto. Ciérralo, o cambia `SERVER_PORT=8081` en `.env`. |
| El celular no conecta al PC | Misma red Wi-Fi; usa la IP del PC, no `localhost`; permite el puerto 8080 en el firewall (Windows lo pregunta al primer arranque; Fedora: `sudo firewall-cmd --add-port=8080/tcp`). Las redes de universidad suelen bloquear conexiones entre equipos: usa el hotspot del celular. |
| La consola dice «Inicia sesión» y no muestra historial | Inicia sesión como `supervisor` en la barra superior. |
| El navegador rellena el usuario con otro nombre | Escribe exactamente `supervisor` o `tecnico`. |

---

## Documentación y entregas

| Documento | Enlace |
|---|---|
| Propuesta Hito 1 | [PDF](<docs/SILBOM_Propuesta_Hito1 (5).pdf>) |
| Presentación Hito 1 | [PDF](<docs/SILBOM_Presentacion_Hito1 (1).pdf>) |
| Informe Hito 2 | [PDF](docs/SILBOM_Informe_Hito2.pdf) |
| Carta Gantt | [PDF](docs/Carta_Gantt_SILBOM.pdf) |
| Video Hito 3 | [YouTube](PEGAR_AQUI_EL_ENLACE_DEL_VIDEO) |
| Diagrama de arquitectura | [PNG](docs/diagrama-arquitectura.png) |
| Mapa de producto | [PNG](docs/mapa-producto.png) |
| Modelo de datos y script SQL | [db/modelo_datos.md](db/modelo_datos.md) · [db/schema.sql](db/schema.sql) |
| Controles de seguridad | [docs/controles-seguridad.md](docs/controles-seguridad.md) |
| Auditoría del backend | [docs/auditoria-backend.md](docs/auditoria-backend.md) |
| Colección Postman | [docs/SILBOM_Postman_Collection.json](docs/SILBOM_Postman_Collection.json) |

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
