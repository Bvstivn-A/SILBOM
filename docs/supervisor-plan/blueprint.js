/* Dibujo arquitectónico ilustrativo. Coordenadas gráficas, nunca metros.
 * Sin rutas, dimensiones, salidas ni certificaciones de seguridad reales. */
(() => {
  'use strict';
  window.SilbomSupervisorBlueprint = Object.freeze({markup: `
<svg class="blueprint" viewBox="0 0 1280 880" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="blueprint-title blueprint-description">
  <title id="blueprint-title">Plano industrial ficticio en vista superior</title>
  <desc id="blueprint-description">Salas de maquinaria, preparación y moldeo al norte del pasillo; mantenimiento al costado derecho. Producción ocupa la nave inferior, junto a bodega y despacho. Puertas y posiciones son ilustrativas, sin escala ni certificación.</desc>
  <defs>
    <pattern id="technical-grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#2b5873" stroke-width=".7" opacity=".35"/></pattern>
    <pattern id="circulation-hatch" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V12" fill="none" stroke="#5a88a2" stroke-width="1" opacity=".2"/></pattern>
    <pattern id="rack-hatch" width="18" height="18" patternUnits="userSpaceOnUse"><path d="M0 0L18 18" stroke="#7497ad" stroke-width="1" opacity=".35"/></pattern>
    <g id="workbench"><rect width="160" height="32" rx="2"/><path d="M40 0v32m40-32v32m40-32v32"/><circle cx="25" cy="58" r="11"/><circle cx="80" cy="58" r="11"/><circle cx="135" cy="58" r="11"/></g>
    <g id="compressor-plan"><rect x="-70" y="-38" width="140" height="76" rx="7"/><path d="M-57-38v76m114-76v76m-99-64v52m10-52v52m10-52v52m10-52v52"/><circle cx="29" cy="0" r="24"/><circle cx="29" cy="0" r="10"/><path d="M-70-20h-12v40h12m140-40h12v40H70M-51 38v10h18V38m66 0v10h18V38"/></g>
    <g id="mixer-plan"><rect x="-66" y="-48" width="132" height="96" rx="30"/><path d="M0-48v96m-43-72 86 48m-86 0 86-48"/><circle r="17"/><path d="M-66-20h-10v40h10m132-40h10v40H66M-40-56h80m-80 112h80"/></g>
    <g id="extruder-plan"><rect x="-54" y="-24" width="115" height="48" rx="3"/><rect x="-85" y="-30" width="31" height="60" rx="5"/><path d="M-85-18h31m-31 12h31m-31 12h31m-31 12h31m11-42 12 48m4-48 12 48m4-48 12 48m4-48 12 48m4-48 12 48M-32-46h40v22h-40zM61-17h24v34H61"/></g>
    <g id="press-plan"><rect x="-63" y="-64" width="126" height="128" rx="3"/><path d="M-44-64V64m88-128V64m-88-99h88m-88 70h88M0-64v29"/><rect x="-29" y="-30" width="58" height="17" rx="2"/><rect x="-29" y="13" width="58" height="22" rx="2"/><path d="M-63-44h-16v24h16m126 40h16v24H63"/></g>
    <g id="filler-plan"><circle r="59"/><circle r="36"/><circle r="12"/><path d="M0-59v23m59 36H36M0 59V36m-59-36h23m-6-42 16 16m68-16L26-26m16 68L26 26m-68 16 16-16"/><rect x="-115" y="-15" width="56" height="30" rx="4"/><rect x="59" y="-15" width="56" height="30" rx="4"/><path d="M-30-71h60m-60 142h60"/></g>
    <g id="conveyor-plan"><rect x="-91" y="-40" width="182" height="80" rx="27"/><rect x="-80" y="-28" width="160" height="56" rx="20"/><path d="M-60-28v56m20-56v56m20-56v56m20-56v56m20-56v56m20-56v56m20-56v56M-60-51H60m-120 102H60"/></g>
  </defs>
  <rect width="1280" height="880" fill="url(#technical-grid)"/>
  <g class="drafting-corners"><path d="M28 58V28h30m1164 0h30v30M28 822v30h30m1164 0h30v-30"/></g>
  <g class="room-surfaces">
    <path d="M90 100H920V72h270v740H915v-60H90Z" fill="#173448"/>
    <path id="zone-sala-maquinas" data-zone="sala-maquinas" d="M90 100h275v230H90Z"/>
    <path id="zone-preparacion" data-zone="preparacion" d="M365 100h300v230H365Z"/>
    <path id="zone-moldeo" data-zone="moldeo" d="M665 100h255v230H665Z"/>
    <path id="zone-mantenimiento" data-zone="mantenimiento" d="M920 72h270v258H920Z"/>
    <path id="zone-produccion" data-zone="produccion" d="M90 410h745v342H90Z"/>
    <path id="zone-bodega" data-zone="bodega" d="M915 410h275v402H915Z"/>
  </g>
  <g class="circulation">
    <path d="M90 330h1100v80H90Zm745 80h80v342h-80Z" fill="#244254"/>
    <path d="M90 330h1100v80H90Zm745 80h80v342h-80Z" fill="url(#circulation-hatch)"/>
    <path class="circulation-center" d="M137 370h1005M875 435v280"/>
  </g>
  <g class="technical-fixtures">
    <use href="#workbench" x="972" y="156"/>
    <rect x="953" y="256" width="70" height="37"/><path d="M953 267h70m-70 13h70"/>
    <rect x="1090" y="256" width="68" height="37"/><path d="M1090 267h68m-68 13h68"/>
    <rect x="947" y="464" width="210" height="40" fill="url(#rack-hatch)"/><path d="M989 464v40m42-40v40m42-40v40m42-40v40"/>
    <rect x="947" y="521" width="210" height="28" fill="url(#rack-hatch)"/><path d="M989 521v28m42-28v28m42-28v28m42-28v28"/>
    <rect x="950" y="731" width="48" height="36"/><path d="m950 731 48 36m-48 0 48-36"/>
    <rect x="1110" y="731" width="48" height="36"/><path d="m1110 731 48 36m-48 0 48-36"/>
    <path class="service-outline" d="M151 180h168v112H151Zm286-7h148v119H437Zm269 5h168v116H706Z"/>
    <path class="service-outline" d="M182 484h207v208H182Zm277 8h282v200H459Z"/>
  </g>
  <g class="machine-footprints" aria-hidden="true">
    <use href="#compressor-plan" x="235" y="222"/>
    <use href="#mixer-plan" x="510" y="218"/>
    <use href="#extruder-plan" x="790" y="224"/>
    <use href="#press-plan" x="285" y="563"/>
    <use href="#filler-plan" x="600" y="566"/>
    <use href="#conveyor-plan" x="1050" y="650"/>
  </g>
  <g class="structural-columns"><rect x="95" y="414" width="17" height="17"/><rect x="810" y="414" width="17" height="17"/><rect x="95" y="721" width="17" height="17"/><rect x="810" y="721" width="17" height="17"/><rect x="119" y="414" width="6" height="17"/></g>
  <path class="outer-wall" d="M90 100H920V72h270v740H915v-60H90Z"/>
  <path class="wall-core" d="M90 100H920V72h270v740H915v-60H90Z"/>
  <g class="inner-walls"><path d="M365 100v230m300-230v230M920 72v258M90 330h118m56 0h213m56 0h221m56 0h165m56 0h159M90 410h118m56 0h331m74 0h306m56 0h159M835 410v153m0 66v123m80-342v153m0 66v123"/></g>
  <g class="door-openings"><path d="M90 345v50m370 357h72m478 60h100"/></g>
  <g class="doors">
    <path d="M208 330v-56m56 56a56 56 0 0 0-56-56M477 330v-56m56 56a56 56 0 0 0-56-56M754 330v-56m56 56a56 56 0 0 0-56-56M975 330v-56m56 56a56 56 0 0 0-56-56"/>
    <path d="M208 410v56m56-56a56 56 0 0 1-56 56M595 410v74m74-74a74 74 0 0 1-74 74M975 410v56m56-56a56 56 0 0 1-56 56M835 563h-66m66 66a66 66 0 0 1-66-66M915 563h66m-66 66a66 66 0 0 0 66-66"/>
    <path d="M90 345h50m-50 50a50 50 0 0 0 50-50M460 752v-72m72 72a72 72 0 0 0-72-72M1010 812v-12h100v12m-100-7h100"/>
  </g>
  <g class="zone-text">
    <text x="126" y="140">Sala de máquinas</text><text class="zone-subtitle" x="126" y="162">Servicios auxiliares</text>
    <text x="400" y="140">Preparación</text><text class="zone-subtitle" x="400" y="162">Mezcla de materiales</text>
    <text x="700" y="140">Moldeo</text><text class="zone-subtitle" x="700" y="162">Extrusión</text>
    <text x="950" y="115">Mantenimiento</text><text class="zone-subtitle" x="950" y="137">Taller de apoyo</text>
    <text x="128" y="460">Producción</text><text class="zone-subtitle" x="128" y="481">Estampado y envasado</text>
    <text x="948" y="444">Bodega</text><text class="zone-subtitle" x="948" y="580">Logística y despacho</text>
  </g>
  <g class="circulation-text"><rect x="422" y="353" width="338" height="34" rx="3"/><text x="591" y="376" text-anchor="middle">Pasillo de circulación</text><text x="876" y="496" text-anchor="middle" transform="rotate(90 876 496)">Circulación</text></g>
  <g class="access-labels"><path d="M35 345v50m-8-25h55m-9-6 9 6-9 6"/><text x="33" y="425">Acceso</text><path d="M470 788h50m-25-15v37m-6-9 6 9 6-9"/><text x="550" y="803">Acceso a producción</text><text x="956" y="845">Acceso de despacho</text></g>
</svg>`});
})();
