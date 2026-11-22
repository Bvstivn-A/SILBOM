# Manual de instalación y uso — SILBOM

> Sistema Inteligente de Lectura y Bloqueo Operativo de Maquinarias.
> Este manual permite instalar SILBOM en cualquier computador (Windows, macOS o Linux), cargar los datos de prueba y recorrer el flujo principal.
> Volver al [README](../README.md).

**Contenido**

1. [Requisitos](#1-requisitos)
2. [Instalación paso a paso](#2-instalación-paso-a-paso-windows-macos-o-linux)
3. [Datos de prueba](#3-datos-de-prueba)
4. [Uso del sistema](#4-uso-del-sistema)
5. [App Android con NFC](#5-app-android-con-nfc-opcional)
6. [Fallas frecuentes](#6-fallas-frecuentes)

---

## 1. Requisitos

| Componente | Versión | Para qué |
|---|---|---|
| Sistema operativo | Windows 10/11, macOS o Linux (Ubuntu, Debian, Mint, Fedora) | Computador que hará de servidor |
| Git | Cualquiera reciente | Descargar el proyecto |
| JDK (kit de desarrollo de Java) | **21** | Compilar y ejecutar el servidor |
| Maven | 3.6.3 o superior | Compilar el proyecto y bajar dependencias |
| PostgreSQL | 15, 16 o 17 | Base de datos |
| Navegador | Chrome, Firefox, Edge o Safari | Consola del supervisor y app web del técnico |
| Internet | Solo durante la primera compilación | Maven descarga las dependencias |
| *Opcional:* celular Android 7.0+ con NFC | — | App nativa y lectura de etiquetas |
| *Opcional:* etiquetas NFC (NTAG213/215) | — | Identificar las máquinas |

---

## 2. Instalación paso a paso (Windows, macOS o Linux)

Tiempo estimado: 20–30 minutos la primera vez. Todos los comandos se ejecutan en una terminal (en Windows: **PowerShell**).

### Paso 1 · Instalar los programas

Los requisitos están en la [sección 1](#1-requisitos). Necesitas **Git**, **JDK 21** (el kit completo, no solo Java), **Maven 3.6.3 o superior** y **PostgreSQL 15, 16 o 17**.

<details>
<summary><b>Windows</b></summary>

```powershell
winget install Git.Git
winget install EclipseAdoptium.Temurin.21.JDK
winget install --interactive -e --id PostgreSQL.PostgreSQL.17
```

- El instalador de PostgreSQL te pide una **contraseña para el usuario `postgres`**: anótala. (Si lo instalaste sin `--interactive`, esa contraseña queda como `postgres`.)
- **Maven:** descarga el *Binary zip archive* desde <https://maven.apache.org/download.cgi>, descomprímelo (por ejemplo en `C:\maven`) y agrega `C:\maven\bin` a la variable de entorno `Path`.
- Agrega también `C:\Program Files\PostgreSQL\17\bin` al `Path` para poder usar `psql`.
- Cierra y vuelve a abrir PowerShell después de cambiar el `Path`.
</details>

<details>
<summary><b>macOS</b> (con <a href="https://brew.sh">Homebrew</a>)</summary>

```bash
brew install git openjdk@21 maven postgresql@17
brew services start postgresql@17
echo 'export JAVA_HOME="$(brew --prefix openjdk@21)"' >> ~/.zshrc
echo 'export PATH="$JAVA_HOME/bin:$(brew --prefix postgresql@17)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Las dos líneas `export` hacen que la terminal use Java 21 y encuentre `psql` (Homebrew no los deja en el `PATH` por defecto).
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

Fedora trae PostgreSQL configurado para no aceptar contraseñas en `localhost`. Si más adelante ves `Ident authentication failed`, revisa la sección [Problemas frecuentes](#6-fallas-frecuentes).
</details>

Comprueba que todo quedó instalado (cada comando debe mostrar una versión):

```bash
git --version
java -version
javac -version
mvn -version
psql --version
```

`java` y `javac` deben decir **21**, y `mvn -version` debe mostrar «Java version: 21». Si muestra otra versión, define la variable `JAVA_HOME` apuntando al JDK 21.

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

Si vas a usar la **app Android** (sección 5), agrega también esta línea, en una sola línea y tal cual:

```properties
SILBOM_CORS_ORIGINS=http://localhost:*,http://127.0.0.1:*,https://localhost:*,https://127.0.0.1:*,https://silbom.netlify.app,null
```

La app Android carga sus pantallas desde el propio celular, así que el servidor recibe sus peticiones con origen `null`. Sin esta línea, el servidor rechaza los bloqueos (error 403) y la app los guarda solo en el celular: nunca llegan a la consola del supervisor. Úsala solo en tu red local para la demostración.

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

Pide las dos contraseñas sin mostrarlas en pantalla y las escribe en `.env`. Más detalles en [docs/DEMO_DOS_CUENTAS.md](DEMO_DOS_CUENTAS.md).
</details>

### Paso 5 · Compilar y arrancar

```bash
mvn clean package
java -jar target/silbom-backend-1.0.0.jar
```

La primera compilación descarga dependencias y ejecuta las pruebas automáticas (puede tardar unos minutos). Cuando veas `Started SilbomApplication`, el servidor está listo. **Deja esa terminal abierta** (para detenerlo: `Ctrl + C`).

En el primer arranque se cargan automáticamente **6 máquinas de demostración** de la «Planta San Joaquín».

---

## 3. Datos de prueba

Todos los datos son **ficticios**. No cargues datos reales de personas.

**Cuentas** (creadas desde `.env` con `SILBOM_DEMO_TWO_USERS_ONLY=true`):

| Usuario | Rol | Contraseña | Dónde entra |
|---|---|---|---|
| `supervisor` | Supervisor | La que pusiste en `SILBOM_DEMO_SUPERVISOR_PASSWORD` | Consola `http://localhost:8080/` |
| `tecnico` | Técnico | La que pusiste en `SILBOM_DEMO_TECHNICIAN_PASSWORD` | App `http://localhost:8080/app/` o APK |

**Máquinas** (se cargan solas en el primer arranque, Planta San Joaquín):

| Código | Máquina | Área |
|---|---|---|
| `EQ-ENV-01` | Envasadora Rotativa Automática | Línea de Envasado 1 |
| `EQ-PR-04` | Prensa Hidráulica 200T | Área de Estampado |
| `EQ-EXT-02` | Extrusora de Polímeros | Área de Moldeo |
| `EQ-MEZ-01` | Mezclador Industrial de Cinta | Área de Preparación |
| `EQ-COM-03` | Compresor de Tornillo | Sala de Máquinas |
| `EQ-TR-01` | Cinta Transportadora Principal | Logística y Despacho |

También se cargan algunos tickets históricos de ejemplo para que el MTBF y el historial tengan datos.

**Ejemplo de bloqueo para probar:**

| Campo | Valor |
|---|---|
| Máquina | `EQ-EXT-02` |
| Tipo de intervención | Correctiva |
| Referencia de la falla | `FALLA-2026-001` |
| Motivo | `Inspección de falla en tornillo extrusor` |
| Candado físico | Marcar la confirmación (DS 594) |

---

## 4. Uso del sistema

| Pantalla | Quién | Qué puede hacer |
|---|---|---|
| **Consola** `http://localhost:8080/` | Supervisor | Ver las máquinas en vivo (rojo = bloqueada), KPIs y MTBF, historial de tickets y sus eventos. Se actualiza cada 10 segundos. |
| **App** `http://localhost:8080/app/` o APK | Técnico | Identificar la máquina (NFC, QR o lista), registrar su bloqueo, ver el cronómetro y liberar **su** candado. |

Reglas que verás al usarlo:

- Solo el técnico que puso el bloqueo puede liberarlo, ni siquiera el supervisor (responde `403`).
- Varios técnicos pueden bloquear la misma máquina a la vez (Multi-LOTO); queda bloqueada hasta que todos liberen.
- Los tickets no se borran: todo queda en el historial.
- Leer una etiqueta NFC solo identifica la máquina; nunca bloquea ni libera por sí sola.

### Recorrido completo (sin celular)

1. Abre **<http://localhost:8080/>** → consola del supervisor. Inicia sesión con `supervisor` y su contraseña.
2. En otra pestaña abre **<http://localhost:8080/app/?maquina=EQ-EXT-02>** → app del técnico. El `?maquina=EQ-EXT-02` simula haber leído la etiqueta NFC de la Extrusora. Inicia sesión con `tecnico`.
3. Registra un bloqueo: elige el tipo de intervención, escribe una referencia de falla (ejemplo `FALLA-2026-001`), confirma el candado físico y aplica el bloqueo.
4. Vuelve a la consola: en máximo 10 segundos la Extrusora aparece **en rojo** con su bloqueo activo. Aunque recargues la página (F5), sigue ahí: está guardado en PostgreSQL.
5. Desde la app del técnico, **libera** el bloqueo. La consola vuelve a mostrar la máquina disponible y el ticket queda en el historial.

> El supervisor **no puede** liberar el candado de un técnico: solo su dueño puede hacerlo (el servidor responde `403`).

---

## 5. App Android con NFC (opcional)

Para probar con un celular real y etiquetas NFC:

1. **PC y celular en la misma red.** El PC puede estar conectado por cable o por Wi-Fi, siempre que esté en el mismo router que el Wi-Fi del celular (no uses la red de invitados). Averigua la IP del PC; si tiene cable y Wi-Fi a la vez, usa la IP de la conexión que comparte red con el celular:
   - Windows: `ipconfig` (línea «Dirección IPv4»)
   - macOS: `ipconfig getifaddr en0`
   - Linux: `hostname -I`
2. Instala la app: descarga `silbom-tecnico.apk` de la versión **[v0.9.1-beta](https://github.com/Bvstivn-A/Silbom/releases/tag/v0.9.1-beta)**, ábrelo en el celular y permite instalar apps de «orígenes desconocidos». Las versiones v0.10.x (con QR) necesitan HTTPS y un certificado instalado en el celular ([Pruebas móviles con HTTPS y QR](PRUEBAS_MOVILES.md)); no funcionan con estos pasos.
3. Revisa que el `.env` del PC tenga la línea `SILBOM_CORS_ORIGINS` del Paso 4 y que el firewall permita el puerto 8080 (ver [Fallas frecuentes](#6-fallas-frecuentes)).
4. En la app, toca **⚙️ IP** (Conectar a IP del Servidor), escribe `http://IP-DEL-PC:8080` (por ejemplo `http://192.168.1.20:8080`) y toca **Guardar IP y Probar Conexión**. Debe aparecer **🟢 API Conectada**. Luego inicia sesión con `tecnico`.
5. Escribe las etiquetas con la app gratuita **NFC Tools**: *Escribir → Añadir registro → Texto*, con **un solo registro** por etiqueta:

   | Texto de la etiqueta | Máquina |
   |---|---|
   | `EQ-EXT-02` | Extrusora de Polímeros |
   | `EQ-COM-03` | Compresor de Tornillo |
   | `EQ-ENV-01` | Envasadora Rotativa Automática |

6. Activa NFC en el celular, abre la app y acerca la etiqueta a la parte trasera del teléfono (en la v0.9.1-beta el NFC queda activo al abrir la app; en versiones nuevas primero toca **Escanear etiqueta NFC**). Si aparece la pantalla de Android «Nueva etiqueta escaneada», la app no estaba abierta en primer plano.
7. Toca **Activar Bloqueo LOTO**. Debe aparecer **«¡BLOQUEO LOTO #… REGISTRADO!»** y la máquina se pone roja en la consola del supervisor.

¿No tienes Android ni etiquetas? Desde el navegador de cualquier celular (también iPhone) entra a `http://IP-DEL-PC:8080/app/` y elige la máquina manualmente.

Guías detalladas: [Android y NFC](ANDROID_NFC_PRUEBAS.md) · [Pruebas móviles con HTTPS y QR](PRUEBAS_MOVILES.md) · [iPhone y Safari](IPHONE_SAFARI.md).

> Las contraseñas viajan por HTTP dentro de tu red local: úsalo solo para demostraciones. Para un uso real se necesita HTTPS ([deploy/Caddyfile.local](../deploy/Caddyfile.local)).

---

## 6. Fallas frecuentes

| Mensaje o síntoma | Solución |
|---|---|
| `javac` no se reconoce o no dice 21 | Instalaste solo Java (JRE). Instala el **JDK 21** (Paso 1). |
| `mvn` / `psql` no se reconoce (Windows) | Falta agregar su carpeta `bin` al `Path`. Luego cierra y abre PowerShell. |
| `Unable to determine Dialect` o `password authentication failed` | `DB_PASSWORD` en `.env` no coincide con la contraseña de `silbom_app`, o PostgreSQL no está iniciado. |
| `Ident authentication failed` (Fedora/RHEL) | En `/var/lib/pgsql/data/pg_hba.conf` cambia `ident` por `scram-sha-256` en las líneas `host`, y luego `sudo systemctl restart postgresql`. |
| `encryption-secret debe decodificar a exactamente 32 bytes` | Genera de nuevo la clave del Paso 4 y pégala completa, sin comillas ni espacios. |
| `Bootstrap requiere usuario válido y contraseña de 12 caracteres` | Revisa que `SILBOM_DEMO_TWO_USERS_ONLY=true` esté escrito así, o borra las líneas `SILBOM_BOOTSTRAP_…`. |
| `Port 8080 was already in use` | Ya hay otro SILBOM abierto. Ciérralo, o cambia `SERVER_PORT=8081` en `.env`. |
| El celular no conecta al PC | Misma red (PC por cable o Wi-Fi, pero en el mismo router); usa la IP del PC con `http://`, no `localhost`; permite el puerto 8080 en el firewall (Windows lo pregunta al primer arranque: marca «Redes privadas»; Ubuntu/Pop!_OS: `sudo ufw allow 8080/tcp`; Fedora: `sudo firewall-cmd --add-port=8080/tcp`). Las redes de universidad suelen bloquear conexiones entre equipos: usa el hotspot del celular. |
| La app muestra el ticket, pero la máquina no se pone roja en la consola del supervisor | El bloqueo quedó guardado solo en el celular. Revisa que `.env` tenga la línea `SILBOM_CORS_ORIGINS` con `null` (Paso 4) y reinicia el servidor. Si la app perdió la conexión, ciérrala, ábrela de nuevo, comprueba que diga **🟢 API Conectada** e inicia sesión otra vez. Al bloquear debe aparecer «¡BLOQUEO LOTO #… REGISTRADO!». |
| La consola dice «Inicia sesión» y no muestra historial | Inicia sesión como `supervisor` en la barra superior. |
| El navegador rellena el usuario con otro nombre | Escribe exactamente `supervisor` o `tecnico`. |

---
