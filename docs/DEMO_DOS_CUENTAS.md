# Demostración con supervisor y técnico

Rama `feature/two-account-demo-access`, PR https://github.com/Bvstivn-A/Silbom/pull/4.
Modo optativo para una demostración universitaria; no es una configuración de producción.

## Estado y alcance

Con `SILBOM_DEMO_TWO_USERS_ONLY=true`, el backend admite exclusivamente los dos usernames configurados: `supervisor` con rol `SUPERVISOR` y `tecnico` con rol `TECNICO`. Spring Security comprueba contraseña BCrypt, estado activo, planta y rol esperado. Los servicios también rechazan contextos de identidad excluidos o inactivos.

Las cuentas anteriores permanecen en PostgreSQL, pero no pueden autenticarse durante la demo. POST, PUT y DELETE de identidades quedan prohibidos tanto en el filtro HTTP como en `TecnicoService`. Las lecturas administrativas autorizadas siguen disponibles para supervisión, junto con la administración actual de maquinaria. No se borran identidades, tickets ni eventos.

En el arranque se comprueba que no existan tickets activos sin un responsable habilitado: incluye terceros, responsables inactivos y tickets legados sin identidad. Si existe alguno, el arranque falla y la transacción se revierte. **No reasignar responsables, no cerrar tickets mediante SQL y no retirar candados por este cambio de modo.** Mantener el modo normal y resolverlos con el responsable y el procedimiento autorizado. Después detener las instancias anteriores y volver a intentar la activación.

Las cuentas nuevas se crean con los nombres visibles `Supervisor SILBOM` y `Técnico SILBOM`, sin contraseñas predeterminadas. Una cuenta existente de otro rol o desactivada exige revisión administrativa; no se reactiva ni se cambia su rol automáticamente. Se conserva su ID e historial. Si la contraseña ya coincide, el arranque conserva el hash BCrypt; si cambió el secreto configurado, actualiza su hash dentro de la transacción.

## Configuración local sin publicar contraseñas

El trabajo se preparó en Codex Cloud. **No se accedió al computador Fedora, a su `.env`, a su PostgreSQL ni a su servicio systemd. Las cuentas de esa máquina no se dan por activadas.** Las bases utilizadas aquí son efímeras y tienen credenciales aleatorias diferentes de las de la demostración.

En el computador donde ejecutas Spring Boot:

1. Revisa que estés en el repositorio nuevo `Bvstivn-A/Silbom` y en la rama indicada. Conserva los cambios de tus compañeros; no uses `reset --hard` ni reemplaces el proyecto anterior a ciegas.

   ```bash
   git status --short
   git branch --show-current
   git fetch origin feature/two-account-demo-access
   git pull --ff-only origin feature/two-account-demo-access
   ```

   Ejecuta el último comando únicamente estando en esa rama y con el árbol preparado para la actualización. No es necesario fusionar a `main` para demostrar esta rama.

2. Detén la instancia anterior antes de activar la nueva. Si todavía utilizas el servicio mostrado anteriormente:

   ```bash
   systemctl --user stop silbom-hito2
   systemctl --user is-active silbom-hito2
   ```

   `inactive` confirma que ese servicio se detuvo; comprueba que no haya otra instancia sirviendo el mismo puerto. Estos comandos van en una terminal que muestre el prompt, no en una ventana ocupada siguiendo registros. Detener el backend no retira ningún candado físico.

3. Conserva el `.env` local con la URL, usuario, contraseña PostgreSQL, planta y clave de cifrado existentes. No generes otra clave AES sobre una base con notas cifradas. Si aún no hay `.env` en este repositorio, prepara el archivo mediante el procedimiento del README y la configuración local conocida; no copies valores desde GitHub ni sustituyas la configuración por el ejemplo.

   ```bash
   git check-ignore .env
   chmod 600 .env
   python3 scripts/configurar-demo.py
   ```

   El configurador solicita, con entrada oculta y confirmación, las dos contraseñas que pediste para la demostración. **No están escritas en esta guía ni en el programa.** No pases contraseñas por argumentos, no uses `echo`, no compartas una captura del `.env` y no lo publiques.

   El archivo usa formato Java Properties, no shell: no ejecutes `source .env`. El configurador preserva PostgreSQL y los secretos existentes, rechaza un archivo versionado o un enlace simbólico, detecta variables demo duplicadas y sustituye el archivo atómicamente con permisos 0600. No cambia secretos demo ya presentes, excepto marcadores `CAMBIAR_`; confirma localmente que esos valores coincidan con los solicitados. Repetirlo no revela ni reemplaza secretos previos.

   Las variables no secretas resultantes son:

   ```properties
   SILBOM_DEMO_TWO_USERS_ONLY=true
   SILBOM_DEMO_SUPERVISOR_USERNAME=supervisor
   SILBOM_DEMO_TECHNICIAN_USERNAME=tecnico
   ```

   Los nombres de las variables secretas son `SILBOM_DEMO_SUPERVISOR_PASSWORD` y `SILBOM_DEMO_TECHNICIAN_PASSWORD`. Las variables exportadas del proceso tienen prioridad sobre `.env`; revisa en privado que systemd o el script de arranque no conserven valores anteriores. El programa no cambia variables de un servicio remoto.

4. Comprueba JDK **completo** 21 y Maven. No basta con tener solamente Java Runtime:

   ```bash
   java -version
   javac -version
   mvn -version
   mvn clean verify
   python3 scripts/sync-web-assets.py --check
   python3 -m unittest discover -s tests/configuracion -v
   ```

   Antes de compilar con el modo demo habilitado, utiliza las pruebas con sus propiedades aisladas; las pruebas de autenticación demo generan credenciales aleatorias. No introduzcas las contraseñas solicitadas en los tests.

5. Inicia desde la carpeta que contiene el `.env` correcto:

   ```bash
   java -jar target/silbom-backend-1.0.0.jar --spring.profiles.active=local-proxy
   ```

   Este perfil escucha en loopback y conserva el proxy HTTPS local existente. La aplicación no expone PostgreSQL. El arranque queda ocupando esa terminal; **Ctrl+C** detiene esa instancia iniciada directamente. Si vas a utilizar systemd, actualiza primero su `WorkingDirectory` y `ExecStart` para que apunten al repositorio/JAR nuevos, conservando su configuración privada; reiniciar un servicio que apunta al proyecto Hito 2 seguirá ejecutando el backend anterior.

   No se cambia automáticamente la unidad systemd ni Caddy porque esas configuraciones están en tu PC. El arranque CLI permite verificar esta rama antes de sustituir el servicio.

## Comprobar identidades y permisos

Primero prueba desde el PC mediante loopback, sin escribir contraseñas en comandos; `curl --user nombre` las solicita de forma interactiva:

```bash
curl --fail --user supervisor -H 'X-Requested-With: XMLHttpRequest' http://127.0.0.1:8080/api/v1/sesion
curl --fail --user tecnico -H 'X-Requested-With: XMLHttpRequest' http://127.0.0.1:8080/api/v1/sesion
```

El primer resultado debe tener `rol: SUPERVISOR`, el segundo `rol: TECNICO`, y ambos `modoDosCuentas: true`, `identidadesSoloLectura: true`. La respuesta no incluye contraseña ni hash y tiene `Cache-Control: no-store`.

Una contraseña incorrecta, un username inexistente, una cuenta inactiva o una tercera cuenta existente deben recibir 401. La consulta `/api/v1/tecnicos` devuelve 403 a un técnico y 200 al supervisor. Para comprobar el bloqueo de altas sin enviar datos válidos de una nueva identidad:

```bash
curl --user supervisor -H 'X-Requested-With: XMLHttpRequest' -H 'Content-Type: application/json' -X POST --data '{}' --write-out '\nHTTP %{http_code}\n' http://127.0.0.1:8080/api/v1/tecnicos
```

Con la demo activa debe responder 403 antes de validar el cuerpo. No uses credenciales reales en una conexión HTTP desde otro dispositivo; para Android/iPhone y la LAN utiliza el HTTPS ya configurado y un certificado confiable. Si mantienes la misma IP y Caddy de las pruebas anteriores, verifica `https://192.168.50.242:8443`; si la IP cambió, ajusta el proxy/certificado y la URL configurada en la app.

Para revisar cuentas directamente en PostgreSQL, ejecuta como administrador autorizado y en la planta correcta una consulta **sin mostrar hashes**:

```sql
SELECT username, nombre, rol, activo, planta_id,
       password_hash ~ '^\$2[aby]\$' AS usa_bcrypt
FROM tecnicos
WHERE planta_id = 'PLANTA-SAN-JOAQUIN'
  AND username IN ('supervisor', 'tecnico');
```

Deben existir dos filas diferentes, con los roles/nombres adecuados, activas y `usa_bcrypt = true`. La aplicación valida la coincidencia del secreto mediante BCrypt; la consulta anterior solo comprueba su formato. No publiques el contenido de `password_hash`.

## Interfaces, sesión y NFC Android

- Consola supervisora: `/` o `/index.html`. Interfaz técnica: `/app/`. Tras autenticar, un enlace indica la interfaz del rol verificado por `/api/v1/sesion`; no se infiere un rol a partir de un error 403.
- No hay redirecciones que transfieran credenciales. Cambiar de vista solicita iniciar sesión de nuevo; la URL solo puede llevar el identificador de máquina.
- La gestión de identidades queda deshabilitada en demo y para técnicos. El backend la deniega aunque se llame directamente al endpoint o al servicio.
- El cierre de un ticket exige su propietario, también frente al supervisor. Un segundo ticket mantiene Multi-LOTO. El historial no se borra.
- Un 401, el cierre de sesión o `pagehide` eliminan la credencial y los datos privados de la memoria de la página. Una solicitud incierta conserva únicamente el intento operativo para que su responsable pueda verificarlo al volver a autenticar; no se reenvía sola. Durante una escritura en curso se exige esperar su resultado antes de cambiar de sesión.
- No se guardan contraseñas en localStorage, sessionStorage, Cache Storage o assets APK. El service worker solo conserva el shell estático; el endpoint de sesión y la API no se cachean.
- Se conservan `MainActivity`, el puente NFC y `NfcTextDecoder`; solo se sincronizan los assets web que usa Android. No se añaden credenciales al APK.
- Un APK instalado antes de estos cambios puede llevar un HTML anterior: recompílalo con el SDK existente mediante `bash android-app/build-apk.sh` e instala ese artefacto después de revisión. No se afirma haber construido ni probado un nuevo APK en un teléfono durante este trabajo.
- NFC identifica una máquina; nunca inicia o libera automáticamente un bloqueo. Se conserva la selección manual y los enlaces QR/PWA.

Resultados de la revisión: [VERIFICACION_DOS_CUENTAS.md](VERIFICACION_DOS_CUENTAS.md).

## Pruebas y vuelta al modo normal

```bash
mvn verify
python3 -m unittest discover -s tests/configuracion -v
python3 -m unittest discover -s tests/browser -v
bash tests/android-nfc/run-tests.sh
```

Las pruebas de navegador requieren Playwright y su motor; las NFC requieren Node.js y JDK. El script `scripts/test-postgres.sh`, usado por CI, exige un PostgreSQL de pruebas y crea/borrar bases efímeras; **no dirigirlo a producción**. Verifica RLS/concurrencia y ejecuta la autenticación de dos cuentas en otra base, con contraseñas aleatorias de prueba.

Para regresar al funcionamiento normal, detén el backend, cambia localmente `SILBOM_DEMO_TWO_USERS_ONLY=false` y reinicia. Se restablecen la autenticación y los permisos administrativos normales de las cuentas activas; no se borran las identidades demo ni sus historiales. El cambio no representa una liberación física ni autoriza reenergizar maquinaria.
