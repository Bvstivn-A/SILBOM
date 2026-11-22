/* Catálogo contrastado con DataInitializer. Coordenadas, estados y MTBF ficticios.
 * Script clásico para funcionar también con apertura directa file://, sin imports/fetch. */
(() => {
  'use strict';
  const positions = [
    { id: 'EQ-COM-03', x: 235, y: 260, zone: 'sala-maquinas', nombre: 'Compresor de Tornillo', area: 'Sala de Máquinas', mtbf: 718.5, count: 0 },
    { id: 'EQ-MEZ-01', x: 510, y: 260, zone: 'preparacion', nombre: 'Mezclador Industrial de Cinta', area: 'Área de Preparación', mtbf: 715, count: 0 },
    { id: 'EQ-EXT-02', x: 790, y: 260, zone: 'moldeo', nombre: 'Extrusora de Polímeros', area: 'Área de Moldeo', mtbf: 171.3, count: 0 },
    { id: 'EQ-PR-04', x: 285, y: 592, zone: 'produccion', nombre: 'Prensa Hidráulica 200T', area: 'Área de Estampado', mtbf: 356, count: 1 },
    { id: 'EQ-ENV-01', x: 600, y: 592, zone: 'produccion', nombre: 'Envasadora Rotativa Automática', area: 'Línea de Envasado 1', mtbf: 233.8, count: 2 },
    { id: 'EQ-TR-01', x: 1050, y: 680, zone: 'bodega', nombre: 'Cinta Transportadora Principal', area: 'Logística y Despacho', mtbf: null, count: 0 }
  ].map(item => Object.freeze(item));
  window.SilbomPlanData = Object.freeze({
    width: 1280, height: 880,
    positions: Object.freeze(positions),
    initialMachines: () => positions.map(({id, nombre, area, mtbf, count}) =>
      ({id, nombre, area, mtbf, bloqueada: count > 0, bloqueosActivos: count}))
  });
})();
