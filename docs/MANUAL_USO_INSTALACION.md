# Manual de Instalación, Configuración y Uso (Hito 3)

**SILBOM — Sistema Inteligente de Lectura y Bloqueo Operativo de Maquinarias**  
*Asignatura:* INGT1003 Arquitectura de Desarrollo (Móvil y Web)  
*Escuela de Ingeniería Civil en Computación e Informática · Universidad Mayor*

Este manual permite a un tercero o evaluador docente desplegar, configurar y operar la solución completa de SILBOM en un computador con sistema operativo Linux, macOS o Windows, recorriendo el flujo punta a punta tanto en la Consola Web del Supervisor como en el Cliente Móvil Android.

---

## 1. Requisitos Previos

Para ejecutar la solución en un entorno local se requieren los siguientes componentes de software:

| Herramienta | Versión mínima | Comando de verificación | Propósito |
|---|---|---|---|
| **Java Development Kit (JDK)** | 21 LTS | `javac -version` | Compilación y ejecución del backend Spring Boot 3.5.16 |
| **Apache Maven** | 3.9+ | `mvn -version` | Gestión de dependencias del ciclo de construcción |
| **PostgreSQL** | 15, 16 o 17 | `psql --version` | Motor de base de datos relacional con soporte RLS |
| **Navegador web moderno** | Última versión | Chrome, Firefox o Edge | Acceso a la Consola Supervisor y cliente web de terreno |
| **Terminal Android (Opcional)** | Android 7.0+ (SDK 24 a 34) | Ajustes > Información del teléfono | Ejecución en terreno del archivo `silbom-tecnico.apk` con NFC |

> **Aviso de plataforma móvil:** SILBOM opera de manera exclusiva sobre el ecosistema **Android**. No se entrega soporte para terminales Apple iOS (iPhone/iPad) debido a restricciones de hardware para compilación (macOS/Xcode), costos de licenciamiento del *Apple Developer Program* y las políticas de bloqueo para instalación directa (*sideloading*) de instaladores corporativos en terreno.

---

## 2. Instalación Paso a Paso

Sigue esta secuencia para levantar el entorno desde cero en una máquina limpia:

### Paso 1: Clonar el repositorio
Abre una terminal y descarga el código fuente del proyecto:

```bash
git clone https://github.com/Bvstivn-A/Silbom.git
cd Silbom
```

### Paso 2: Configurar la base de datos PostgreSQL
Inicia el servicio de PostgreSQL en tu sistema. Crea los roles de migración (`silbom_owner`) y de aplicación (`silbom_app`), asignando contraseñas seguras a cada uno, junto con la base de datos `silbom_db`:

```bash
sudo -u postgres createuser --pwprompt silbom_owner
sudo -u postgres createuser --pwprompt silbom_app
sudo -u postgres createdb --owner=silbom_owner silbom_db
```

Ejecuta los dos scripts SQL transaccionales en orden estricto utilizando el usuario propietario:

```bash
psql -h localhost -U silbom_owner -d silbom_db -v ON_ERROR_STOP=1 -f db/schema.sql
psql -h localhost -U silbom_owner -d silbom_db -v ON_ERROR_STOP=1 -f db/migrations/V2__integridad_loto.sql
```

> **Garantía de integridad:** El esquema aplica políticas RLS (*Row-Level Security*), claves foráneas compuestas por planta y restringe al rol de aplicación `silbom_app` de ejecutar sentencias `DELETE` o `DROP TABLE`.

### Paso 3: Configurar variables de entorno (`.env`)
Copia la plantilla base y ajusta los permisos del archivo para que solo sea legible por tu usuario:

```bash
cp .env.example .env
chmod 600 .env
```

Genera una clave criptográfica de 32 bytes (256 bits) en Base64 para el cifrado AES-256-GCM de las notas de auditoría:

```bash
openssl rand -base64 32
```

Edita el archivo `.env` con un editor de texto (por ejemplo `nano .env`). Asigna los valores correspondientes **sin comillas** (Spring Boot lo interpreta con formato Java Properties):

```ini
DB_URL=jdbc:postgresql://localhost:5432/silbom_db
DB_USERNAME=silbom_app
DB_PASSWORD=tu_contraseña_silbom_app
ENCRYPTION_SECRET=pega_aqui_la_clave_base64_generada
PLANTA_ID=PLANTA-SAN-JOAQUIN
SERVER_PORT=8080
SILBOM_BOOTSTRAP_USERNAME=supervisor-local
SILBOM_BOOTSTRAP_PASSWORD=SupervisorDemo2026!
```

### Paso 4: Compilar y arrancar el backend
Ejecuta el servidor Spring Boot desde la raíz del proyecto:

```bash
mvn spring-boot:run
```

O genera el archivo JAR empaquetado y ejecútalo con la JVM:

```bash
mvn clean package
java -jar target/silbom-backend-1.0.0.jar
```

Abre en tu navegador **`http://localhost:8080/`**. Debes observar en el extremo superior el indicador verde **`🟢 API Conectada (PostgreSQL)`**. En este primer arranque, el componente `DataInitializer` creará de manera automática la cuenta supervisora y precargará las 6 máquinas de la planta.

### Paso 5: Instalación de la aplicación móvil Android
Para probar el cliente en un teléfono Android físico:
1. Accede desde el teléfono a la pestaña de entregas en GitHub:  
   👉 **[Descargar instalador en GitHub Releases](https://github.com/Bvstivn-A/Silbom/releases)**
2. Descarga el paquete `silbom-tecnico.apk` correspondiente a la Pre-release de pruebas.
3. Abre el archivo descargado y autoriza la instalación de aplicaciones de orígenes desconocidos en tu navegador móvil.
4. Una vez instalada, abre **SILBOM Técnico** y pulsa el botón **⚙️ IP** en la barra superior.
5. Si el computador y el teléfono están en la misma red Wi-Fi doméstica, ingresa la IP local de tu computador (ej. `http://192.168.1.100:8080`).
6. Si estás en una red Wi-Fi institucional (como la red de la universidad) que aísla los dispositivos, conecta el teléfono al PC mediante cable USB con la *Depuración USB* activada y corre en tu terminal:
   ```bash
   adb reverse tcp:8080 tcp:8080
   ```
   Luego en la aplicación pulsa **💻 Localhost (8080)** y presiona **Guardar IP y Probar Conexión**.

---

## 3. Usuarios y Datos de Prueba (100% Ficticios)

En estricto cumplimiento de la **Ley 21.719 sobre Protección de Datos Personales**, todo el entorno de evaluación opera exclusivamente con datos simulados y ficticios.

### Tabla de credenciales de prueba

| Usuario | Contraseña | Rol | Origen y permisos |
|---|---|---|---|
| `supervisor-local` | `SupervisorDemo2026!` | `SUPERVISOR` | Cuenta maestra creada al primer arranque mediante las variables bootstrap de `.env`. Tiene acceso a la gestión de técnicos, visualización de KPIs, auditoría global y cálculo de MTBF. |
| `tecnico1` | `SilbomTec_123456` | `TECNICO` | Técnico de terreno. Se crea durante la prueba desde la Consola Supervisor. Permite aplicar bloqueos LOTO, registrar notas confidenciales y liberar sus propios candados. |

### Máquinas precargadas (Planta San Joaquín)

| Identificador | Nombre del equipo | Área de planta | Horas operativas | Fallas previas | MTBF inicial |
|---|---|---|---|---|---|
| `EQ-ENV-01` | Envasadora Rotativa Automática | Línea de Envasado 1 | 701.5 hrs | 3 | 233.8 hrs |
| `EQ-PR-04` | Prensa Hidráulica 200T | Área de Estampado | 712.0 hrs | 2 | 356.0 hrs |
| `EQ-EXT-02` | Extrusora de Polímeros | Área de Moldeo | 685.2 hrs | 4 | 171.3 hrs |
| `EQ-MEZ-01` | Mezclador Industrial de Cinta | Área de Preparación | 715.0 hrs | 1 | 715.0 hrs |
| `EQ-COM-03` | Compresor de Tornillo | Sala de Máquinas | 718.5 hrs | 0 | *Sin fallas* |
| `EQ-TR-01` | Cinta Transportadora Principal | Logística y Despacho | 708.0 hrs | 2 | 354.0 hrs |

---

## 4. Guía de Uso Rápido (Flujo Principal Punta a Punta)

Este recorrido permite evaluar la integración completa entre el frontend, el backend y la base de datos sin necesidad de hardware móvil adicional:

```
[1. Supervisor en PC]  ──► [2. Crear Técnico] ──► [3. NFC Simulado en /app/]
          ▲                                                   │
          │                                                   ▼
[6. Auditoría y MTBF] ◄── [5. F5 Persistencia] ◄── [4. Aplicar Bloqueo LOTO]
```

### 1. Iniciar sesión en la Consola Supervisor
1. Entra a `http://localhost:8080/`.
2. En la barra superior ingresa con `supervisor-local` y la contraseña `SupervisorDemo2026!`.
3. Haz clic en **Iniciar Sesión**. La barra mostrará el estado de la sesión activa en memoria.

### 2. Registrar un nuevo técnico de mantenimiento
1. Haz clic en el botón **👥 Técnicos** del panel principal.
2. En el modal de gestión, completa el formulario con los datos de prueba:
   - **Nombre completo:** `Técnico de Terreno 1`
   - **Nombre de usuario:** `tecnico1`
   - **Contraseña:** `SilbomTec_123456` *(debe tener al menos 12 caracteres)*
   - **Rol:** `Técnico LOTO`
3. Presiona **Guardar Técnico**. El servidor responderá `201 Created` y la tabla listará al nuevo usuario con su hash BCrypt persistido en PostgreSQL. Cierra el modal.

### 3. Simular escaneo de etiqueta NFC en terreno
1. Abre una nueva pestaña o ventana del navegador en la URL:  
   **`http://localhost:8080/app/?maquina=EQ-ENV-01`**
   > **Mecanismo de prueba:** El parámetro `?maquina=EQ-ENV-01` simula la lectura automática del tag NFC físico instalado sobre la Envasadora Rotativa, cargando sus datos de inmediato sin requerir un sensor de hardware.
2. Ve a la pestaña **👤 Técnicos / Sesión** en la barra de navegación inferior.
3. Inicia sesión con el usuario recién creado: `tecnico1` y contraseña `SilbomTec_123456`.
4. Vuelve a la pestaña **🔒 Operar LOTO**.
5. Comprueba que el **Paso 1 (Identificar)** tiene seleccionada automáticamente la máquina `EQ-ENV-01`.
6. En el **Paso 2 (Bloqueo)**:
   - Selecciona Tipo de intervención: `CORRECTIVA`.
   - Ingresa el Motivo: `Falla en cabezal de sellado térmico`.
   - Ingresa una Nota confidencial: `Se desenergiza interruptor Q3 y se purga línea de aire comprimido`.
   - Marca la casilla obligatoria: **`Confirmo instalación de candado físico (DS 594)`**.
   - Presiona el botón **Aplicar Bloqueo LOTO**.
7. La aplicación pasa al **Paso 3 (En Curso)** mostrando el ticket generado en estado `ACTIVO`.

### 4. Demostrar persistencia real tras recarga de página (F5)
1. Regresa a la pestaña de la Consola Supervisor en `http://localhost:8080/`.
2. Presiona la tecla **`F5`** (o el botón de recarga del navegador).
3. **Comprobación:** La máquina `EQ-ENV-01` permanece en color rojo con la leyenda **`BLOQUEADA (1 bloqueo activo)`** y el botón de intervención en curso. Esto demuestra que los datos no residen en la memoria volátil del navegador ni en almacenamiento local, sino que fueron persistidos en la base de datos PostgreSQL.

### 5. Verificar control de propiedad del candado (`403 Forbidden`)
1. Desde la Consola del Supervisor (`http://localhost:8080/`), intenta hacer clic en el botón de desbloqueo de `EQ-ENV-01`.
2. El sistema bloqueará la acción y el servidor devolverá el código **`403 Forbidden`** indicando que solo el técnico `tecnico1` que instaló el candado puede retirarlo. Esta regla previene accidentes fatales en planta y cumple el estándar de seguridad industrial.

### 6. Liberación del candado y auditoría inmutable
1. En la pestaña del técnico (`http://localhost:8080/app/`), pulsa **Liberar Bloqueo LOTO** y confirma la acción.
2. Vuelve a la Consola Supervisor (`http://localhost:8080/`) y recarga con **`F5`**: la máquina `EQ-ENV-01` vuelve al estado **OPERATIVA** (verde).
3. En la tabla inferior de historial de tickets, haz clic en **Auditoría / Eventos** del ticket recién cerrado: podrás observar la traza inmutable de auditoría con el evento `CREACION` y `LIBERACION`, los sellos de tiempo exactos y la nota confidencial descifrada en pantalla.

---

## 5. Solución de Fallas Frecuentes

### Falla 1: Error de conexión a PostgreSQL
- **Síntoma:** El backend no inicia y muestra en consola `Connection to localhost:5432 refused` o `FATAL: password authentication failed for user "silbom_app"`.
- **Causa probable:** El motor de PostgreSQL está apagado, el puerto `5432` está bloqueado o la contraseña de `silbom_app` en `.env` no coincide con la configurada en PostgreSQL.
- **Solución paso a paso:**
  1. Comprueba el estado del servicio:
     ```bash
     sudo systemctl status postgresql
     ```
     Si está inactivo, inícialo con `sudo systemctl start postgresql`.
  2. Valida el acceso con el cliente de PostgreSQL usando las credenciales de `.env`:
     ```bash
     psql -h localhost -U silbom_app -d silbom_db
     ```
  3. Si la clave no coincide, cámbiala desde el usuario administrativo de PostgreSQL:
     ```sql
     ALTER USER silbom_app WITH PASSWORD 'tu_nueva_contraseña';
     ```
     Y actualiza `DB_PASSWORD` en tu archivo `.env`.

### Falla 2: Falla al arrancar por variables de entorno o clave AES inválida
- **Síntoma:** Excepción `IllegalArgumentException: Bootstrap requiere usuario válido y contraseña de 12 caracteres` o error al inicializar el bean de cifrado `CryptoUtils`.
- **Causa probable:** El archivo `.env` no existe en la raíz de ejecución, los valores contienen comillas de shell (ej. `DB_PASSWORD="clave"`) o `ENCRYPTION_SECRET` no tiene exactamente 32 bytes en formato Base64.
- **Solución paso a paso:**
  1. Verifica que el archivo se llame exactamente `.env` y esté ubicado en el mismo directorio desde donde ejecutas Maven.
  2. Abre `.env` y elimina cualquier comilla simple o doble alrededor de los valores.
  3. Genera una clave limpia de exactamente 32 bytes con OpenSSL y pégala en `ENCRYPTION_SECRET`:
     ```bash
     openssl rand -base64 32
     ```
  4. Comprueba que `SILBOM_BOOTSTRAP_PASSWORD` tenga al menos 12 caracteres (por ejemplo: `SupervisorDemo2026!`).

### Falla 3: El smartphone Android no conecta al backend en Wi-Fi universitario
- **Síntoma:** La aplicación móvil muestra `No responde http://10.50.X.X:8080. Verifica Wi-Fi y puerto 8080` y el badge se mantiene en color amarillo `Modo Demo Local (Offline)`.
- **Causa probable:** Los puntos de acceso de la red Wi-Fi universitaria tienen activada la función de aislamiento de clientes (*AP Isolation*), impidiendo la comunicación directa por paquetes TCP entre el teléfono y el computador.
- **Solución paso a paso:**
  - **Opción A (Recomendada - Túnel por cable USB):**
    1. Conecta el teléfono al computador mediante cable USB.
    2. Activa la casilla **Depuración USB** en *Ajustes > Opciones de desarrollador* del teléfono.
    3. En la terminal de tu PC ejecuta el comando de reenvío inverso de puertos:
       ```bash
       adb reverse tcp:8080 tcp:8080
       ```
    4. En la app móvil, abre **⚙️ IP**, pulsa el botón **💻 Localhost (8080)** y presiona **Guardar IP y Probar Conexión**. La app se conectará al instante a través del cable sin depender de la red Wi-Fi.
  - **Opción B (Zona Wi-Fi portátil / Hotspot):**
    1. Activa la zona de cobertura Wi-Fi (*Hotspot móvil*) en tu teléfono celular.
    2. Conecta el computador a esa red Wi-Fi compartida.
    3. Revisa la nueva dirección IP asignada a tu computador ejecutando `hostname -I` en Linux o `ipconfig` en Windows.
    4. Ingresa esa nueva IP en el campo de configuración de la app móvil (ejemplo: `http://192.168.43.15:8080`).
  - **Opción C (Firewall local de Linux):**
    Comprueba que el puerto no esté bloqueado por UFW en tu computador:
    ```bash
    sudo ufw allow 8080/tcp
    ```

### Falla 4: Código `403 Forbidden` al intentar liberar un bloqueo LOTO
- **Síntoma:** Al pulsar el botón de liberación de un equipo, la aplicación muestra una alerta roja `403 Forbidden` y el candado no se abre.
- **Causa probable:** La sesión activa en ese momento no pertenece al técnico responsable que instaló el bloqueo original.
- **Solución paso a paso:**
  1. Identifica el usuario responsable asignado al ticket revisando el campo `Dueño` en la tabla de bloqueos.
  2. En la aplicación móvil, ve a la pestaña **👤 Técnicos / Sesión** y pulsa **Cerrar Sesión**.
  3. Inicia sesión con el nombre de usuario y contraseña del técnico que colocó el candado (por ejemplo `tecnico1`).
  4. Vuelve a la pestaña de operación y ejecuta la liberación. La operación se procesará de forma autorizada.
