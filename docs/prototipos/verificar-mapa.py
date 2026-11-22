#!/usr/bin/env python3
"""Pruebas del prototipo aislado. No inicia Spring ni accede a PostgreSQL."""
import hashlib
import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import threading
import unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'evidencias-mapa'
OUT.mkdir(exist_ok=True)
REPORT = {'browser': 'Chromium', 'checks': [], 'viewports': [], 'requests': [],
          'html_sha256': hashlib.sha256((ROOT / 'mapa-planta.html').read_bytes()).hexdigest()}

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reject(self):
        self.send_error(405, 'Este servidor de pruebas solo sirve archivos')

    do_POST = do_PUT = do_PATCH = do_DELETE = reject

class MapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.pw = sync_playwright().start()
        executable = os.environ.get('SILBOM_TEST_CHROMIUM') or shutil.which('chromium')
        cls.browser = cls.pw.chromium.launch(**({'executable_path': executable} if executable else {}),
                                            args=['--no-sandbox', '--disable-dev-shm-usage'])
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/mapa-planta.html'

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 1040})
        self.page = self.context.new_page()
        self.errors, self.requests = [], []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('request', lambda req: self.requests.append({'method': req.method, 'url': req.url}))
        self.page.goto(self.url)
        self.initial = self.page.evaluate('SilbomPlantMap.snapshot().machines')

    def tearDown(self):
        self.assertEqual(self.errors, [], 'Excepciones JavaScript')
        self.assertTrue(all(r['method'] == 'GET' and r['url'].startswith(self.url) for r in self.requests),
                        f'Petición inesperada: {self.requests}')
        REPORT['requests'].extend(self.requests)
        self.context.close()

    def metrics(self):
        return [self.page.locator('#' + key).inner_text() for key in
                ('total-machines', 'locked-machines', 'free-machines', 'total-locks')]

    def render(self, rows, verified=True):
        self.page.evaluate('(v) => SilbomPlantMap.renderMachines(v.rows, {verified: v.verified})',
                           {'rows': rows, 'verified': verified})

    def select(self, machine):
        self.page.locator('#machine-' + machine).click()
        self.assertEqual(self.page.locator('#panel-code').inner_text(), machine)

    def test_01_catalog_and_derived_summary(self):
        self.assertEqual(self.page.locator('[data-machine-id]').count(), 6)
        self.assertEqual(self.metrics(), ['6', '2', '4', '3'])
        self.assertEqual(self.page.locator('#panel-count').inner_text(), '2')
        self.assertIn('2 bloqueos LOTO activos', self.page.locator('#panel-status').inner_text())
        self.assertEqual(self.page.locator('.machine[data-state=free]').count(), 4)
        self.assertEqual(self.page.locator('.machine[data-state=locked]').count(), 2)
        for row in self.initial:
            self.assertIn(row['nombre'], self.page.locator('#machine-' + row['id']).inner_text())
        self.assertIn("connect-src 'none'", self.page.locator('meta[http-equiv="Content-Security-Policy"]').get_attribute('content'))

    def test_02_all_selections_keyboard_and_hover(self):
        self.page.evaluate('window.savedButton = document.querySelector("[data-machine-id]")')
        for row in self.initial:
            self.select(row['id'])
            self.assertEqual(self.page.locator('#panel-name').inner_text(), row['nombre'])
            self.assertEqual(self.page.locator('#panel-area').inner_text(), row['area'])
        button = self.page.locator('#machine-EQ-COM-03')
        button.focus()
        button.press('Enter')
        self.assertEqual(self.page.locator('#panel-code').inner_text(), 'EQ-COM-03')
        self.assertTrue(button.evaluate('(el) => el.matches(":focus-visible")'))
        button.hover()
        self.assertIn('EQ-COM-03', button.get_attribute('title'))
        self.assertTrue(self.page.evaluate('savedButton === document.querySelector("[data-machine-id]")'))
        self.assertEqual(self.metrics(), ['6', '2', '4', '3'])

    def test_03_multiloto_and_reset(self):
        self.page.locator('#simulate-lock').click()
        self.assertEqual(self.page.locator('#panel-count').inner_text(), '3')
        self.assertEqual(self.metrics(), ['6', '2', '4', '4'])
        self.select('EQ-COM-03')
        self.page.locator('#simulate-lock').click()
        self.assertEqual(self.metrics(), ['6', '3', '3', '5'])
        self.assertEqual(self.page.locator('#machine-EQ-COM-03').get_attribute('data-state'), 'locked')
        self.page.locator('#reset-demo').click()
        self.assertEqual(self.metrics(), ['6', '2', '4', '3'])
        self.assertEqual(self.page.locator('#panel-code').inner_text(), 'EQ-ENV-01')

    def test_04_offline_stale_and_restore(self):
        self.page.locator('#simulate-lock').click()
        for scenario in ('offline', 'stale'):
            self.page.locator('#scenario').select_option(scenario)
            self.assertEqual(self.metrics(), ['6', '—', '—', '—'])
            self.assertEqual(self.page.locator('.machine[data-state=unknown]').count(), 6)
            self.assertTrue(self.page.locator('#simulate-lock').is_disabled())
            self.assertEqual(self.page.locator('#panel-mtbf').inner_text(), 'Sin verificar')
            self.assertEqual(self.page.locator('#panel-count').inner_text(), 'Sin verificar')
        self.page.locator('#scenario').select_option('available')
        self.assertEqual(self.metrics(), ['6', '2', '4', '4'])

    def test_05_local_sheet_keyboard_and_return_focus(self):
        self.page.locator('#show-sheet').click()
        self.assertTrue(self.page.locator('#sheet').evaluate('(el) => el.open'))
        self.assertEqual(self.page.locator('#sheet-id').inner_text(), 'EQ-ENV-01')
        self.page.locator('#back-to-map').focus()
        self.page.keyboard.press('Tab')
        self.assertEqual(self.page.evaluate('document.activeElement.id'), 'close-sheet')
        self.page.keyboard.press('Shift+Tab')
        self.assertEqual(self.page.evaluate('document.activeElement.id'), 'back-to-map')
        self.page.keyboard.press('Escape')
        self.assertFalse(self.page.locator('#sheet').evaluate('(el) => el.open'))
        self.page.wait_for_function('document.activeElement.id === "show-sheet"')
        self.assertEqual(self.metrics(), ['6', '2', '4', '3'])

    def test_06_clear_and_switch_without_reload(self):
        self.page.evaluate('window.pageMarker = 123')
        self.page.locator('#clear-selection').click()
        self.assertTrue(self.page.locator('#empty-panel').is_visible())
        self.assertEqual(self.page.evaluate('document.activeElement.id'), 'map-title')
        self.select('EQ-TR-01')
        self.assertEqual(self.page.locator('#panel-mtbf').inner_text(), 'No calculable')
        self.page.locator('#show-all').click()
        self.assertEqual(self.page.locator('[aria-pressed=true]').count(), 0)
        self.select('EQ-EXT-02')
        self.assertEqual(self.page.evaluate('window.pageMarker'), 123)

    def test_07_renderer_reordered_array_and_mtbf(self):
        self.render(list(reversed(self.initial)))
        self.assertEqual(self.metrics(), ['6', '2', '4', '3'])
        for value, expected in ((None, 'No calculable'), (-1, 'No calculable'), ('12', 'No calculable'), (0, '0 h')):
            rows = [dict(row, mtbf=value) for row in self.initial]
            self.render(rows)
            self.assertEqual(self.page.locator('#panel-mtbf').inner_text(), expected)
        self.page.evaluate('SilbomPlantMap.renderMachines(SilbomPlantMap.snapshot().machines.map(x => ({...x, mtbf: Infinity})))')
        self.assertEqual(self.page.locator('#panel-mtbf').inner_text(), 'No calculable')

    def test_08_invalid_incomplete_duplicate_data_fail_gray(self):
        for rows in (None, [], self.initial[:-1], [self.initial[0]] * 6):
            self.render(rows)
            self.assertEqual(self.metrics(), ['6', '—', '—', '—'])
            self.assertEqual(self.page.locator('.machine[data-state=unknown]').count(), 6)
        for patch in ({'bloqueosActivos': -1}, {'bloqueosActivos': '0'}, {'bloqueada': False}, {'nombre': ''}):
            rows = [dict(row) for row in self.initial]
            rows[4].update(patch)
            self.render(rows)
            self.assertEqual(self.page.locator('#machine-EQ-ENV-01').get_attribute('data-state'), 'unknown')
            self.assertTrue(self.page.locator('#simulate-lock').is_disabled())
            self.assertEqual(self.metrics(), ['6', '—', '—', '—'])
        self.render(self.initial, verified=False)
        self.assertEqual(self.page.locator('.machine[data-state=unknown]').count(), 6)

    def test_09_untrusted_strings_remain_text(self):
        payload = '<img src=x onerror="window.injected=true">'
        rows = [dict(row, nombre=payload, area=payload) for row in self.initial]
        self.render(rows)
        self.assertEqual(self.page.locator('#panel-name').inner_text(), payload)
        self.assertEqual(self.page.locator('img').count(), 0)
        self.assertIsNone(self.page.evaluate('window.injected'))

    def test_10_responsive_geometry_and_touch_targets(self):
        for width in (375, 390, 768, 834, 1024, 1280, 1440, 1920):
            self.page.set_viewport_size({'width': width, 'height': 1000})
            geometry = self.page.evaluate('''() => {
              const map = document.querySelector('.plant'), panel = document.querySelector('#detail-panel');
              const m = (map || document.querySelector('#floor')).getBoundingClientRect(), p = panel.getBoundingClientRect();
              return {width:innerWidth, scroll:document.documentElement.scrollWidth,
                map:{x:m.x,y:m.y,right:m.right,bottom:m.bottom}, panel:{x:p.x,y:p.y},
                controls:[...document.querySelectorAll('button,select')].filter(x=>x.getClientRects().length).map(x=>({id:x.id,w:x.getBoundingClientRect().width,h:x.getBoundingClientRect().height}))}; }''')
            self.assertLessEqual(geometry['scroll'], width)
            for control in geometry['controls']:
                self.assertGreaterEqual(control['h'], 44, control)
                self.assertGreaterEqual(control['w'], 44, control)
            if width > 1200:
                self.assertGreaterEqual(geometry['panel']['x'], geometry['map']['right'])
            else:
                self.assertGreaterEqual(geometry['panel']['y'], geometry['map']['bottom'])
            REPORT['viewports'].append(geometry)

    def test_11_reduced_motion_and_large_text(self):
        self.page.emulate_media(reduced_motion='reduce')
        self.assertEqual(self.page.locator('.machine').first.evaluate('(el) => getComputedStyle(el).transitionDuration'), '0s')
        self.page.set_viewport_size({'width': 768, 'height': 1000})
        self.page.evaluate('''() => {
          const values = [...document.querySelectorAll('body, body *')].map(el => [el, parseFloat(getComputedStyle(el).fontSize)]);
          values.forEach(([el, size]) => el.style.setProperty('font-size', `${size * 2}px`, 'important'));
        }''')
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 768)

    def test_12_actual_network_offline_remains_local_demo(self):
        self.context.set_offline(True)
        self.page.locator('#simulate-lock').click()
        self.assertEqual(self.metrics(), ['6', '2', '4', '4'])
        self.assertIn('Simulación local', self.page.locator('#feedback').inner_text())
        self.assertIn('No se consulta la API', self.page.locator('#availability-text').inner_text())
        self.context.set_offline(False)

    def test_13_hash_selects_without_simulating_and_malformed_is_safe(self):
        self.page.goto(self.url + '#EQ-COM-03')
        self.assertEqual(self.page.locator('#panel-code').inner_text(), 'EQ-COM-03')
        self.assertIn('Compresor', self.page.locator('#feedback').inner_text())
        self.assertEqual(self.metrics(), ['6', '2', '4', '3'])
        self.page.evaluate('history.pushState(null,"","#%"); dispatchEvent(new PopStateEvent("popstate"))')
        self.assertTrue(self.page.locator('#empty-panel').is_visible())
        self.page.goto(self.url + '#INVALIDO')
        self.assertEqual(self.metrics(), ['6', '2', '4', '3'])

    def test_14_screenshot_evidence(self):
        for width, name in ((1440, 'escritorio-1440'), (1024, 'tablet-1024'), (390, 'movil-390')):
            self.page.set_viewport_size({'width': width, 'height': 1040})
            self.page.screenshot(path=str(OUT / f'mapa-{name}.png'), full_page=True)
        self.page.set_viewport_size({'width':1440, 'height':1040})
        self.page.locator('#scenario').select_option('offline')
        self.page.screenshot(path=str(OUT / 'mapa-sin-verificar.png'), full_page=True)
        self.page.locator('#scenario').select_option('available')
        self.page.locator('#show-sheet').click()
        self.page.screenshot(path=str(OUT / 'mapa-ficha-local.png'), full_page=True)

    def test_15_direct_file_url(self):
        page = self.context.new_page()
        try:
            page.goto((ROOT / 'mapa-planta.html').as_uri())
            self.assertEqual(page.locator('[data-machine-id]').count(), 6)
            page.locator('#simulate-lock').click()
            self.assertEqual(page.locator('#panel-count').inner_text(), '3')
            REPORT['direct_file'] = 'verified'
        except Exception as error:
            if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(error):
                raise
            REPORT['direct_file'] = 'not_verified_managed_browser_policy'
            self.skipTest('El navegador administrado bloquea file://; comprobar apertura directa en un navegador personal.')
        finally:
            page.close()

class Result(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        REPORT['checks'].append({'test': test._testMethodName, 'status': 'pass'})
    def addFailure(self, test, error):
        super().addFailure(test, error)
        REPORT['checks'].append({'test': test._testMethodName, 'status': 'fail'})
    def addError(self, test, error):
        super().addError(test, error)
        REPORT['checks'].append({'test': test._testMethodName, 'status': 'error'})
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        REPORT['checks'].append({'test': test._testMethodName, 'status': 'skip', 'reason': reason})

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromTestCase(MapTests))
    REPORT.update(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))
    # No tokens ni credenciales; sustituir puerto efímero por un origen estable para la evidencia.
    for request in REPORT['requests']:
        request['url'] = request['url'].replace(MapTests.url, 'http://127.0.0.1:<puerto>/mapa-planta.html')
    (OUT / 'verificacion.json').write_text(json.dumps(REPORT, ensure_ascii=False, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
