#!/usr/bin/env python3
"""Empaqueta la demo sin dependencias. Conserva las fuentes separadas y una CSP con hashes."""
import argparse
import base64
import hashlib
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'SILBOM-plano-demo.html'
SCRIPTS=('datos-demo.js','plano.js','script.js')

def csp_hash(content):
    return "'sha256-"+base64.b64encode(hashlib.sha256(content.encode('utf-8')).digest()).decode('ascii')+"'"

def generate():
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    css='\n'+(ROOT/'styles.css').read_text(encoding='utf-8')+'\n'
    script='\n'+'\n'.join('// '+name+'\n'+(ROOT/name).read_text(encoding='utf-8') for name in SCRIPTS)+'\n'
    if re.search(r'</script[\s>]',script,re.I) or re.search(r'</style[\s>]',css,re.I):
        raise ValueError('Las fuentes contienen una etiqueta de cierre incompatible con el empaquetado.')
    for name in SCRIPTS:
        tag=f'  <script defer src="{name}"></script>\n'
        if html.count(tag)!=1:raise ValueError('Referencia inesperada: '+name)
        html=html.replace(tag,'')
    tag='  <link rel="stylesheet" href="styles.css">'
    if html.count(tag)!=1:raise ValueError('Referencia CSS inesperada')
    html=html.replace(tag,'  <style>'+css+'</style>')
    # Dibujo estático visible incluso si un visor no ejecuta JavaScript. Los controles
    # requieren un navegador que ejecute JS; el mensaje inicial lo explica.
    drawing=(ROOT/'plano.js').read_text(encoding='utf-8').split('markup: `',1)[1].rsplit('`}',1)[0]
    html=html.replace('<div id="blueprint-layer" class="blueprint-layer"></div>',
                      '<div id="blueprint-layer" class="blueprint-layer">'+drawing+'</div>')
    html=html.replace('El plano aún no se ha cargado. Si descargaste solo index.html, usa <a href="SILBOM-plano-demo.html">SILBOM-plano-demo.html (archivo único)</a> o conserva los archivos de la carpeta juntos. Abre el archivo en un navegador con JavaScript habilitado.',
                      'Las interacciones todavía no se han cargado. Descarga este HTML y ábrelo en Chrome, Firefox o Safari con JavaScript habilitado. La vista previa de un archivo puede mostrar solo el dibujo.')
    policy="default-src 'none'; script-src "+csp_hash(script)+"; style-src "+csp_hash(css)+"; img-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'; object-src 'none'"
    html=re.sub(r'(<meta http-equiv="Content-Security-Policy" content=")[^"]+(">)',lambda m:m[1]+policy+m[2],html,count=1)
    html=html.replace('</body>','  <script>'+script+'</script>\n</body>')
    html=html.replace('<!doctype html>','<!doctype html>\n<!-- Archivo autónomo generado por exportar-demo.py. Editar las fuentes separadas. -->',1)
    return html

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Comprueba que el HTML portátil coincide con las fuentes sin escribirlo.')
    args=parser.parse_args()
    content=generate()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8')!=content:
            raise SystemExit('HTML portátil desactualizado. Ejecuta python3 exportar-demo.py.')
        print('HTML portátil actualizado.')
    else:
        OUTPUT.write_text(content,encoding='utf-8');print(OUTPUT)

if __name__=='__main__':main()
