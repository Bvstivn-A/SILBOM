/* Visualización local. No tiene transporte HTTP, credenciales ni operaciones LOTO. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const config = window.SilbomPlanData;
  const positions = config.positions;
  const format = new Intl.NumberFormat('es-CL', {maximumFractionDigits: 1});
  const nodes = new Map();
  const ICONS = {
    reset:'M3 10a9 9 0 1 1 2 8M3 4v6h6', plan:'M3 3h18v18H3zM3 10h11V3m0 7v11m0-6h7',
    plus:'M12 5v14M5 12h14', minus:'M5 12h14', fit:'M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M8 8h8v8H8z',
    left:'m14 6-6 6 6 6', right:'m10 6 6 6-6 6', up:'m6 14 6-6 6 6', down:'m6 10 6 6 6-6',
    database:'M20 6c0 2-4 4-8 4S4 8 4 6s4-4 8-4 8 2 8 4Zm0 0v12c0 2-4 4-8 4s-8-2-8-4V6m0 6c0 2 4 4 8 4s8-2 8-4',
    location:'M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Zm-8-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
    file:'M14 2H5v20h14V7l-5-5Zm0 0v5h5M8 12h8m-8 4h8',
    simulation:'M7 3h10M9 3v6L3 19a2 2 0 0 0 2 3h14a2 2 0 0 0 2-3L15 9V3M7 15h10',
    shield:'m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6l9-4Zm0 5v6m0 4h.01',
    close:'m6 6 12 12M6 18 18 6', lock:'M5 10h14v11H5zM8 10V6a4 4 0 0 1 8 0v4m-4 5v2',
    free:'M9 12h6M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
    unknown:'M9.5 8a2.5 2.5 0 0 1 5 .5c0 2-2.5 2-2.5 4m0 4h.01M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0'
  };
  function icon(name) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 24 24'); svg.setAttribute('class','icon');
    svg.setAttribute('aria-hidden','true'); svg.setAttribute('focusable','false');
    const path = document.createElementNS(svg.namespaceURI,'path'); path.setAttribute('d',ICONS[name]); svg.append(path); return svg;
  }
  document.querySelectorAll('[data-icon]').forEach(node => node.replaceChildren(icon(node.dataset.icon)));
  // Solo dibujo propio estático: ningún dato del catálogo se interpola en markup.
  $('blueprint-layer').innerHTML = window.SilbomBlueprint.markup;
  let rows = [], view = [], selected = 'EQ-ENV-01', scenario = 'available', sourceVerified = true;
  let tooltipId = null, sheetTrigger = null, drag = null;
  const camera = {zoom:1, x:0, y:0};
  const clamp = (value,min,max) => Math.min(max,Math.max(min,value));
  const current = () => view.find(item => item.id === selected);
  const announce = message => { $('feedback').textContent = message; };
  function state(item) { return !item.verified ? 'unknown' : item.bloqueosActivos > 0 ? 'locked' : 'free'; }
  function stateText(item) {
    if (!item.verified) return scenario === 'stale' ? 'Información desactualizada' : 'Estado sin verificar';
    const n = item.bloqueosActivos;
    return n === 0 ? 'Sin bloqueos digitales' : `${format.format(n)} bloqueo${n === 1 ? '' : 's'} LOTO activo${n === 1 ? '' : 's'}`;
  }
  function countText(item) { return item.verified ? format.format(item.bloqueosActivos) : 'Sin verificar'; }
  function mtbfText(item) { return !item.verified ? 'Sin verificar' : item.mtbf === null ? 'No calculable' : `${format.format(item.mtbf)} h`; }
  function renderPill(element,item) {
    element.dataset.state = state(item);
    const text = document.createElement('span'); text.textContent = stateText(item);
    element.replaceChildren(icon(state(item) === 'locked' ? 'lock' : state(item)),text);
  }
  function normalizeMachines(input, verified) {
    const list = Array.isArray(input) ? input : [];
    const ids = new Set(list.map(item => item?.id));
    const complete = list.length === positions.length && ids.size === positions.length && positions.every(p => ids.has(p.id));
    return positions.map(fallback => {
      const row = list.find(item => item?.id === fallback.id) || {};
      const validState = Number.isInteger(row.bloqueosActivos) && row.bloqueosActivos >= 0 && row.bloqueosActivos <= 2147483647
        && typeof row.bloqueada === 'boolean' && row.bloqueada === (row.bloqueosActivos > 0);
      const validText = typeof row.nombre === 'string' && row.nombre.trim() && typeof row.area === 'string' && row.area.trim();
      return {id:fallback.id,
        nombre:typeof row.nombre === 'string' && row.nombre.trim() ? row.nombre.trim() : fallback.nombre,
        area:typeof row.area === 'string' && row.area.trim() ? row.area.trim() : fallback.area,
        bloqueada:validState ? row.bloqueada : null, bloqueosActivos:validState ? row.bloqueosActivos : null,
        mtbf:typeof row.mtbf === 'number' && Number.isFinite(row.mtbf) && row.mtbf >= 0 ? row.mtbf : null,
        verified:Boolean(verified && complete && validState && validText)};
    });
  }
  function renderSummary() {
    const unknown = view.filter(item => !item.verified).length;
    $('stat-total').textContent = format.format(view.length);
    const values = {
      'stat-locked':view.filter(item => item.bloqueosActivos > 0).length,
      'stat-free':view.filter(item => item.bloqueosActivos === 0).length,
      'stat-locks':view.reduce((sum,item) => sum + (item.bloqueosActivos ?? 0),0)
    };
    for (const [key,value] of Object.entries(values)) {
      $(key).textContent = unknown ? '—' : format.format(value);
      $(key).setAttribute('aria-label',unknown ? 'Sin confirmar: hay datos sin verificar' : format.format(value));
    }
    $('availability-text').textContent = unknown
      ? `${unknown} equipo(s) sin verificar en esta demostración. «—» no significa cero bloqueos.`
      : 'Datos simulados en memoria; no se consulta la API.';
  }
  function renderDetail() {
    const item = current();
    $('detail-body').hidden = !item; $('empty-detail').hidden = Boolean(item);
    $('clear-selection').disabled = !item;
    $('machine-picker').value = selected || '';
    for (const button of document.querySelectorAll('[data-demo-count]')) {
      button.disabled = !item?.verified;
      button.setAttribute('aria-pressed',String(Boolean(item?.verified && item.bloqueosActivos === Number(button.dataset.demoCount))));
    }
    $('demo-help').textContent = !item ? 'Selecciona un equipo para mostrar sus escenarios ficticios.'
      : item.verified ? 'Disponible únicamente en este prototipo.' : 'Elige «Datos demo disponibles» para cambiar el escenario local.';
    document.querySelectorAll('[data-zone]').forEach(node => node.classList.toggle('zone-selected',Boolean(item && node.dataset.zone === positions.find(p => p.id === item.id).zone)));
    if (!item) return;
    $('detail-code').textContent = item.id; $('detail-name').textContent = item.nombre; $('detail-area').textContent = item.area;
    $('detail-count').textContent = countText(item); $('detail-mtbf').textContent = mtbfText(item);
    renderPill($('detail-state'),item);
  }
  // Única entrada visual para un arreglo externo. No contiene transporte ni autenticación.
  function renderMachines(input,{verified=true}={}) {
    rows = Array.isArray(input) ? input.map(item => item && typeof item === 'object' ? {...item} : item) : [];
    sourceVerified = Boolean(verified);
    view = normalizeMachines(rows,sourceVerified && scenario === 'available');
    for (const item of view) {
      const {button,disc,option} = nodes.get(item.id);
      button.dataset.state = state(item);
      button.setAttribute('aria-pressed',String(item.id === selected));
      button.setAttribute('aria-label',`${item.id}, ${item.nombre}. ${item.area}. ${stateText(item)}. Bloqueos activos: ${countText(item)}. Datos simulados.`);
      disc.textContent = !item.verified ? '?' : item.bloqueosActivos > 0 ? format.format(item.bloqueosActivos) : '−';
      disc.classList.toggle('large-count',item.verified && item.bloqueosActivos > 99);
      option.textContent = `${item.id} · ${item.nombre}`;
    }
    hideTooltip(); renderSummary(); renderDetail(); if ($('sheet').open) renderSheet();
  }
  function machineHash() { try { return decodeURIComponent(location.hash.slice(1)); } catch { return ''; } }
  function setHash() { try { const url = new URL(location.href); url.hash = selected || ''; history.pushState(null,'',url); } catch { /* file:// puede restringir History sin impedir usar el plano. */ } }
  function selectMachine(id,{center=false,updateUrl=true}={}) {
    if (!positions.some(item => item.id === id)) return;
    selected = id;
    for (const [key,node] of nodes) node.button.setAttribute('aria-pressed',String(key === id));
    hideTooltip(); renderDetail(); if (center && camera.zoom > 1) centerOn(id);
    if (updateUrl) setHash();
    announce(`${current().nombre} seleccionada. ${stateText(current())}. Datos simulados; no se ejecutó ninguna operación.`);
  }
  function clearSelection(updateUrl=true) {
    selected = null;
    for (const node of nodes.values()) node.button.setAttribute('aria-pressed','false');
    hideTooltip(); renderDetail(); if (updateUrl) setHash();
    announce('Selección quitada. Elige un punto del plano o un equipo de la lista.');
  }
  function applyDemoCount(count) {
    const item = current();
    if (!item?.verified || ![0,1,2].includes(count)) return;
    const next = rows.map(row => row.id === item.id ? {...row,bloqueada:count > 0,bloqueosActivos:count} : row);
    renderMachines(next);
    announce(`Escenario local: ${item.id}, ${stateText(current())}. Solo cambiaron datos simulados; no se creó ni liberó un bloqueo real.`);
  }
  function resetDemo() {
    hideTooltip();
    if ($('sheet').open) $('sheet').close();
    selected = 'EQ-ENV-01'; scenario = 'available'; $('scenario').value = scenario;
    renderMachines(config.initialMachines()); fit(); setHash();
    announce(`Escenario inicial restablecido: ${$('stat-total').textContent} equipos, ${$('stat-locked').textContent} con registros y ${$('stat-locks').textContent} bloqueos digitales simulados.`);
  }
  function renderSheet() {
    const item = current(); if (!item) return;
    $('sheet-code').textContent = item.id; $('sheet-name').textContent = item.nombre; $('sheet-area').textContent = item.area;
    $('sheet-count').textContent = countText(item); $('sheet-mtbf').textContent = mtbfText(item); renderPill($('sheet-state'),item);
  }
  function hideTooltip() {
    if (tooltipId) nodes.get(tooltipId).button.removeAttribute('aria-describedby');
    tooltipId = null; $('machine-tooltip').hidden = true;
  }
  function showTooltip(id) {
    const item = view.find(row => row.id === id); if (!item || drag) return;
    hideTooltip(); tooltipId = id;
    $('tip-code').textContent = id; $('tip-name').textContent = item.nombre; $('tip-area').textContent = item.area;
    $('tip-state').textContent = stateText(item); $('tip-count').textContent = `Bloqueos activos: ${countText(item)}`;
    const tooltip = $('machine-tooltip'); tooltip.hidden = false; tooltip.style.maxHeight='';
    const rect = nodes.get(id).button.getBoundingClientRect(), parent = $('plan-viewport').getBoundingClientRect();
    const width = tooltip.offsetWidth;
    const above=rect.top-parent.top-16, below=parent.bottom-rect.bottom-16;
    const placeAbove=above >= tooltip.offsetHeight || above >= below;
    tooltip.style.maxHeight=`${Math.max(32,placeAbove ? above : below)}px`;
    const height=tooltip.offsetHeight, x=rect.left-parent.left+rect.width/2;
    const y=placeAbove ? rect.top-parent.top-height-8 : rect.bottom-parent.top+8;
    tooltip.style.left=`${clamp(x-width/2,8,Math.max(8,parent.width-width-8))}px`;
    tooltip.style.top=`${clamp(y,8,Math.max(8,parent.height-height-8))}px`;
    nodes.get(id).button.setAttribute('aria-describedby','machine-tooltip');
  }
  function updateCamera() {
    camera.x = clamp(camera.x,1-camera.zoom,0); camera.y = clamp(camera.y,1-camera.zoom,0);
    $('plan-viewport').scrollLeft=0; $('plan-viewport').scrollTop=0;
    $('scene').style.transform = `translate(${camera.x*100}%,${camera.y*100}%) scale(${camera.zoom})`;
    $('zoom-level').textContent = `${format.format(camera.zoom*100)} %`;
    $('zoom-out').disabled = camera.zoom <= 1; $('zoom-in').disabled = camera.zoom >= 2.5;
    $('plan-viewport').dataset.zoomed = String(camera.zoom > 1);
    $('pan-controls').hidden = camera.zoom === 1;
    hideTooltip();
  }
  function centerOn(id) {
    const p = positions.find(item => item.id === id); if (!p) return;
    camera.x = .5-p.x/config.width*camera.zoom; camera.y = .5-p.y/config.height*camera.zoom; updateCamera();
  }
  function zoomTo(value) {
    const next = clamp(value,1,2.5), p = positions.find(item => item.id === selected);
    const anchorX = p ? p.x/config.width : (.5-camera.x)/camera.zoom;
    const anchorY = p ? p.y/config.height : (.5-camera.y)/camera.zoom;
    camera.zoom = next; camera.x = .5-anchorX*next; camera.y = .5-anchorY*next; updateCamera();
    announce(`Plano ampliado al ${format.format(next*100)} %. Usa las flechas para desplazarte o «Ajustar» para volver a la vista completa.`);
  }
  function fit() { camera.zoom=1; camera.x=0; camera.y=0; updateCamera(); }
  function ensureVisible(id) {
    if (camera.zoom === 1) return;
    const rect = nodes.get(id).button.getBoundingClientRect(), parent = $('plan-viewport').getBoundingClientRect();
    if (rect.left < parent.left+8 || rect.right > parent.right-8 || rect.top < parent.top+8 || rect.bottom > parent.bottom-35) centerOn(id);
  }
  function buildMarkers() {
    const placeholder = document.createElement('option'); placeholder.value=''; placeholder.textContent='Selecciona un equipo'; $('machine-picker').append(placeholder);
    for (const p of positions) {
      const button = document.createElement('button'); button.type='button'; button.className='machine-marker'; button.id='point-'+p.id;
      button.dataset.machineId=p.id; button.style.left=`${p.x/config.width*100}%`; button.style.top=`${p.y/config.height*100}%`;
      const disc = document.createElement('span'); disc.className='marker-disc'; disc.setAttribute('aria-hidden','true');
      const label = document.createElement('span'); label.className='marker-label'; label.textContent=p.id; label.setAttribute('translate','no'); label.setAttribute('aria-hidden','true');
      button.append(disc,label); $('markers').append(button);
      const option = document.createElement('option'); option.value=p.id; $('machine-picker').append(option);
      nodes.set(p.id,{button,disc,option});
      button.addEventListener('click',() => selectMachine(p.id));
      button.addEventListener('pointerenter',event => { if (event.pointerType !== 'touch') showTooltip(p.id); });
      button.addEventListener('pointerleave',event => { if (!$('machine-tooltip').contains(event.relatedTarget) && document.activeElement !== button) hideTooltip(); });
      button.addEventListener('focus',() => { ensureVisible(p.id); showTooltip(p.id); });
      button.addEventListener('blur',() => hideTooltip());
    }
  }
  buildMarkers();
  $('machine-tooltip').addEventListener('pointerleave',event => {
    if (tooltipId && event.relatedTarget !== nodes.get(tooltipId).button && document.activeElement !== nodes.get(tooltipId).button) hideTooltip();
  });
  document.addEventListener('keydown',event => { if (event.key === 'Escape') hideTooltip(); });
  $('machine-picker').addEventListener('change',event => event.target.value ? selectMachine(event.target.value,{center:true}) : clearSelection());
  $('clear-selection').addEventListener('click',() => { clearSelection(); $('machine-picker').focus(); });
  document.querySelectorAll('[data-demo-count]').forEach(button => button.addEventListener('click',() => applyDemoCount(Number(button.dataset.demoCount))));
  $('reset-demo').addEventListener('click',resetDemo);
  $('scenario').addEventListener('change',event => {
    scenario=event.target.value; renderMachines(rows,{verified:sourceVerified});
    announce(scenario === 'available' ? 'Datos demo locales disponibles. No se consultó la API.'
      : scenario === 'stale' ? 'Información desactualizada en la demostración. Estados y contadores sin verificar.'
      : 'Servidor desconectado en la demostración. Estados grises, sin confirmar ningún bloqueo.');
  });
  $('zoom-in').addEventListener('click',() => zoomTo(camera.zoom+.5));
  $('zoom-out').addEventListener('click',() => zoomTo(camera.zoom-.5));
  $('fit-plan').addEventListener('click',() => { fit(); announce('Plano completo ajustado a pantalla.'); });
  document.querySelectorAll('[data-pan]').forEach(button => button.addEventListener('click',() => {
    const direction=button.dataset.pan;
    camera.x += direction === 'left' ? .18 : direction === 'right' ? -.18 : 0;
    camera.y += direction === 'up' ? .18 : direction === 'down' ? -.18 : 0;
    updateCamera();
  }));
  $('plan-viewport').addEventListener('pointerdown',event => {
    if (camera.zoom === 1 || event.button !== 0 || event.target.closest('button,.machine-tooltip')) return;
    // Se preserva el scroll vertical/pinch nativo en pantallas táctiles; las flechas ofrecen desplazamiento accesible.
    if (event.pointerType === 'touch') return;
    const rect=$('plan-viewport').getBoundingClientRect();
    drag={id:event.pointerId,x:event.clientX,y:event.clientY,cameraX:camera.x,cameraY:camera.y,width:rect.width,height:rect.height};
    $('plan-viewport').setPointerCapture(event.pointerId); $('plan-viewport').classList.add('dragging'); hideTooltip(); event.preventDefault();
  });
  $('plan-viewport').addEventListener('pointermove',event => {
    if (!drag || drag.id !== event.pointerId) return;
    camera.x=drag.cameraX+(event.clientX-drag.x)/drag.width; camera.y=drag.cameraY+(event.clientY-drag.y)/drag.height; updateCamera();
  });
  const endDrag=() => { drag=null; $('plan-viewport').classList.remove('dragging'); };
  $('plan-viewport').addEventListener('pointerup',endDrag);
  $('plan-viewport').addEventListener('pointercancel',endDrag);
  $('plan-viewport').addEventListener('lostpointercapture',endDrag);
  $('open-sheet').addEventListener('click',() => { if (!current()) return; sheetTrigger=document.activeElement; hideTooltip(); renderSheet(); $('sheet').showModal(); });
  $('close-sheet').addEventListener('click',() => $('sheet').close());
  $('back-to-plan').addEventListener('click',() => $('sheet').close());
  $('sheet').addEventListener('close',() => { if (sheetTrigger?.isConnected && sheetTrigger.getClientRects().length) sheetTrigger.focus(); });
  $('sheet').addEventListener('keydown',event => {
    if (event.key !== 'Tab') return;
    const controls=[...$('sheet').querySelectorAll('button:not(:disabled)')];
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1).focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0].focus(); }
  });
  window.addEventListener('popstate',() => {
    const id=machineHash();
    if (positions.some(p => p.id === id)) selectMachine(id,{center:true,updateUrl:false});
    else if (!id) clearSelection(false);
  });
  if (positions.some(p => p.id === machineHash())) selected=machineHash();
  renderMachines(config.initialMachines()); updateCamera();
  announce(`${current().nombre} seleccionada. ${stateText(current())}. PROTOTIPO: datos simulados.`);
  window.SilbomIndustrialPlan=Object.freeze({
    renderMachines,
    snapshot:() => JSON.parse(JSON.stringify({machines:view,selected,scenario,camera}))
  });
})();
