# SILBOM Android — Lector QR nativo (junto a NFC)

Versión de la app: **1.2.2 (versionCode 5)** · paquete `cl.silbom.tecnico`

El técnico puede identificar una máquina de tres formas equivalentes:

| Método | Qué lee | Resultado |
|---|---|---|
| 📡 Escanear NFC | Registro NDEF Text `EQ-COM-03` | Ficha de la máquina confirmada por la API |
| 📷 Escanear QR | QR cuyo texto es solo `EQ-COM-03` | Ficha de la máquina confirmada por la API |
| Selección manual | Lista del catálogo confirmado | Ficha de la máquina |

Identificar una máquina **no** crea, libera ni modifica bloqueos LOTO.

## 1. Tecnología elegida: ZXing core 3.5.3 + actividad de cámara propia

Se evaluó primero **Google Code Scanner** (`play-services-code-scanner`), como pedía el requerimiento. Se descartó porque:

- SILBOM Android **no usa Gradle**: se compila con `android-app/build-apk.sh` (aapt2 + javac + d8).
  Code Scanner se distribuye como varios AAR (Play Services base/basement/tasks, ML Kit,
  AndroidX) con recursos y manifiestos que Gradle fusiona automáticamente. Hacerlo a mano en
  el script, o migrar el proyecto a Gradle, era un cambio grande y arriesgado para la entrega.
- Requiere Google Play Services y **descargar el módulo de escaneo** en el teléfono la primera
  vez (necesita Internet de Google). En la red de la demo eso puede fallar.
- ML Kit "con modelo incluido" tiene el mismo problema de AAR/Gradle y además bibliotecas nativas.

**ZXing core** (Apache 2.0) es un único `.jar` en Java puro, sin recursos ni manifiesto:
basta con añadirlo al `javac -cp` y a `d8`. Funciona sin Play Services, sin Internet y en
Android 7–14 (minSdk 24 del proyecto). La interfaz de cámara es una actividad pequeña
(`QrScannerActivity`) dentro de la misma APK, así que no se abre Chrome ni otra app.

- El lector está limitado a `BarcodeFormat.QR_CODE`.
- El `.jar` **no se sube a Git**: `build-apk.sh` lo descarga de Maven Central y verifica su
  SHA-256 (`8d8064c1…09fd82`). Si no coincide, la compilación se detiene.
- Costo: la app pide el permiso `CAMERA` en tiempo de ejecución (la primera vez que se pulsa
  *Escanear QR*). La cámara está declarada como **opcional**: sin cámara, NFC y la selección
  manual siguen funcionando.

## 2. Cómo funciona

```
Botón «📷 Escanear QR» (WebView)
  └─ window.SilbomAndroidQr.startScan()                 (puente Java)
       └─ QrScannerActivity: cámara trasera + ZXing (solo QR_CODE)
            └─ devuelve el texto leído a MainActivity
                 └─ MachineCode.rejectionReason(texto)  (validación Java compartida)
                      ├─ inválido / URL / vacío → window.SilbomQr.onError(motivo)
                      └─ válido → window.SilbomQr.onRead("EQ-COM-03")
                           └─ identifyMachineByCode(código, 'QR')   (misma función que NFC)
                                ├─ valida otra vez el formato
                                ├─ bloquea si hay una operación LOTO pendiente
                                ├─ GET /api/v1/maquinas/EQ-COM-03 al servidor configurado
                                ├─ 404 → «Máquina no registrada en SILBOM.»
                                ├─ 401/403 → «No autorizado para consultar esta máquina.»
                                ├─ sin red → «No se pudo conectar con el servidor.»
                                └─ 200 + catálogo confirmado → abre la ficha (paso 2)
```

### Relación NFC ↔ QR

Ambos lectores terminan en la **misma** función JavaScript `identifyMachineByCode(code, source)`
y en la misma regla Java `MachineCode` (`^EQ-[A-Z]{2,4}-[0-9]{2}$`). La lectura NFC física
(`ReaderCallback`, NDEF Text, `NfcTextDecoder`) **no cambió**; solo su validación final usa ahora
`MachineCode.isValid`, que tiene la misma expresión regular que antes.

Protecciones conservadas: un escaneo a la vez, lecturas duplicadas ignoradas, sin escaneo
mientras haya una operación LOTO sin confirmar, y no se abre ninguna ficha sin confirmación del
servidor (no se usan datos simulados).

### Seguridad

- El QR **solo identifica** la máquina. No es credencial ni autorización: puede copiarse.
- La dirección del servidor sale de la configuración de la app (*Configurar servidor*), **nunca del QR**.
- Si el QR contiene `https://…`, `http://192.168.1.50:8080`, `www.…`, una IP, `javascript:`,
  `intent:` u otro esquema, se rechaza como «enlace o dirección» y **no se abre**. El contenido
  rechazado ni siquiera se envía a la WebView.
- Crear o liberar bloqueos sigue exigiendo sesión y las reglas existentes (propiedad del ticket,
  Multi-LOTO). Backend, base de datos, autenticación y roles no se modificaron.

## 3. Uso del escáner (técnico)

1. Abrir **SILBOM Técnico** → pestaña **Operar** → paso **Identificar**.
2. Pulsar **📷 Escanear QR**. La primera vez Android pide permiso de cámara → **Permitir**.
3. Mensaje: «Apunta la cámara al código QR de la máquina». Encuadrar el QR (15–30 cm).
4. Al reconocerlo: «Código detectado: EQ-COM-03. Verificando máquina con SILBOM…».
5. Si el servidor confirma: «Máquina encontrada: EQ-COM-03 · Compresor de Tornillo» y se abre la ficha.
6. Si falla después de leer, el mensaje lo indica: «QR leído: EQ-COM-03. No se pudo conectar con el servidor.».
7. Continuar la intervención LOTO como siempre.

Para salir sin escanear: botón **Cancelar y volver a SILBOM** o la tecla Atrás.
Si se negó el permiso: *Ajustes → Aplicaciones → SILBOM Técnico → Permisos → Cámara*.

## 4. Configurar el servidor

La app solo acepta **HTTPS**, o **HTTP en `localhost`** (regla de seguridad previa de SILBOM,
para no enviar credenciales sin cifrar por el Wi-Fi). Una dirección `http://192.168.x.x:8080`
se rechaza con «Usa HTTPS para conectar desde el teléfono». Usar `https://…:8080` tampoco
funciona: Spring Boot atiende HTTP en el 8080.

**Opción A: por cable USB (la más simple para probar y para la demo)**

```bash
java -jar target/silbom-backend-1.0.0.jar            # backend en el computador
adb reverse tcp:8080 tcp:8080                        # el localhost:8080 del teléfono = el del PC
```

En la app: **⚙️ Servidor** → `http://localhost:8080` → *Guardar IP y Probar Conexión*.
Funciona mientras el cable esté conectado. Hay que repetir `adb reverse` si se reconecta el teléfono.

**Opción B: por Wi-Fi con HTTPS (Caddy)**

```bash
sudo apt install caddy && sudo systemctl disable --now caddy    # una vez; sin servicio en :80
java -jar target/silbom-backend-1.0.0.jar --spring.profiles.active=local-proxy   # solo 127.0.0.1
SILBOM_TEST_HOST=<ip-del-pc> caddy run --config deploy/Caddyfile.local --adapter caddyfile
```

Caddy recibe HTTPS en `8443` con su propia CA (`tls internal`) y reenvía a `127.0.0.1:8080`.
El `Caddyfile` no abre el puerto 80 ni instala la CA en el computador.

En el teléfono, **una sola vez**:
1. Copiar la CA **pública** (nunca `root.key`):
   `adb push ~/.local/share/caddy/pki/authorities/local/root.crt /sdcard/Download/SILBOM-Caddy-CA.crt`
2. *Ajustes → Seguridad y privacidad → Más ajustes de seguridad → Instalar desde el almacenamiento
   del dispositivo → Certificado de CA* → **Instalar de todas formas** → elegir `SILBOM-Caddy-CA.crt`.
   (Android exige tener un bloqueo de pantalla.)
3. En SILBOM: **⚙️ Servidor** → `https://<ip-del-pc>:8443` → *Guardar IP y Probar Conexión*.

Desde la versión 1.2.2 la APK confía en las CA instaladas por el usuario
(`res/xml/network_security_config.xml`); sin ese archivo Android 7+ las ignora. Es aceptable para
la APK de demostración. En producción convendría un certificado público o fijar solo la CA propia.
Si cambia la IP del computador (otra red), hay que ejecutar Caddy con la nueva IP; la CA es la misma
y no hay que reinstalarla.

## 5. Etiquetas QR

Imprimibles en `docs/qr/` (contenido codificado = **solo** el identificador):

| Archivo | Contenido QR | Máquina |
|---|---|---|
| `docs/qr/QR-EQ-COM-03.png` | `EQ-COM-03` | Compresor de Tornillo |
| `docs/qr/QR-EQ-ENV-01.png` | `EQ-ENV-01` | Envasadora Rotativa Automática |
| `docs/qr/QR-EQ-EXT-02.png` | `EQ-EXT-02` | Extrusora de Polímeros |

Imprimir al 100 % (sin "ajustar a página" que deforme), QR de al menos 4 cm de lado, en papel
mate para evitar reflejos.

### Generar nuevas etiquetas

```bash
bash android-app/build-apk.sh          # descarga ZXing en android-app/libs/ (una vez)
java -Djava.awt.headless=true -cp android-app/libs/zxing-core-3.5.3.jar \
  scripts/qr/GenerarEtiquetasQr.java docs/qr EQ-MOL-04 "Moledora Industrial"
```

El generador rechaza códigos que no cumplan el formato SILBOM. La máquina debe existir en
PostgreSQL para que la app abra su ficha.

### Verificar etiquetas

```bash
bash tests/android-nfc/run-tests.sh                  # decodifica con ZXing (mismo lector de la app)
python3 scripts/qr/verificar_qr_zbar.py docs/qr      # decodificador independiente (libzbar0 + Pillow)
```

## 6. Compilar la APK

Requisitos: JDK 17+, Android SDK con `platforms;android-34` y **`build-tools;35.0.0`**
(con build-tools 34 el d8 incluido falla incluso en `main`), `curl`, `zip`.

```bash
export ANDROID_SDK_ROOT=$HOME/Android/Sdk       # o la ruta de tu SDK
# Para que la APK se instale como ACTUALIZACIÓN de la v0.9.x, firmar con el MISMO keystore debug:
export SILBOM_DEBUG_KEYSTORE=/ruta/fuera/del/repo/debug.keystore
bash android-app/build-apk.sh
# Resultado: android-app/build/silbom-tecnico.apk
```

`ANDROID_BUILD_TOOLS_VERSION` permite elegir otra versión de build-tools si fuera necesario.
El keystore **nunca** se sube a Git (`*.keystore` está en `.gitignore`). Si se firma con otra
clave, Android rechazará la actualización: habrá que desinstalar la versión anterior.

Instalación por cable: `adb install -r SILBOM-Android-NFC-QR-debug.apk`.

## 7. Pruebas realizadas

Automáticas (ejecutadas en el computador de desarrollo):

| Prueba | Resultado |
|---|---|
| `node --test` helpers JS (`nfc-code.test.js`) | 3/3 OK |
| `NfcTextDecoderTest` (NFC sin cambios) | OK |
| `MachineCodeTest`: válidos `EQ-COM-03`, `EQ-ENV-01`, `EQ-EXT-02`; inválidos `HOLA`, `EQ-ENV`, vacío, minúsculas, caracteres invisibles, JSON; URL `https://google.com`, `http://192.168.1.50:8080`, `javascript:`, `intent:` | 59 verificaciones OK |
| Etiquetas PNG decodificadas con ZXing (opciones de la app) | 3/3 exactas |
| Etiquetas PNG decodificadas con **zbar** (independiente) | 3/3 exactas, 9 bytes, sin URL |
| `sync-web-assets.py --check` y `tests/configuracion` | OK |
| Compilación Java + d8 + firma `apksigner verify` | OK |
| Firma APK = firma de v0.9.1-beta (SHA-256 `8df6955c…1a8d`) | Coincide: instala como actualización |

Nuevas pruebas de navegador en `tests/browser/test_mobile.py` (Playwright, se ejecutan en el CI
*Backend y PWA* con Chromium y WebKit): QR válido abre la ficha sin escrituras; lecturas
duplicadas consultan una sola vez; 404 / 401 / 403 / servidor caído no abren ficha; contenidos
inválidos y URL no generan peticiones; errores nativos (cancelado, permiso, cámara, lector)
permiten reintentar; sin puente Android se explica y la selección manual sigue; QR bloqueado con
operación pendiente; **NFC sigue identificando por el flujo común**; tras identificar por QR se
puede crear un bloqueo con sesión.

### Pendiente de validación física

No había un teléfono conectado por ADB durante el desarrollo. **La lectura QR con la cámara real
está pendiente de validación física.** Lista para el Android de la demo:

1. Instalar la APK sobre la versión anterior (debe actualizar sin desinstalar).
2. Verificar que **NFC** sigue leyendo `EQ-COM-03`.
3. Escanear los tres QR impresos → se abre Compresor de Tornillo / Envasadora Rotativa Automática / Extrusora de Polímeros.
4. QR con `https://google.com` → «contiene un enlace…; no se abrió nada».
5. Cancelar el escáner → vuelve a SILBOM sin reiniciar.
6. Negar permiso de cámara → mensaje con instrucciones; NFC y selección manual siguen.
7. Apagar el backend y escanear → «No se pudo conectar con el servidor.», sin ficha.
8. Iniciar sesión, crear y liberar un bloqueo, revisar Historial y Multi-LOTO.

## 8. Limitaciones conocidas

- Usa la API `android.hardware.Camera` (obsoleta pero soportada en Android 7–14); se eligió por
  ser mucho más simple que Camera2 y no requerir AndroidX. La pantalla del escáner es solo vertical.
- La cámara frontal se usa solo si el equipo no tiene cámara trasera.
- QR muy pequeños, arrugados o con reflejos pueden tardar en leerse; sin linterna integrada.
- Un QR (como un NFC) puede copiarse: identifica, no autoriza. La autorización la hace el backend.
- Las pruebas de navegador no se pudieron ejecutar localmente (Playwright no está instalado en el
  equipo de desarrollo); se ejecutan en GitHub Actions.
