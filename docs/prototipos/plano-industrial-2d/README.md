# Plano industrial 2D · Prototipo SILBOM

Propuesta arquitectónica navegable para revisión del equipo. Rama **`prototype/plano-industrial-2d`**, creada desde `main` en `cb8693e365d897fb529087d20fb38aa1250cd7d2`. Es independiente del prototipo anterior `prototype/mapa-planta`; no lo reemplaza ni integra funciones en producción.

**PROTOTIPO — DATOS SIMULADOS.** El edificio, las posiciones y los valores de estado/MTBF son ficticios. No es un plano certificado, no tiene escala ni dimensiones reales y no describe rutas de evacuación.

## Cómo abrirlo

Descarga o cambia a esta rama y conserva todos los archivos de la carpeta juntos. Abre `docs/prototipos/plano-industrial-2d/index.html` en un navegador. HTML, CSS y JavaScript son locales, sin módulos, fuentes externas, paquetes npm ni peticiones para cargar el dibujo. No necesitas iniciar Spring Boot, PostgreSQL ni la aplicación Android.

Si el navegador o visor restringe los archivos locales, desde la raíz del repositorio ejecuta:

```bash
python3 -m http.server 8091 --bind 127.0.0.1 --directory docs/prototipos/plano-industrial-2d
```

Abre <http://127.0.0.1:8091/>. Para detener este servidor de archivos, pulsa **Ctrl+C** en esa terminal. No es el servicio del backend y no lo reemplaza. La dirección `127.0.0.1` solo sirve para el computador donde ejecutas el comando.

La apertura directa está diseñada sin dependencias de servidor; **no pudo verificarse aquí** porque Chromium administrado bloquea `file://` con `ERR_BLOCKED_BY_ADMINISTRATOR`. Las pruebas interactivas se ejecutaron con servidor local. Pendiente: comprobar doble clic en el navegador personal y una revisión en dispositivos físicos.

## Qué incluye

- Edificio vectorial SVG de contorno irregular, muros exteriores dobles, divisiones interiores, puertas con arcos de apertura y accesos ilustrativos.
- Sala de máquinas, preparación, moldeo, nave de producción, taller de mantenimiento, bodega y despacho, conectados por pasillos.
- Seis símbolos de maquinaria y puntos circulares interactivos. No se representa la planta mediante una tabla de tarjetas.
- Tooltip con nombre, ID, área, estado digital y cantidad de registros; también accesible al enfocar con teclado y descartable con Escape.
- Panel con información del equipo y ficha modal local, sin navegar a operaciones reales.
- Selección con clic, toque, Tab + Enter/Espacio o lista «Ir a un equipo». Seleccionar no cambia los contadores.
- Zoom entre 100 % y 250 %, ajuste a pantalla y desplazamiento con mouse o botones de flechas. Al navegar con teclado, el punto enfocado vuelve al área visible. En pantallas táctiles se conserva el scroll y zoom nativos del navegador; usa las flechas del plano para desplazar su vista ampliada.
- Panel lateral por encima de 1280 px; debajo del plano en notebook y tablet. El SVG conserva sus proporciones. En teléfonos, los detalles del dibujo requieren acercamiento; los IDs y controles mantienen su tamaño legible.
- Cuatro indicadores calculados a partir del arreglo renderizado: equipos del catálogo, con registros, sin registros y suma de bloqueos digitales activos.

El color se acompaña de símbolo y texto:

| Estado | Punto | Significado |
| --- | --- | --- |
| Verde | `−` | SILBOM no registra bloqueos digitales activos |
| Rojo | Número de registros | Uno o varios bloqueos digitales activos |
| Gris | `?` | Información desconocida, desactualizada o no verificada |

El verde **no certifica seguridad física, energía, disponibilidad ni permiso para arrancar**. El MTBF mostrado es ilustrativo, no una predicción de falla ni una medida de aislamiento físico. Los nombres de salas no identifican un edificio real.

## Demostración de estados

1. Selecciona un equipo que inicialmente esté verde.
2. En el panel **Escenarios de demostración**, pulsa «1 · Un registro» para verlo rojo.
3. Pulsa «2 · Multi-LOTO»: el punto, tooltip, ficha, panel y totales reflejan dos registros.
4. Pulsa «0 · Sin registros» para devolverlo al estado digital verde.
5. Cambia «Escenario» a «Servidor desconectado (demo)» o «Información desactualizada». Los puntos quedan grises, los indicadores operacionales muestran «—» y los controles de datos locales se deshabilitan.
6. Recupera «Datos demo disponibles» y usa «Restablecer escenario» para volver al inicio, incluida la selección y el zoom.

Estos botones fijan una cantidad **local** para la presentación; no crean o liberan bloqueos reales. Los cambios se pierden al recargar. No hay cookies, almacenamiento persistente, credenciales, tokens ni service worker.

El selector de desconexión es una simulación manual; no realiza una comprobación real del backend ni detecta conectividad. Si se corta internet después de cargar, los controles de demostración siguen cambiando solo datos ficticios. Ningún mensaje confirma una operación LOTO real.

## Catálogo y origen de los datos

Nombres y áreas contrastados con `src/main/java/cl/silbom/backend/config/DataInitializer.java`. Estados, MTBF y coordenadas son de demostración:

| ID | Nombre | Área del catálogo | Registros iniciales |
| --- | --- | --- | ---: |
| EQ-COM-03 | Compresor de Tornillo | Sala de Máquinas | 0 |
| EQ-MEZ-01 | Mezclador Industrial de Cinta | Área de Preparación | 0 |
| EQ-EXT-02 | Extrusora de Polímeros | Área de Moldeo | 0 |
| EQ-PR-04 | Prensa Hidráulica 200T | Área de Estampado | 1 |
| EQ-ENV-01 | Envasadora Rotativa Automática | Línea de Envasado 1 | 2 |
| EQ-TR-01 | Cinta Transportadora Principal | Logística y Despacho | 0 |

El resumen inicial es **6 / 2 / 4 / 3**, calculado, no mantenido como contadores independientes. La cinta transportadora ejemplifica MTBF ausente («No calculable»). El fragmento `#EQ-COM-03` permite abrir una selección de demostración sin ejecutar acciones.

## Archivos y diseño

| Archivo | Responsabilidad |
| --- | --- |
| `index.html` | Estructura semántica, controles, panel y ficha |
| `styles.css` | Tema, blueprint, responsive y estados de interacción |
| `plano.js` | Geometría SVG propia y estática del edificio y sus elementos |
| `datos-demo.js` | Catálogo, posiciones gráficas ficticias y datos iniciales |
| `script.js` | Render, selección, tooltip, cámara y controles locales |
| `verificar-plano.py` | Pruebas de navegador reproducibles |
| `evidencias/` | Siete capturas y tres informes JSON |

La consola actual `src/main/resources/static/index.html` usa tipografía del sistema, cian `#0CB7F2`, fondos grafito `#252A2E`/`#22272B`, tarjetas `#343C42` y estados verde `#66DDB0` y rojo `#FF7379`. Su estructura combina indicadores y tarjetas de máquinas.

Este prototipo conserva tipografía, cian, estados con texto/íconos y lenguaje de paneles. Adapta las superficies al azul técnico `#101D2A`/`#182C3B`, muros claros y rojo más luminoso `#FF8D93` para legibilidad. El centro visual es el edificio SVG, con un solo panel contextual. No copia ni altera estilos de producción.

Se utilizaron UI/UX Pro Max para planificar la interacción, Frontend Design para el diseño e implementación y Web Design Guidelines para la revisión. Las sugerencias genéricas de landing pages y fuentes externas se descartaron por no corresponder a esta consola industrial autónoma.

## Integración posterior con la API

El backend, a través de sus servicios existentes, es quien accede a PostgreSQL. **El navegador no debe conectarse directamente a PostgreSQL.**

Se verificó `MaquinaResponseDTO.java`: `GET /api/v1/maquinas` devuelve un arreglo con `id`, `nombre`, `area` (`String`), `bloqueada` (`Boolean`), `bloqueosActivos` (`Integer`) y `mtbf` (`Double`, puede ser nulo). También existen `icono`, `horasOperativas`, `fallasCorrectivas` y `plantaId`; no se requieren cambios al contrato.

El renderizador recibe datos independientemente de su origen:

```javascript
window.SilbomIndustrialPlan.renderMachines(arregloDeMaquinas, { verified: true });
window.SilbomIndustrialPlan.renderMachines(arregloDeMaquinas, { verified: false });
window.SilbomIndustrialPlan.snapshot(); // Copia para inspección, sin modificar el estado interno.
```

La validación conserva la regla del dashboard: contador entero no negativo y `bloqueada === (bloqueosActivos > 0)`. El contador admite el rango de `Integer` del DTO. Datos inconsistentes o campos obligatorios inválidos dejan al equipo gris. Arreglos incompletos, duplicados o IDs desconocidos dejan el plano completo sin verificar, porque la disposición está definida para estos seis equipos. Los totales operacionales dejan de mostrarse si algún estado está sin confirmar. MTBF nulo, negativo, textual o no finito no se trata como válido; cero numérico sí es válido.

Una futura integración aprobada podría:

1. Extraer el componente visual al dashboard y conservar las posiciones ficticias en una configuración separada. Cambiar las posiciones solo tras acordar un plano con el equipo; los números actuales son coordenadas del SVG, no distancias.
2. Reutilizar `loadMachinesFromApi()` y el estado `AppState.machinesConfirmed` de la consola. Esa función ya usa el wrapper autenticado `apiFetch('/maquinas')`. El adaptador visual convertiría `name → nombre`, `isLocked → bloqueada` y `activeLocks → bloqueosActivos`, conservando `id`, `area` y `mtbf`; no necesita otro endpoint ni otra solicitud paralela.
3. Usar rutas relativas bajo el mismo origen HTTPS, respetando sesión, autorización y planta del usuario. El identificador solo seleccionaría el equipo; no contendría credenciales.
4. Pasar `verified: false` ante errores, sesión vencida o información caducada. No interpretar una respuesta fallida ni caché antigua como cero bloqueos. Registrar la antigüedad de la última lectura válida al integrar.
5. Retirar datos y controles de demostración antes de publicar; conectar «Ver ficha completa» con el detalle existente, sin activar LOTO al seleccionar un punto.
6. Revisar la CSP del componente integrado: en esta demo `connect-src 'none'` impide toda conexión de scripts. No desactivarla a ciegas ni añadir acceso directo a base de datos.

No existe todavía ese adaptador ni conexión real en estos archivos.

## Verificación y límites

Pruebas Chromium: **15 casos, 14 aprobados, 1 omitido por la política `file://` del navegador administrado**. Sin errores JavaScript ni errores de consola/CSP. Se prueba mediante servidor local; no se declara apertura directa verificada ni pruebas en Safari o dispositivos físicos.

La suite verifica catálogo, seis posiciones, estados, selección sin mutación, tooltip con teclado/Escape, cambios 0/1/2, Multi-LOTO, restablecimiento, ficha y retorno de foco, zoom, arrastre y alternativa por botones, coordenadas proporcionales, ausencia de superposición de IDs, datos inválidos/duplicados/incompletos, estado no confirmado conservado al cambiar de escenario, MTBF, texto no confiable y pérdida de red después de cargar. Solo se permiten peticiones GET a los cinco archivos estáticos esperados: ninguna llamada a la API, ni POST, PUT, PATCH o DELETE.

Responsive: **375, 390, 768, 834, 1024, 1280, 1440, 1600 y 1920 px**, sin desplazamiento horizontal de la página y con controles de al menos 44 × 44 CSS px. También se comprueban movimiento reducido y ampliación de texto por CSS al doble en 768 px. Esta última comprobación no sustituye Dynamic Type ni las opciones de accesibilidad de cada sistema operativo.

Para repetir las pruebas, necesitas Python 3, Playwright para Python y Chromium ya instalados:

```bash
python3 docs/prototipos/plano-industrial-2d/verificar-plano.py
```

El script inicia y detiene su propio servidor local con puerto efímero. Usa Chromium en `PATH`, permite indicar `SILBOM_TEST_CHROMIUM` o utiliza el navegador instalado de Playwright. No instala paquetes ni modifica configuraciones del sistema. Estas dependencias son solo para las pruebas, no para abrir el prototipo.

Evidencias:

- [Escritorio 1600 px](evidencias/escritorio-1600.png), [tablet 1024 px](evidencias/tablet-1024.png) y [teléfono 390 px](evidencias/movil-390.png).
- [Tooltip](evidencias/tooltip.png), [estado sin verificar](evidencias/sin-verificar.png), [zoom 150 %](evidencias/zoom-150.png) y [ficha local](evidencias/ficha-local.png).
- [Resultados y geometría de controles](evidencias/verificacion.json), con SHA-256 de los cinco archivos probados.
- [Contrastes de pares principales](evidencias/contraste.json): texto ≥4,5:1; contornos y foco ≥3:1. Comprobación parcial del tema oscuro, no certificación WCAG.
- [Integridad de los archivos originales](evidencias/aislamiento.json).

Revisión Web Design Guidelines: controles nativos etiquetados, foco visible, tooltip descartable sin cubrir el punto enfocado, salto al contenido, estados con texto y símbolo, anuncio de cambios, cierre por Escape/retorno de foco en la ficha, alternativa al arrastre, movimiento reducido y zoom del navegador habilitado. Pendientes manuales: lectura con lector de pantalla, navegadores personales y dispositivos reales. Solo se solicita y prueba tema oscuro.

No se modifican dashboard, backend, PostgreSQL, Android, NFC, QR, autenticación ni reglas LOTO. Los **132 archivos originales** permanecen intactos. La rama y el Pull Request son para revisión; **no se fusionan automáticamente**.
