/* Apartado de lectura del supervisor. No conoce credenciales ni realiza peticiones HTTP. */
(() => {
  'use strict';
  const cssUrl = new URL('./plan.css', document.currentScript.src).href;
  const POSITIONS = Object.freeze([
    {id:'EQ-COM-03',x:235,y:260,zone:'sala-maquinas'},
    {id:'EQ-MEZ-01',x:510,y:260,zone:'preparacion'},
    {id:'EQ-EXT-02',x:790,y:260,zone:'moldeo'},
    {id:'EQ-PR-04',x:285,y:592,zone:'produccion'},
    {id:'EQ-ENV-01',x:600,y:592,zone:'produccion'},
    {id:'EQ-TR-01',x:1050,y:680,zone:'bodega'}
  ].map(Object.freeze));
  const ICONS = {
    plus:'M12 5v14M5 12h14',minus:'M5 12h14',fit:'M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M8 8h8v8H8z',
    left:'m14 6-6 6 6 6',right:'m10 6 6 6-6 6',up:'m6 14 6-6 6 6',down:'m6 10 6 6 6-6',
    refresh:'M3 10a9 9 0 1 1 2 8M3 4v6h6',location:'M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Zm-8-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
    file:'M14 2H5v20h14V7l-5-5Zm0 0v5h5M8 12h8m-8 4h8',lock:'M5 10h14v11H5zM8 10V6a4 4 0 0 1 8 0v4m-4 5v2',
    free:'M9 12h6M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',unknown:'M9.5 8a2.5 2.5 0 0 1 5 .5c0 2-2.5 2-2.5 4m0 4h.01M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
    plan:'M3 3h18v18H3zM3 10h11V3m0 7v11m0-6h7'
  };
  function icon(name) {
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('class','icon');svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');
    const path=document.createElementNS(svg.namespaceURI,'path');path.setAttribute('d',ICONS[name]||ICONS.unknown);svg.append(path);return svg;
  }
  const MARKUP = `
  <main>
    <section class="page-heading"><div><h1>Plano de planta</h1><p>Ubica un equipo y consulta sus registros digitales de bloqueo.</p></div><button id="refresh" type="button" class="button"><span data-icon="refresh"></span>Actualizar datos</button></section>
    <section class="summary" aria-label="Resumen de las posiciones del plano"><div><span>Posiciones del plano</span><strong id="stat-total">—</strong></div><div><span><i class="dot locked" aria-hidden="true"></i>Con registros digitales</span><strong id="stat-locked">—</strong></div><div><span><i class="dot free" aria-hidden="true"></i>Sin registros de bloqueo</span><strong id="stat-free">—</strong></div><div><span>Bloqueos digitales activos</span><strong id="stat-locks">—</strong></div></section>
    <div class="workbench">
      <section class="plan-section" aria-labelledby="plan-heading"><div class="plan-topline"><div><h2 id="plan-heading">Distribución de la instalación</h2><p>Distribución ilustrativa · Sin escala · Sin certificación</p></div></div>
        <div class="drawing-shell"><div class="drawing-toolbar"><span class="drawing-label"><span data-icon="plan"></span>Plano esquemático de supervisión</span><div class="zoom-controls" role="group" aria-label="Ampliación del plano"><button id="zoom-out" class="icon-button" type="button" aria-label="Alejar plano"><span data-icon="minus"></span></button><output id="zoom-level" aria-label="Nivel de ampliación" aria-live="polite">100 %</output><button id="zoom-in" class="icon-button" type="button" aria-label="Acercar plano"><span data-icon="plus"></span></button><button id="fit-plan" class="button fit-button" type="button"><span data-icon="fit"></span>Ajustar</button></div></div>
          <div id="plan-viewport" class="plan-viewport" aria-label="Plano. Selecciona un punto para consultar un equipo."><div id="scene" class="scene"><div id="blueprint-layer" class="blueprint-layer"></div><div id="markers" class="markers" role="group" aria-label="Máquinas del plano"></div></div><div id="machine-tooltip" class="machine-tooltip" role="tooltip" hidden><p id="tip-code" class="code" translate="no"></p><strong id="tip-name"></strong><p id="tip-area"></p><p id="tip-state"></p><p id="tip-count"></p></div></div>
          <div class="drawing-bottom"><span>Las puertas y posiciones son ilustrativas; no representan rutas de evacuación.</span><div id="pan-controls" class="pan-controls" role="group" aria-label="Desplazar el plano ampliado" hidden><button class="icon-button" type="button" data-pan="left" aria-label="Ver hacia la izquierda"><span data-icon="left"></span></button><button class="icon-button" type="button" data-pan="up" aria-label="Ver hacia arriba"><span data-icon="up"></span></button><button class="icon-button" type="button" data-pan="down" aria-label="Ver hacia abajo"><span data-icon="down"></span></button><button class="icon-button" type="button" data-pan="right" aria-label="Ver hacia la derecha"><span data-icon="right"></span></button></div></div>
        </div>
        <div class="legend" aria-label="Estados digitales"><span><i class="state-symbol locked" aria-hidden="true">+</i>Con registros de bloqueo</span><span><i class="state-symbol free" aria-hidden="true">−</i>Sin registros de bloqueo</span><span><i class="state-symbol unknown" aria-hidden="true">?</i>Sin verificar</span></div>
        <p id="availability" class="availability" role="status" aria-live="polite"></p><p class="refresh-note">Última lectura válida: <time id="verified-at">Sin verificar</time>. Actualización cada 10 segundos.</p><p id="unmapped" class="map-warning" hidden></p>
        <div class="machine-nav"><label for="machine-picker">Ir a un equipo</label><select id="machine-picker" name="machine-picker"></select><button id="clear-selection" class="button" type="button">Quitar selección</button></div><p class="map-help">Tab y Enter para seleccionar. Acerca el dibujo y arrastra el fondo con el mouse o usa las flechas de desplazamiento.</p>
      </section>
      <aside class="side-column"><section class="equipment-panel" aria-labelledby="detail-heading"><div class="section-heading"><h2 id="detail-heading">Equipo seleccionado</h2><span data-icon="location"></span></div><div id="empty-detail" class="empty-detail"><h3>Selecciona un equipo</h3><p>Consulta su registro digital y su análisis sin ejecutar operaciones LOTO.</p></div><div id="detail-body" class="detail-body" hidden><p id="detail-code" class="code" translate="no"></p><h3 id="detail-name"></h3><div id="detail-state" class="state-pill"></div><dl><div><dt>Área del catálogo</dt><dd id="detail-area"></dd></div><div><dt>Bloqueos activos</dt><dd id="detail-count"></dd></div><div><dt>MTBF</dt><dd id="detail-mtbf"></dd></div></dl><p class="detail-help">El registro digital no demuestra aislamiento físico ni autoriza una intervención.</p><button id="open-analysis" class="button button-primary" type="button"><span data-icon="file"></span>Ver análisis en el resumen</button></div></section></aside>
    </div><p id="feedback" class="feedback" role="status" aria-live="polite" aria-atomic="true">Selecciona un equipo.</p><footer><p>El verde solo indica ausencia de bloqueos digitales registrados. No significa que la máquina sea segura, esté energizada o pueda arrancar.</p></footer>
  </main>`;
  function create(host,{onSelect=()=>{},onOpen=()=>{},onRefresh=async()=>{}}={}) {
    const root=host.attachShadow({mode:'open'}),link=document.createElement('link');link.rel='stylesheet';link.href=cssUrl;
    root.append(link);const content=document.createElement('div');content.innerHTML=MARKUP;root.append(content);
    const $=id=>root.getElementById(id),nodes=new Map(),fmt=new Intl.NumberFormat('es-CL',{maximumFractionDigits:1});
    root.querySelectorAll('[data-icon]').forEach(node=>node.replaceChildren(icon(node.dataset.icon)));
    $('blueprint-layer').innerHTML=window.SilbomSupervisorBlueprint.markup;
    const camera={zoom:1,x:0,y:0};let view=[],selected=null,tooltipId=null,drag=null;
    const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
    const current=()=>view.find(row=>row.id===selected);
    const state=row=>!row.verified?'unknown':row.activeLocks>0?'locked':'free';
    function stateText(row){return !row.verified?'Estado sin verificar':row.activeLocks===0?'Sin bloqueos digitales':`${fmt.format(row.activeLocks)} bloqueo${row.activeLocks===1?'':'s'} LOTO activo${row.activeLocks===1?'':'s'}`;}
    const countText=row=>row.verified?fmt.format(row.activeLocks):'Sin verificar';
    const announce=text=>{$('feedback').textContent=text;};
    function hideTooltip(){if(tooltipId)nodes.get(tooltipId).button.removeAttribute('aria-describedby');tooltipId=null;$('machine-tooltip').hidden=true;}
    function detail(){
      const row=current();$('detail-body').hidden=!row;$('empty-detail').hidden=Boolean(row);$('clear-selection').disabled=!row;$('machine-picker').value=selected||'';
      root.querySelectorAll('[data-zone]').forEach(node=>node.classList.toggle('zone-selected',Boolean(row&&node.dataset.zone===POSITIONS.find(p=>p.id===row.id).zone)));
      if(!row)return;
      $('detail-code').textContent=row.id;$('detail-name').textContent=row.name||'Equipo sin información actual';$('detail-area').textContent=row.area||'Sin verificar';
      $('detail-count').textContent=countText(row);$('detail-mtbf').textContent=!row.verified?'Sin verificar':row.mtbf===null?'No calculable':`${fmt.format(row.mtbf)} h`;
      const text=document.createElement('span');text.textContent=stateText(row);$('detail-state').dataset.state=state(row);$('detail-state').replaceChildren(icon(state(row)==='locked'?'lock':state(row)),text);
      $('open-analysis').disabled=!row.present;
    }
    function render({machines=[],verified=false,selectedId=null,verifiedAt=0,theme='dark',reason='Información sin verificar'}={}) {
      host.dataset.theme=theme;
      const rows=Array.isArray(machines)?machines:[],ids=new Set(rows.map(row=>row?.id));
      const unique=ids.size===rows.length;
      view=POSITIONS.map(p=>{
        const row=rows.find(m=>m?.id===p.id);
        const valid=row&&typeof row.name==='string'&&row.name.trim()&&typeof row.area==='string'&&row.area.trim()
          &&Number.isInteger(row.activeLocks)&&row.activeLocks>=0&&row.activeLocks<=2147483647&&typeof row.isLocked==='boolean'&&row.isLocked===(row.activeLocks>0);
        return {id:p.id,present:Boolean(row),name:row?.name||'',area:row?.area||'',activeLocks:valid?row.activeLocks:null,
          mtbf:typeof row?.mtbf==='number'&&Number.isFinite(row.mtbf)&&row.mtbf>=0?row.mtbf:null,verified:Boolean(verified&&unique&&valid)};
      });
      selected=POSITIONS.some(p=>p.id===selectedId)?selectedId:null;
      for(const row of view){const {button,disc,option}=nodes.get(row.id);
        button.dataset.state=state(row);button.setAttribute('aria-pressed',String(row.id===selected));
        button.setAttribute('aria-label',`${row.id}, ${row.name||'Sin información actual'}. ${row.area||'Área sin verificar'}. ${stateText(row)}. Bloqueos activos: ${countText(row)}.`);
        disc.textContent=!row.verified?'?':row.activeLocks>99?'99+':row.activeLocks>0?fmt.format(row.activeLocks):'−';
        option.textContent=row.name?`${row.id} · ${row.name}`:`${row.id} · Sin información actual`;
      }
      const unknown=view.filter(row=>!row.verified).length;
      $('stat-total').textContent=fmt.format(view.length);
      for(const [id,value] of Object.entries({'stat-locked':view.filter(r=>r.activeLocks>0).length,'stat-free':view.filter(r=>r.activeLocks===0).length,'stat-locks':view.reduce((sum,r)=>sum+(r.activeLocks||0),0)}))$(id).textContent=unknown?'—':fmt.format(value);
      $('availability').textContent=!verified?`${reason}. Estados y contadores sin verificar.`:unknown?`${unknown} posición(es) sin datos válidos del catálogo. «—» no representa cero bloqueos.`:'Estados digitales confirmados por la última lectura del catálogo.';
      $('verified-at').textContent=verifiedAt?new Intl.DateTimeFormat('es-CL',{hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(verifiedAt):'Sin verificar';
      if(verifiedAt)$('verified-at').dateTime=new Date(verifiedAt).toISOString();else $('verified-at').removeAttribute('datetime');
      const extra=rows.filter(row=>row&&typeof row.id==='string'&&!POSITIONS.some(p=>p.id===row.id));
      $('unmapped').hidden=!extra.length;$('unmapped').textContent=extra.length?`${extra.length} equipo(s) del catálogo no tienen posición en este esquema. Consúltalos en Resumen general.`:'';
      hideTooltip();detail();
    }
    function select(id){if(!POSITIONS.some(p=>p.id===id))return;selected=id;for(const [key,node]of nodes)node.button.setAttribute('aria-pressed',String(key===id));hideTooltip();detail();onSelect(id);announce(`${current().name||id}. ${stateText(current())}.`);}
    function cameraUpdate(){camera.x=clamp(camera.x,1-camera.zoom,0);camera.y=clamp(camera.y,1-camera.zoom,0);$('plan-viewport').scrollLeft=0;$('plan-viewport').scrollTop=0;
      $('scene').style.transform=camera.zoom===1?'none':`translate(${camera.x*100}%,${camera.y*100}%) scale(${camera.zoom})`;
      $('zoom-level').textContent=`${fmt.format(camera.zoom*100)} %`;$('zoom-out').disabled=camera.zoom<=1;$('zoom-in').disabled=camera.zoom>=2.5;
      $('plan-viewport').dataset.zoomed=String(camera.zoom>1);$('pan-controls').hidden=camera.zoom===1;hideTooltip();}
    function center(id){const p=POSITIONS.find(p=>p.id===id);if(!p)return;camera.x=.5-p.x/1280*camera.zoom;camera.y=.5-p.y/880*camera.zoom;cameraUpdate();}
    function zoom(value){const next=clamp(value,1,2.5),p=POSITIONS.find(p=>p.id===selected),x=p?p.x/1280:(.5-camera.x)/camera.zoom,y=p?p.y/880:(.5-camera.y)/camera.zoom;camera.zoom=next;camera.x=.5-x*next;camera.y=.5-y*next;cameraUpdate();}
    function ensureVisible(id){if(camera.zoom===1)return;const r=nodes.get(id).button.getBoundingClientRect(),v=$('plan-viewport').getBoundingClientRect();if(r.left<v.left+8||r.right>v.right-8||r.top<v.top+8||r.bottom>v.bottom-35)center(id);}
    function showTooltip(id){const row=view.find(row=>row.id===id);if(!row||drag)return;hideTooltip();tooltipId=id;
      $('tip-code').textContent=id;$('tip-name').textContent=row.name||'Equipo sin información actual';$('tip-area').textContent=row.area||'Área sin verificar';$('tip-state').textContent=stateText(row);$('tip-count').textContent=`Bloqueos activos: ${countText(row)}`;
      const tip=$('machine-tooltip');tip.hidden=false;tip.style.maxHeight='';const r=nodes.get(id).button.getBoundingClientRect(),v=$('plan-viewport').getBoundingClientRect(),width=tip.offsetWidth;
      const above=r.top-v.top-16,below=v.bottom-r.bottom-16,up=above>=tip.offsetHeight||above>=below;tip.style.maxHeight=`${Math.max(32,up?above:below)}px`;
      tip.style.left=`${clamp(r.left-v.left+r.width/2-width/2,8,Math.max(8,v.width-width-8))}px`;tip.style.top=`${clamp(up?r.top-v.top-tip.offsetHeight-8:r.bottom-v.top+8,8,Math.max(8,v.height-tip.offsetHeight-8))}px`;
      nodes.get(id).button.setAttribute('aria-describedby','machine-tooltip');}
    const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent='Selecciona un equipo';$('machine-picker').append(placeholder);
    for(const p of POSITIONS){const button=document.createElement('button');button.type='button';button.className='machine-marker';button.id='point-'+p.id;button.dataset.machineId=p.id;button.style.left=`${p.x/1280*100}%`;button.style.top=`${p.y/880*100}%`;
      const disc=document.createElement('span');disc.className='marker-disc';disc.setAttribute('aria-hidden','true');const label=document.createElement('span');label.className='marker-label';label.textContent=p.id;label.setAttribute('translate','no');label.setAttribute('aria-hidden','true');button.append(disc,label);$('markers').append(button);
      const option=document.createElement('option');option.value=p.id;$('machine-picker').append(option);nodes.set(p.id,{button,disc,option});
      button.addEventListener('click',()=>select(p.id));button.addEventListener('focus',()=>{ensureVisible(p.id);showTooltip(p.id);});button.addEventListener('blur',hideTooltip);
      button.addEventListener('pointerenter',e=>{if(e.pointerType!=='touch')showTooltip(p.id);});button.addEventListener('pointerleave',e=>{if(!$('machine-tooltip').contains(e.relatedTarget)&&root.activeElement!==button)hideTooltip();});}
    $('machine-tooltip').addEventListener('pointerleave',e=>{if(tooltipId&&e.relatedTarget!==nodes.get(tooltipId).button&&root.activeElement!==nodes.get(tooltipId).button)hideTooltip();});
    root.addEventListener('keydown',e=>{if(e.key==='Escape')hideTooltip();});
    $('machine-picker').addEventListener('change',e=>{if(e.target.value){select(e.target.value);if(camera.zoom>1)center(e.target.value);}else clearSelection();});
    function clearSelection(){selected=null;for(const node of nodes.values())node.button.setAttribute('aria-pressed','false');hideTooltip();detail();onSelect(null);}
    $('clear-selection').addEventListener('click',()=>{clearSelection();$('machine-picker').focus();});
    $('open-analysis').addEventListener('click',()=>{if(current()?.present)onOpen(selected);});
    $('refresh').addEventListener('click',async()=>{$('refresh').disabled=true;try{await onRefresh();}finally{$('refresh').disabled=false;}});
    $('zoom-in').addEventListener('click',()=>zoom(camera.zoom+.5));$('zoom-out').addEventListener('click',()=>zoom(camera.zoom-.5));$('fit-plan').addEventListener('click',()=>{camera.zoom=1;camera.x=0;camera.y=0;cameraUpdate();});
    root.querySelectorAll('[data-pan]').forEach(button=>button.addEventListener('click',()=>{const d=button.dataset.pan;camera.x+=d==='left'?.18:d==='right'?-.18:0;camera.y+=d==='up'?.18:d==='down'?-.18:0;cameraUpdate();}));
    $('plan-viewport').addEventListener('pointerdown',e=>{if(camera.zoom===1||e.button!==0||e.pointerType==='touch'||e.target.closest('button,.machine-tooltip'))return;const r=$('plan-viewport').getBoundingClientRect();drag={id:e.pointerId,x:e.clientX,y:e.clientY,cx:camera.x,cy:camera.y,w:r.width,h:r.height};$('plan-viewport').setPointerCapture(e.pointerId);$('plan-viewport').classList.add('dragging');hideTooltip();e.preventDefault();});
    $('plan-viewport').addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;camera.x=drag.cx+(e.clientX-drag.x)/drag.w;camera.y=drag.cy+(e.clientY-drag.y)/drag.h;cameraUpdate();});
    for(const type of ['pointerup','pointercancel','lostpointercapture'])$('plan-viewport').addEventListener(type,()=>{drag=null;$('plan-viewport').classList.remove('dragging');});
    cameraUpdate();
    return Object.freeze({render,clear:()=>{hideTooltip();view=[];selected=null;nodes.clear();root.replaceChildren();}});
  }
  window.SilbomSupervisorPlan=Object.freeze({create});
})();
