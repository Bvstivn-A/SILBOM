# Verificación del acceso de demostración

Fecha: 19 de noviembre de 2026. Base revisada: `1846e0800399babb75f3fad3a9cef5b626f03d47`, PR #4, rama `feature/two-account-demo-access` de `Bvstivn-A/Silbom`. El repositorio anterior `Silbom_Pruebas` y su prototipo independiente no se modifican en este trabajo.

## Diagnóstico de la implementación preliminar

Ya existían: opt-in por entorno, usernames permitidos en UserDetailsService, BCrypt, bloqueo de altas/edición de usuarios y creación/configuración de dos identidades durante el arranque.

Se corrigieron o completaron:

1. `TecnicoService.eliminar` no aplicaba la prohibición de cambios del modo demo.
2. La comprobación de tickets antes de activar solo recorría técnicos activos: podía omitir responsables inactivos y legados. Ahora una consulta sobre los tickets de la planta exige un responsable activo permitido.
3. La autenticación no comprobaba que cada username permitido conservara el rol esperado. Ahora se valida tanto en Spring Security como al obtener el actor en servicios.
4. Las interfaces deducían el rol por éxito/403 al consultar `/tecnicos`, ignorando fallos de comunicación. Ahora usan `/api/v1/sesion`, validan su respuesta y no crean una sesión con rol desconocido.
5. Se añadió navegación explícita por rol y deshabilitación de gestión de identidades según la sesión verificada. El backend mantiene controles propios.
6. Se eliminan credenciales/datos privados al cerrar sesión, recibir 401 o salir de la página. Un intento LOTO incierto se conserva sin reenvío y sin la credencial, para verificarlo al volver a autenticar.
7. El configurador local conserva PostgreSQL/clave AES y secretos previos; solicita las contraseñas mediante entrada oculta, comprueba Git y reemplaza atómicamente el archivo con permisos 0600.

## Resultados

| Suite | Resultado |
|---|---|
| Java / Spring, H2, JDK 21 | 66 pruebas; cero fallos y errores |
| PostgreSQL 17: integridad, concurrencia y RLS | 8 pruebas; cero fallos y errores |
| Autenticación demo en otra base PostgreSQL 17 | 14 pruebas; cero fallos y errores |
| Navegador Chromium: frontend real con API controlada | 27 pruebas; cero fallos y errores |
| Configurador local Python | 8 pruebas; cero fallos y errores |
| NFC: módulo JavaScript | 3 pruebas; cero fallos |
| Decodificador NDEF Java | Programa de comprobación correcto, UTF-8/UTF-16, idiomas, vacío e inválidos |
| Copias web, docs y Android | `scripts/sync-web-assets.py --check` correcto |
| Secretos solicitados en archivos del repositorio | Ausentes; no se imprimieron sus valores |

Las pruebas Java generan credenciales efímeras para esta demostración de autenticación; no utilizan las contraseñas reales solicitadas. PostgreSQL se ejecutó en un contenedor de pruebas accesible solo en loopback, con dos bases separadas, esquema repetido y rol de aplicación no propietario/sin superusuario. No se usó la base del computador Fedora.

La suite de 14 casos comprueba ambos logins válidos/roles, contraseñas incorrectas, identidad inexistente, tercera cuenta con hash válido, cuenta desactivada, rol alterado, técnico sin permisos administrativos, supervisor autorizado sobre máquinas/lecturas, identidad inmutable en demo, cierre propio/Multi-LOTO, bloqueo de activación para responsables excluidos/inactivos/legados y reinicio sin cambio de IDs/hashes/historial.

Los tests normales fijan el modo demo desactivado para no depender de un `.env` usado para desplegar. La suite específica lo activa con propiedades dinámicas y contraseñas aleatorias. El configurador se prueba únicamente en repositorios y archivos temporales, incluyendo repetición, fichero versionado, symlink, duplicados y errores de entrada.

Las pruebas de navegador conservan las de pérdidas de conexión, timeout, respuesta incompleta, reintentos idempotentes, Multi-LOTO, URL de máquina, instalación PWA y restauración iOS. Añaden rol verificado, fallo de sesión, formularios demo deshabilitados, sesión revocada y salida con operación incierta. Al recibir 401 ahora se exige volver a autenticar antes de otro intento.

## Seguridad y límites

- No se modificaron esquema, tickets reales ni identidades históricas. El arranque transaccional falla antes de habilitar una demo que dejaría tickets sin responsable autorizado.
- Las únicas contraseñas reales deben estar en el entorno o `.env` privado del servidor. No se escribieron en Java, HTML/JavaScript, SQL, tests ni APK.
- No se implementó un nuevo sistema de sesiones/cookies: continúa HTTP Basic explícito y stateless, sobre HTTPS fuera de loopback. El endpoint de identidad no devuelve un token, contraseña o hash.
- No se cambió el lector NFC Java ni su puente. Se actualizaron sus assets web; no se construyó un APK nuevo ni se ensayó una etiqueta física/Android real.
- Chromium es la ejecución local del navegador. La matriz de CI también contempla WebKit; no se presenta un resultado local de WebKit inexistente.
- No se accedió al `.env`, systemd, Caddy o PostgreSQL del PC Fedora. No se afirma que las cuentas estén activadas allí.
- La activación local exige revisar el historial de bloqueos, usar el JAR de esta rama y conservar el HTTPS de acceso móvil. Ver [procedimiento local](DEMO_DOS_CUENTAS.md).
- El modo debe mantenerse en una única instancia controlada durante la demo; detener instancias antiguas antes de activarlo. No cambia una flota de servidores remotos ni sustituye el procedimiento físico LOTO.
