# Mapa esquemático de planta · Prototipo SILBOM

Propuesta visual para evaluar con el equipo antes de decidir su incorporación al Hito 3. Rama: `prototype/mapa-planta`. Base revisada: `main` en `cb8693e365d897fb529087d20fb38aa1250cd7d2` (22 de noviembre de 2026). No requiere backend, PostgreSQL ni credenciales.

## Abrir la demostración

1. Descarga esta rama o cambia a ella en tu copia del repositorio.
2. Abre **`docs/prototipos/mapa-planta.html`** con doble clic, o arrastra ese archivo al navegador.
3. Selecciona cualquier máquina, consulta «Ver ficha completa» y prueba «Simular bloqueo».
4. Prueba «Desconexión simulada» y «Datos desactualizados» en el selector de escenarios.
5. Usa «Mapa completo» para quitar la selección y «Restablecer demostración» para recuperar los datos iniciales.

El HTML contiene CSS, JavaScript, dibujos SVG y favicon; no necesita internet, Node, npm ni un servidor. Los cambios se pierden al recargar. No guarda datos en cookies ni almacenamiento local. El fragmento de URL `#EQ-COM-03` permite compartir una selección de demostración sin ejecutar acciones.

Si tu navegador o visor de archivos restringe la apertura directa, desde la raíz del repositorio puedes usar:

```bash
python3 -m http.server 8091 --bind 127.0.0.1 --directory docs/prototipos
```

Abre <http://127.0.0.1:8091/mapa-planta.html>. Detén ese servidor con `Ctrl+C`. Es un servidor local para visualizar el prototipo; no inicia SILBOM ni habilita acceso desde otros equipos.

## Qué incluye

- Perímetro y seis zonas con un pasillo principal en escritorio y tablet; distribución ficticia, sin dimensiones ni ubicaciones reales. En teléfonos pequeños se reorganiza en dos columnas y se omite el pasillo transversal para conservar legibilidad.
- Seis máquinas con símbolos propios en SVG, identificación, nombre, estado digital y contador.
- Selección por clic, toque, Tab + Enter o Espacio, con foco visible y sin recargar la página.
- Panel lateral en escritorio (más de 1200 px) e inferior en notebook y tablet.
- Ficha modal local con área, estado, cantidad de registros y MTBF ilustrativo. Cierre con botón o Escape y retorno del foco.
- Simulación de un registro local adicional, Multi-LOTO y restablecimiento.
- Cuatro indicadores derivados del arreglo de máquinas: total del catálogo, equipos con registros, equipos sin registros y suma de registros activos.
- Estados grises para información sin verificar o desactualizada. Los indicadores operacionales muestran «—», nunca un cero inferido; la simulación se deshabilita para el equipo sin verificar.
- Etiquetas, íconos y texto además del color, anuncio de cambios, controles de al menos 44 × 44 CSS px y respeto por `prefers-reduced-motion`.

**Rojo:** uno o más registros digitales. **Verde:** ningún bloqueo digital registrado. **Gris:** información sin verificar. Ninguno de estos estados demuestra aislamiento físico, energía cero o autorización para intervenir. El MTBF es una media ilustrativa; no predice la próxima falla ni certifica seguridad.

Todos los estados, contadores y MTBF son **DEMO**. Los nombres y áreas se contrastaron con `src/main/java/cl/silbom/backend/config/DataInitializer.java`:

| ID | Nombre del catálogo | Área | Registros iniciales DEMO |
| --- | --- | --- | ---: |
| EQ-COM-03 | Compresor de Tornillo | Sala de Máquinas | 0 |
| EQ-MEZ-01 | Mezclador Industrial de Cinta | Área de Preparación | 0 |
| EQ-EXT-02 | Extrusora de Polímeros | Área de Moldeo | 0 |
| EQ-PR-04 | Prensa Hidráulica 200T | Área de Estampado | 1 |
| EQ-ENV-01 | Envasadora Rotativa Automática | Línea de Envasado 1 | 2 |
| EQ-TR-01 | Cinta Transportadora Principal | Logística y Despacho | 0 |

El resumen inicial calculado es 6 máquinas, 2 con registros, 4 sin registros y 3 registros activos. La cinta transportadora ilustra un MTBF no calculable.

## Revisión del diseño actual

Se revisó la consola canónica `src/main/resources/static/index.html`: cabecera oscura, tarjetas de maquinaria, indicadores superiores, paneles con bordes redondeados, tipografía del sistema y estados de bloqueo. Sus colores incluyen cian `#0CB7F2`, fondo grafito `#252A2E`, tarjetas `#343C42`, verde `#66DDB0` y rojo `#FF7379`.

La propuesta conserva el cian, la tipografía del sistema, el lenguaje de tarjetas, los radios y las indicaciones por texto e ícono. Adapta las superficies a azul oscuro y aclara el rojo para el contraste del mapa. CSS y SVG quedan aislados en el HTML; no se copian estilos al dashboard ni se cambia su navegación. No se añaden fuentes remotas ni bibliotecas.

Se aplicaron UI/UX Pro Max para la planificación, Frontend Design para la implementación y Web Design Guidelines para la revisión. Las recomendaciones genéricas de landing pages no sustituyen la identidad ni los requisitos de SILBOM.

## Aislamiento y comportamiento de la demostración

No hay `fetch`, XHR, WebSocket, formularios enviados ni service worker. La política CSP declara `connect-src 'none'` y `form-action 'none'`, bloqueando comunicaciones de scripts y envíos de formularios. Los únicos SVG generados como HTML provienen de geometría estática propia; nombres, áreas y estados se insertan mediante `textContent`.

La opción «Desconexión simulada» representa cómo se vería información no disponible. No detecta el estado del backend ni mide conectividad real. Incluso sin conexión real, «Simular bloqueo» sigue siendo una acción exclusivamente local, con aviso explícito. Nunca confirma una operación LOTO ni informa un cambio en PostgreSQL.

No se cambian dashboard oficial, backend, base de datos, autenticación, Android, NFC, QR ni reglas LOTO. La comprobación de los 132 archivos originales está en `evidencias-mapa/aislamiento.json`. Solo se agregan archivos bajo `docs/prototipos/`.

## Integración futura: propuesta para revisar, todavía no implementada

El contrato actual se verificó en `src/main/java/cl/silbom/backend/dto/MaquinaResponseDTO.java` y el controlador de máquinas. `GET /api/v1/maquinas` devuelve un arreglo cuyos campos relevantes son:

| Campo | Tipo Java actual | Uso visual |
| --- | --- | --- |
| `id` | `String` | Asociar el equipo a una posición conocida |
| `nombre` | `String` | Nombre visible |
| `area` | `String` | Panel de información |
| `bloqueada` | `Boolean` | Consistencia con el contador |
| `bloqueosActivos` | `Integer` | Conteo Multi-LOTO y resúmenes |
| `mtbf` | `Double` | Horas, solo si el valor es finito y no negativo |

También existen `icono`, `horasOperativas`, `fallasCorrectivas` y `plantaId`; no se modifican endpoints ni DTO. Los valores nulos o inconsistentes no deben convertirse en ceros.

El renderizador está disponible como:

```javascript
window.SilbomPlantMap.renderMachines(arregloDeMaquinas, { verified: true });
window.SilbomPlantMap.renderMachines(arregloDeMaquinas, { verified: false });
window.SilbomPlantMap.snapshot(); // Copia de datos y selección, para inspección/pruebas.
```

La función recibe datos sin saber cómo se obtuvieron. El plano de este prototipo está definido para los seis IDs del catálogo: arreglos incompletos, duplicados o con IDs inesperados dejan el plano sin verificar. Contador/booleano contradictorios o datos obligatorios inválidos dejan ese equipo gris y los totales operacionales sin confirmar. MTBF ausente, negativo o no finito se muestra «No calculable». Reordenar el arreglo no cambia las posiciones. No es todavía un editor genérico de plantas.

Para una integración aprobada, extraer el componente visual al frontend existente, reemplazar el origen DEMO por un adaptador de lectura con ruta relativa `/api/v1/maquinas`, conservar autenticación y autorización vigentes y usar HTTPS con el mismo origen. Mantener fecha de última respuesta válida y pasar `verified: false` ante errores, sesión vencida o datos caducados. Cambiar la CSP solo tras revisar ese adaptador. Retirar los botones, datos y manejadores de simulación del componente productivo. La ficha podría abrir el detalle existente mediante selección de ID, sin iniciar ni liberar bloqueos. Este prototipo no contiene ese adaptador ni enlaces a acciones reales.

## Pruebas y evidencias

Verificación con Chromium automatizado: **15 pruebas, 14 aprobadas, 1 omitida por política del navegador**, sin errores ni fallos. La apertura `file://` está bloqueada por el navegador administrado de este entorno (`ERR_BLOCKED_BY_ADMINISTRATOR`); no se afirma que esa prueba haya pasado. La ejecución e interacción se comprobaron mediante servidor HTTP local. Pendiente: probar doble clic en un navegador personal y realizar una revisión manual con lector de pantalla y en dispositivos reales; no se declara certificación WCAG ni pruebas realizadas en Safari.

La suite cubre catálogo, selección, teclado, hover, foco, ficha, Multi-LOTO, resúmenes, restablecimiento, escenarios grises, datos incompletos/duplicados/inconsistentes, MTBF, texto no confiable, pérdida real de red después de cargar, selección por URL y ausencia de llamadas externas o de escritura. Revisa anchos 375, 390, 768, 834, 1024, 1280, 1440 y 1920 px; panel lateral/inferior, blancos de pulsación, movimiento reducido y texto ampliado al doble por CSS. La ampliación CSS no sustituye las pruebas de accesibilidad de cada sistema operativo.

Para repetir las pruebas, en un entorno con **Python 3, Playwright para Python y Chromium**:

```bash
python3 docs/prototipos/verificar-mapa.py
```

El script inicia y detiene su propio servidor en `127.0.0.1` con puerto efímero. Si Chromium no está en `PATH`, puedes indicar su ejecutable con `SILBOM_TEST_CHROMIUM`; en su ausencia usa el navegador instalado de Playwright. Estas dependencias son solo para pruebas, no para abrir el HTML. No se instala nada al ejecutar el script.

Evidencias:

- [Escritorio, 1440 px](evidencias-mapa/mapa-escritorio-1440.png)
- [Tablet, 1024 px](evidencias-mapa/mapa-tablet-1024.png)
- [Teléfono, 390 px](evidencias-mapa/mapa-movil-390.png)
- [Información sin verificar](evidencias-mapa/mapa-sin-verificar.png)
- [Ficha local](evidencias-mapa/mapa-ficha-local.png)
- [Resultados y dimensiones](evidencias-mapa/verificacion.json), con SHA-256 del HTML probado.
- [Contraste calculado](evidencias-mapa/contraste.json): combinaciones principales de texto ≥4,5:1; contornos de controles y foco ≥3:1. Es una comprobación parcial de pares de colores, no una auditoría completa de todos los estados.
- [Aislamiento de archivos originales](evidencias-mapa/aislamiento.json).

Revisión de Web Design Guidelines sobre `mapa-planta.html`: controles nativos y etiquetados, foco visible, salto al contenido, estados expresados con texto e ícono, actualizaciones anunciadas, Escape y retorno de foco en el diálogo, movimiento reducido, zoom permitido y ausencia de dependencias externas. No se encontraron bloqueantes en este alcance. El tema oscuro es el único tema solicitado y probado.

## Archivos nuevos

- `mapa-planta.html`: prototipo autónomo.
- `README-mapa-planta.md`: instrucciones, alcance e integración propuesta.
- `verificar-mapa.py`: verificaciones reproducibles.
- `evidencias-mapa/`: cinco capturas PNG y tres informes JSON.

La rama y su Pull Request son para revisión del equipo. No se fusionan automáticamente con `main`.
