#!/usr/bin/env python3
"""Verifica únicamente la demostración estática; nunca inicia Spring ni PostgreSQL."""
import hashlib
import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from threading import Thread
import unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'evidencias'
OUT.mkdir(exist_ok=True)
ASSETS = ['index.html','styles.css','script.js','datos-demo.js','plano.js']
REPORT = {'browser':'Chromium', 'checks':[], 'viewports':[], 'requests':[],
          'sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ASSETS}}
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass
    def reject(self):
        self.send_error(405,'Servidor de archivos de pruebas; no admite escrituras')
    do_POST=do_PUT=do_PATCH=do_DELETE=reject

class PlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
        cls.thread=Thread(target=cls.server.serve_forever,daemon=True); cls.thread.start()
        cls.pw=sync_playwright().start()
        executable=os.environ.get('SILBOM_TEST_CHROMIUM') or shutil.which('chromium')
        cls.browser=cls.pw.chromium.launch(**({'executable_path':executable} if executable else {}),
                                         args=['--no-sandbox','--disable-dev-shm-usage'])
        cls.url=f'http://127.0.0.1:{cls.server.server_port}/'
    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':1600,'height':1100})
        self.page=self.context.new_page(); self.errors=[]; self.requests=[]; self.console_errors=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.on('console',lambda msg:self.console_errors.append(msg.text) if msg.type=='error' else None)
        self.page.on('request',lambda req:self.requests.append({'method':req.method,'url':req.url}))
        self.page.goto(self.url+'index.html'); self.page.wait_for_function('window.SilbomIndustrialPlan !== undefined')
        self.initial=self.page.evaluate('SilbomPlanData.initialMachines()')
    def tearDown(self):
        try:
            self.assertEqual(self.errors,[],'Excepciones JavaScript')
            self.assertEqual(self.console_errors,[],'Errores de consola/CSP')
            allowed={self.url+name for name in ASSETS}
            self.assertTrue(all(r['method']=='GET' and r['url'].split('#')[0] in allowed for r in self.requests),self.requests)
            REPORT['requests'].extend(self.requests)
        finally:
            self.context.close()
    def metrics(self):
        return [self.page.locator('#stat-'+key).inner_text() for key in ('total','locked','free','locks')]
    def select(self,code):
        self.page.locator('#point-'+code).click()
        self.assertEqual(self.page.locator('#detail-code').inner_text(),code)
    def render(self,rows,verified=True):
        self.page.evaluate('(v)=>SilbomIndustrialPlan.renderMachines(v.rows,{verified:v.verified})',{'rows':rows,'verified':verified})
    def snapshot(self):
        return self.page.evaluate('SilbomIndustrialPlan.snapshot()')

    def test_01_catalog_architecture_and_consistent_positions(self):
        self.assertEqual(self.page.locator('.machine-marker').count(),6)
        self.assertEqual(self.metrics(),['6','2','4','3'])
        self.assertEqual(self.page.locator('#detail-count').inner_text(),'2')
        self.assertEqual(self.page.locator('.machine-marker[data-state=free]').count(),4)
        self.assertEqual(self.page.locator('.machine-marker[data-state=locked]').count(),2)
        self.assertTrue(self.page.locator('.outer-wall').is_visible())
        self.assertEqual(self.page.locator('[data-zone]').count(),6)
        positions=self.page.evaluate('SilbomPlanData.positions')
        for point in positions:
            geometry=self.page.locator('#point-'+point['id']).evaluate('''el=>{
              const r=el.getBoundingClientRect(),v=document.querySelector('#plan-viewport').getBoundingClientRect();
              return {x:(r.x+r.width/2-v.x)/v.width,y:(r.y+r.height/2-v.y)/v.height};}''')
            self.assertAlmostEqual(geometry['x'],point['x']/1280,places=3)
            self.assertAlmostEqual(geometry['y'],point['y']/880,places=3)
            self.assertIn(point['id'],self.page.locator('#point-'+point['id']).get_attribute('aria-label'))
        self.assertIn("connect-src 'none'",self.page.locator('meta[http-equiv="Content-Security-Policy"]').get_attribute('content'))

    def test_02_mouse_selection_all_catalog_rows_without_mutation(self):
        self.page.evaluate('window.originalMarker=document.querySelector(".machine-marker");window.pageMarker=321')
        for row in self.initial:
            self.select(row['id'])
            self.assertEqual(self.page.locator('#detail-name').inner_text(),row['nombre'])
            self.assertEqual(self.page.locator('#detail-area').inner_text(),row['area'])
            self.assertEqual(self.page.locator('#machine-picker').input_value(),row['id'])
        self.assertEqual(self.metrics(),['6','2','4','3'])
        self.assertEqual(self.page.evaluate('window.pageMarker'),321)
        self.assertTrue(self.page.evaluate('originalMarker===document.querySelector(".machine-marker")'))

    def test_03_tooltip_hover_keyboard_dismiss_and_keep_point_visible(self):
        for width in (390,768,1600):
            self.page.set_viewport_size({'width':width,'height':1100})
            point=self.page.locator('#point-EQ-COM-03'); point.hover()
            tooltip=self.page.locator('#machine-tooltip')
            self.assertTrue(tooltip.is_visible())
            for part in ('Compresor de Tornillo','EQ-COM-03','Sala de Máquinas','Sin bloqueos digitales','Bloqueos activos: 0'):
                self.assertIn(part,tooltip.inner_text())
            p=point.bounding_box(); t=tooltip.bounding_box()
            self.assertTrue(t['y']+t['height']<=p['y'] or t['y']>=p['y']+p['height'],'Tooltip cubre el punto enfocado')
            self.page.keyboard.press('Escape'); self.assertTrue(tooltip.is_hidden())
            point.focus(); self.assertTrue(tooltip.is_visible())
            self.assertTrue(point.evaluate('(el)=>el.matches(":focus-visible")'))
            point.press('Enter'); self.assertEqual(self.page.locator('#detail-code').inner_text(),'EQ-COM-03')
            point.press('Space'); self.assertEqual(self.metrics(),['6','2','4','3'])
            self.page.locator('#fit-plan').focus()

    def test_04_green_red_multi_zero_and_reset(self):
        self.select('EQ-COM-03')
        self.page.locator('[data-demo-count="1"]').click()
        self.assertEqual(self.metrics(),['6','3','3','4'])
        self.assertEqual(self.page.locator('#point-EQ-COM-03').get_attribute('data-state'),'locked')
        self.page.locator('[data-demo-count="2"]').click()
        self.assertEqual(self.page.locator('#detail-count').inner_text(),'2')
        self.assertIn('2 bloqueos LOTO activos',self.page.locator('#detail-state').inner_text())
        self.assertEqual(self.metrics(),['6','3','3','5'])
        self.page.locator('[data-demo-count="0"]').click()
        self.assertEqual(self.page.locator('#point-EQ-COM-03').get_attribute('data-state'),'free')
        self.select('EQ-ENV-01');self.page.locator('[data-demo-count="0"]').click()
        self.assertEqual(self.metrics(),['6','1','5','1'])
        self.page.locator('#reset-demo').click()
        self.assertEqual(self.metrics(),['6','2','4','3'])
        self.assertEqual(self.page.locator('#detail-code').inner_text(),'EQ-ENV-01')

    def test_05_offline_stale_gray_and_restore(self):
        self.page.locator('[data-demo-count="1"]').click()
        for scenario in ('offline','stale'):
            self.page.locator('#scenario').select_option(scenario)
            self.assertEqual(self.metrics(),['6','—','—','—'])
            self.assertEqual(self.page.locator('.machine-marker[data-state=unknown]').count(),6)
            self.assertEqual(self.page.locator('#detail-count').inner_text(),'Sin verificar')
            self.assertEqual(self.page.locator('#detail-mtbf').inner_text(),'Sin verificar')
            self.assertTrue(all(b.is_disabled() for b in self.page.locator('[data-demo-count]').all()))
            self.page.locator('#point-EQ-ENV-01').hover()
            self.assertIn('Bloqueos activos: Sin verificar',self.page.locator('#machine-tooltip').inner_text())
        self.page.locator('#scenario').select_option('available')
        self.assertEqual(self.metrics(),['6','2','4','2'])

    def test_06_sheet_escape_focus_and_no_operation(self):
        self.page.locator('#open-sheet').click()
        self.assertTrue(self.page.locator('#sheet').evaluate('(el)=>el.open'))
        self.assertEqual(self.page.locator('#sheet-code').inner_text(),'EQ-ENV-01')
        self.assertEqual(self.page.locator('#sheet-count').inner_text(),'2')
        self.page.locator('#back-to-plan').focus();self.page.keyboard.press('Tab')
        self.assertEqual(self.page.evaluate('document.activeElement.id'),'close-sheet')
        self.page.keyboard.press('Shift+Tab')
        self.assertEqual(self.page.evaluate('document.activeElement.id'),'back-to-plan')
        self.page.keyboard.press('Escape')
        self.page.wait_for_function('document.activeElement.id==="open-sheet"')
        self.assertFalse(self.page.locator('#sheet').evaluate('(el)=>el.open'))
        self.assertEqual(self.metrics(),['6','2','4','3'])

    def test_07_zoom_pan_fit_and_keyboard_recenters(self):
        for zoom in (1.5,2,2.5):
            self.page.locator('#zoom-in').click()
            self.assertEqual(self.snapshot()['camera']['zoom'],zoom)
        self.assertTrue(self.page.locator('#zoom-in').is_disabled())
        self.assertTrue(self.page.locator('#pan-controls').is_visible())
        original=self.snapshot()['camera']
        self.page.locator('[data-pan=left]').click()
        self.assertNotEqual(original['x'],self.snapshot()['camera']['x'])
        for row in self.initial:
            point=self.page.locator('#point-'+row['id']);point.focus();point.press('Enter')
            self.assertEqual(self.page.locator('#detail-code').inner_text(),row['id'])
            r=point.bounding_box();v=self.page.locator('#plan-viewport').bounding_box()
            self.assertGreaterEqual(r['x'],v['x']);self.assertLessEqual(r['x']+r['width'],v['x']+v['width'])
            self.assertGreaterEqual(r['y'],v['y']);self.assertLessEqual(r['y']+r['height'],v['y']+v['height'])
        self.page.locator('#fit-plan').click()
        self.assertEqual(self.snapshot()['camera'],{'zoom':1,'x':0,'y':0})
        self.assertTrue(self.page.locator('#zoom-out').is_disabled())
        self.assertTrue(self.page.locator('#pan-controls').is_hidden())
        self.assertEqual(self.metrics(),['6','2','4','3'])

    def test_08_drag_background_preserves_selection_and_state(self):
        self.page.locator('#zoom-in').click()
        original=self.snapshot()['camera'];v=self.page.locator('#plan-viewport').bounding_box()
        x=v['x']+30;y=v['y']+v['height']/2
        self.page.mouse.move(x,y);self.page.mouse.down();self.page.mouse.move(x+70,y+40,steps=5);self.page.mouse.up()
        self.assertNotEqual(original,self.snapshot()['camera'])
        self.assertEqual(self.snapshot()['selected'],'EQ-ENV-01')
        self.assertEqual(self.metrics(),['6','2','4','3'])

    def test_09_picker_clear_selection_and_deep_link(self):
        self.page.locator('#machine-picker').select_option('EQ-TR-01')
        self.assertEqual(self.page.locator('#detail-code').inner_text(),'EQ-TR-01')
        self.assertEqual(self.page.locator('#detail-mtbf').inner_text(),'No calculable')
        self.page.locator('#clear-selection').click()
        self.assertTrue(self.page.locator('#empty-detail').is_visible())
        self.assertTrue(self.page.locator('[data-demo-count="1"]').is_disabled())
        self.page.goto(self.url+'index.html#EQ-COM-03')
        self.assertEqual(self.page.locator('#detail-code').inner_text(),'EQ-COM-03')
        self.assertEqual(self.metrics(),['6','2','4','3'])
        self.page.evaluate('history.pushState(null,"","#%");dispatchEvent(new PopStateEvent("popstate"))')
        self.assertTrue(self.page.locator('#empty-detail').is_visible())

    def test_10_renderer_validation_reorder_and_mtbf(self):
        self.render(list(reversed(self.initial)));self.assertEqual(self.metrics(),['6','2','4','3'])
        for rows in (None,[],self.initial[:-1],[self.initial[0]]*6):
            self.render(rows);self.assertEqual(self.metrics(),['6','—','—','—'])
            self.assertEqual(self.page.locator('.machine-marker[data-state=unknown]').count(),6)
        for patch in ({'bloqueosActivos':-1},{'bloqueosActivos':'0'},{'bloqueada':False},{'nombre':''},{'bloqueosActivos':2147483648}):
            rows=[dict(row) for row in self.initial];rows[4].update(patch);self.render(rows)
            self.assertEqual(self.page.locator('#point-EQ-ENV-01').get_attribute('data-state'),'unknown')
            self.assertEqual(self.metrics(),['6','—','—','—'])
        for value,expected in ((None,'No calculable'),(-1,'No calculable'),('12','No calculable'),(0,'0 h')):
            self.render([dict(row,mtbf=value) for row in self.initial])
            self.assertEqual(self.page.locator('#detail-mtbf').inner_text(),expected)
        self.render(self.initial,verified=False)
        self.page.locator('#scenario').select_option('offline')
        self.page.locator('#scenario').select_option('available')
        self.assertEqual(self.page.locator('.machine-marker[data-state=unknown]').count(),6)

    def test_11_untrusted_text_is_not_html(self):
        payload='<img src=x onerror="window.injected=true">'
        self.render([dict(row,nombre=payload,area=payload) for row in self.initial])
        self.assertEqual(self.page.locator('#detail-name').inner_text(),payload)
        self.assertEqual(self.page.locator('img').count(),0)
        self.assertIsNone(self.page.evaluate('window.injected'))

    def test_12_responsive_proportions_targets_and_no_overlap(self):
        for width in (375,390,768,834,1024,1280,1440,1600,1920):
            self.page.set_viewport_size({'width':width,'height':1000})
            geometry=self.page.evaluate('''()=>{
              const v=document.querySelector('#plan-viewport').getBoundingClientRect(),side=document.querySelector('.side-column').getBoundingClientRect(),map=document.querySelector('.plan-section').getBoundingClientRect();
              return {width:innerWidth,scroll:document.documentElement.scrollWidth,ratio:v.width/v.height,side:{x:side.x,y:side.y},map:{right:map.right,bottom:map.bottom},
                controls:[...document.querySelectorAll('button,select')].filter(x=>x.getClientRects().length).map(x=>({id:x.id,w:x.getBoundingClientRect().width,h:x.getBoundingClientRect().height})),
                labels:[...document.querySelectorAll('.marker-label')].map(x=>{const r=x.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom};})};}''')
            self.assertLessEqual(geometry['scroll'],width)
            self.assertAlmostEqual(geometry['ratio'],1280/880,places=2)
            for control in geometry['controls']:
                self.assertGreaterEqual(control['h'],44,control);self.assertGreaterEqual(control['w'],44,control)
            if width>1280:self.assertGreaterEqual(geometry['side']['x'],geometry['map']['right'])
            else:self.assertGreaterEqual(geometry['side']['y'],geometry['map']['bottom'])
            for i,a in enumerate(geometry['labels']):
                for b in geometry['labels'][i+1:]:
                    self.assertTrue(a['right']<=b['x'] or b['right']<=a['x'] or a['bottom']<=b['y'] or b['bottom']<=a['y'],'Identificadores superpuestos')
            REPORT['viewports'].append(geometry)

    def test_13_reduced_motion_offline_and_large_text(self):
        self.page.emulate_media(reduced_motion='reduce')
        self.assertEqual(self.page.locator('.marker-disc').first.evaluate('(el)=>getComputedStyle(el).transitionDuration'),'0s')
        self.context.set_offline(True)
        self.page.locator('[data-demo-count="0"]').click()
        self.assertEqual(self.metrics(),['6','1','5','1'])
        self.assertIn('Solo cambiaron datos simulados',self.page.locator('#feedback').inner_text())
        self.context.set_offline(False)
        self.page.set_viewport_size({'width':768,'height':1000})
        self.page.evaluate('''()=>{
          const values=[...document.querySelectorAll('body,body *:not(svg):not(svg *)')].map(el=>[el,parseFloat(getComputedStyle(el).fontSize)]);
          values.forEach(([el,size])=>el.style.setProperty('font-size',`${size*2}px`,'important'));
        }''')
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),768)

    def test_14_captures(self):
        for width,name in ((1600,'escritorio-1600'),(1024,'tablet-1024'),(390,'movil-390')):
            self.page.set_viewport_size({'width':width,'height':1100})
            self.page.screenshot(path=str(OUT/(name+'.png')),full_page=True)
        self.page.set_viewport_size({'width':1600,'height':1100})
        self.page.locator('#point-EQ-COM-03').hover()
        self.page.screenshot(path=str(OUT/'tooltip.png'),full_page=True)
        self.page.locator('#scenario').select_option('offline')
        self.page.screenshot(path=str(OUT/'sin-verificar.png'),full_page=True)
        self.page.locator('#scenario').select_option('available')
        self.page.locator('#zoom-in').click()
        self.page.screenshot(path=str(OUT/'zoom-150.png'),full_page=True)
        self.page.locator('#open-sheet').click()
        self.page.screenshot(path=str(OUT/'ficha-local.png'),full_page=True)

    def test_15_direct_file_opening(self):
        page=self.context.new_page()
        try:
            page.goto((ROOT/'index.html').as_uri())
            self.assertEqual(page.locator('.machine-marker').count(),6)
            page.locator('[data-demo-count="0"]').click()
            self.assertEqual(page.locator('#detail-count').inner_text(),'0')
            REPORT['direct_file']='verified'
        except Exception as error:
            if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(error):raise
            REPORT['direct_file']='not_verified_managed_browser_policy'
            self.skipTest('El navegador administrado bloquea file://. Verificar apertura directa en un navegador personal.')
        finally:page.close()

class Result(unittest.TextTestResult):
    def addSuccess(self,test):
        super().addSuccess(test);REPORT['checks'].append({'test':test._testMethodName,'status':'pass'})
    def addFailure(self,test,error):
        super().addFailure(test,error);REPORT['checks'].append({'test':test._testMethodName,'status':'fail'})
    def addError(self,test,error):
        super().addError(test,error);REPORT['checks'].append({'test':test._testMethodName,'status':'error'})
    def addSkip(self,test,reason):
        super().addSkip(test,reason);REPORT['checks'].append({'test':test._testMethodName,'status':'skip','reason':reason})
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromTestCase(PlanTests))
    REPORT.update(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped))
    for request in REPORT['requests']:request['url']=request['url'].replace(PlanTests.url,'http://127.0.0.1:<puerto>/')
    (OUT/'verificacion.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
