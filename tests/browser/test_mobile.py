"""Pruebas de la interfaz real con una API HTTP controlada (sin base de producción)."""
import base64
import copy
import json
import os
import secrets
from pathlib import Path
import socket
import struct
import threading
import time
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

STATIC = Path(os.environ.get('SILBOM_STATIC_ROOT', Path(__file__).resolve().parents[2] / 'src/main/resources/static'))
MACHINE = {'id': 'EQ-ENV-01', 'nombre': 'Equipo de prueba', 'area': 'Taller', 'icono': 'X',
           'bloqueada': False, 'bloqueosActivos': 0, 'horasOperativas': 100, 'fallasCorrectivas': 0, 'mtbf': None}


class Scenario:
    def __init__(self):
        self.machine = copy.deepcopy(MACHINE)
        self.tickets = []
        self.keys = {}
        self.requests = []
        self.events = []
        self.post_fault = None
        self.put_fault = None
        self.reads_fail = False
        self.network_down = False
        self.demo_two_accounts = False
        self.session_role = "SUPERVISOR"
        self.session_status = 200
        self.auth_rejected = False
        self.detail_status = None
        self.lock = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def end_headers(self):
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https: http://localhost:* http://127.0.0.1:*; worker-src 'self'")
        super().end_headers()

    def log_message(self, *_):
        pass

    def reply(self, status, body):
        data = json.dumps(body).encode() if not isinstance(body, bytes) else body
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def drop(self):
        self.close_connection = True
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.connection.close()

    def api(self):
        path = urlsplit(self.path).path.removeprefix('/api/v1')
        state = self.server.scenario
        method = self.command
        auth = self.headers.get('Authorization', '')
        username = base64.b64decode(auth[6:]).decode().split(':', 1)[0] if auth.startswith('Basic ') else None
        key = self.headers.get('Idempotency-Key')
        state.requests.append({'method': method, 'path': path, 'key': key, 'authenticated': bool(auth)})
        if method == 'GET':
            if state.reads_fail:
                return self.reply(503, {'mensaje': 'Lectura temporalmente no disponible'})
            if path == '/maquinas':
                return self.reply(200, [state.machine])
            if path.startswith('/maquinas/'):  # Público, como GET /api/v1/maquinas/** en SecurityConfig.
                if state.detail_status:
                    return self.reply(state.detail_status, {'mensaje': 'Rechazado por prueba'})
                found = path.split('/')[2] == state.machine['id']
                return self.reply(200 if found else 404, state.machine if found else {'mensaje': 'No encontrada'})
            if not username:
                return self.reply(401, {'mensaje': 'Credencial inválida'})
            if state.auth_rejected:
                return self.reply(401, {'mensaje': 'Credencial inválida'})
            if path == '/sesion':
                if state.session_status != 200:
                    return self.reply(state.session_status, {'mensaje': 'No se pudo verificar la sesión'})
                return self.reply(200, {'id': 2 if state.session_role == 'TECNICO' else 1, 'username': username, 'nombre': 'Identidad de prueba', 'rol': state.session_role, 'modoDosCuentas': state.demo_two_accounts, 'identidadesSoloLectura': state.demo_two_accounts})
            if path == '/tecnicos':
                return self.reply(200, [{'id': 1, 'username': username, 'nombre': 'Supervisor', 'rol': 'SUPERVISOR'}])
            if path == '/bloqueos':
                return self.reply(200, state.tickets)
            if path.startswith('/bloqueos/'):
                ticket = next((t for t in state.tickets if t['id'] == int(path.split('/')[2])), None)
                return self.reply(200 if ticket else 404, ticket)
            return self.reply(404, {})
        if not username:
            return self.reply(401, {'mensaje': 'Credencial inválida'})
        fault = state.post_fault if method == 'POST' else state.put_fault
        if method == 'POST':
            state.post_fault = None
        else:
            state.put_fault = None
        fault = fault or {}
        if fault.get('delay'):
            time.sleep(fault['delay'])
        if fault.get('drop_before'):
            return self.drop()
        if 'status' in fault and fault['status'] < 500:
            return self.reply(fault['status'], {'mensaje': 'Rechazado por prueba'})
        if fault.get('malformed'):
            return self.reply(201 if method == 'POST' else 200, b'<html>proxy</html>')
        if fault.get('incomplete'):
            return self.reply(201 if method == 'POST' else 200, {})
        with state.lock:
            if method == 'POST':
                payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
                if (username, key) in state.keys:
                    ticket = state.keys[username, key]
                else:
                    ticket = dict(payload, id=len(state.tickets) + 1, estado='ACTIVO', nombreTecnico=username,
                                  tecnicoId=1, horaInicio='2026-11-13T12:00:00', notasAuditoria=payload.get('notasConfidenciales'))
                    state.tickets.append(ticket)
                    state.keys[username, key] = ticket
                    state.machine['bloqueosActivos'] += 1
                    state.machine['bloqueada'] = True
                    state.events.append('CREADO')
                status = 201
            else:
                ticket = next(t for t in state.tickets if t['id'] == int(path.split('/')[2]))
                if ticket['estado'] == 'CERRADO':
                    return self.reply(409, {'mensaje': 'Ya cerrado'})
                ticket.update(estado='CERRADO', duracionMinutos=1)
                state.machine['bloqueosActivos'] -= 1
                state.machine['bloqueada'] = state.machine['bloqueosActivos'] > 0
                state.events.append('LIBERADO')
                status = 200
            if fault.get('drop_after'):
                return self.drop()
            if fault.get('fail_reads'):
                state.reads_fail = True
            return self.reply(fault.get('status', status), ticket)

    def do_GET(self):
        if self.server.scenario.network_down:
            return self.drop()
        if self.path.startswith('/api/v1/'):
            return self.api()
        return super().do_GET()

    def do_POST(self):
        return self.api()

    def do_PUT(self):
        return self.api()


class MobileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.server.daemon_threads = True
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw = sync_playwright().start()
        cls.engine = os.environ.get('SILBOM_BROWSER', 'chromium')
        launch = {}
        if cls.engine == 'chromium':
            launch['args'] = ['--no-sandbox', '--disable-dev-shm-usage']
            if os.environ.get('CHROMIUM_PATH'):
                launch['executable_path'] = os.environ['CHROMIUM_PATH']
        cls.browser = getattr(cls.pw, cls.engine).launch(**launch)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.state = Scenario()
        self.server.scenario = self.state
        device = dict(self.pw.devices['iPhone 13']) if self.engine == 'webkit' else dict(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True)
        device.pop('default_browser_type', None)
        self.context = self.browser.new_context(**device,
            service_workers='allow' if self._testMethodName.startswith('test_pwa_') else 'block')
        self.page = self.context.new_page()
        self.page.set_default_timeout(5000)
        self.errors = []
        self.page.on('pageerror', lambda err: self.errors.append(str(err)))
        response = self.page.goto(self.origin + '/app/index.html', wait_until='networkidle')
        self.assertEqual(200, response.status)
        self.page.wait_for_function('() => typeof performLogin === "function" && typeof AppState === "object"')

    def tearDown(self):
        self.context.close()
        self.assertEqual([], self.errors)

    def login(self):
        self.page.locator('#mnav-tecnicos').click()
        self.page.locator('#mobile-auth-user').fill('supervisor-test')
        self.page.locator('#mobile-auth-pass').fill('browser-test-password')
        self.page.locator('form[onsubmit*="loginFromMobilePanel"] button[type=submit]' ).click()
        self.page.wait_for_function('() => AppState.auth?.rol === "SUPERVISOR"')
        self.page.locator('#mnav-operar').click()

    def prepare(self):
        self.login()
        self.page.locator('#manual-machine-select').select_option('EQ-ENV-01')
        self.page.locator('#card-type-preventive').click()
        self.page.locator('#check-padlock').check()

    def create(self):
        self.prepare()
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('confirmado por el servidor')

    def assert_client_active(self):
        self.assertTrue(self.page.evaluate('AppState.machines[0].isLocked'))
        self.assertEqual('ACTIVO', self.page.evaluate('AppState.tickets[0].estado'))

    def test_supervisor_console_uses_verified_role_and_freezes_identities(self):
        self.state.demo_two_accounts=True
        self.page.goto(self.origin+'/index.html',wait_until='networkidle')
        self.assertTrue(self.page.evaluate('(s)=>performLogin("supervisor-test",s)',secrets.token_urlsafe(24)))
        self.page.evaluate('openTechManagementModal()')
        expect(self.page.locator('#supervisor-create-tech-form')).to_be_hidden()
        expect(self.page.locator('#supervisor-tech-table-body button').first).to_be_disabled()
        before=len(self.state.requests)
        self.page.evaluate('createTechnicianFromForm()')
        self.page.evaluate('deactivateTechnician(1,"supervisor-test")')
        self.assertEqual(before,len(self.state.requests))
        self.page.evaluate('logoutOperator()')
        self.assertIsNone(self.page.evaluate('AppState.auth'))
        self.state.session_role='TECNICO'
        self.assertTrue(self.page.evaluate('(s)=>performLogin("tecnico-prueba",s)',secrets.token_urlsafe(24)))
        link=urlsplit(self.page.locator('#role-interface-link').get_attribute('href'))
        self.assertEqual('/app/',link.path)
        self.assertNotIn('password',link.query.lower())
        self.assertEqual('TECNICO',self.page.evaluate('AppState.auth.rol'))

    def test_role_is_authoritative_and_technician_gets_operational_navigation(self):
        self.state.session_role = 'TECNICO'
        result = self.page.evaluate('(s) => performLogin("tecnico-prueba", s)', secrets.token_urlsafe(24))
        self.assertTrue(result)
        self.assertEqual('TECNICO', self.page.evaluate('AppState.auth.rol'))
        self.assertEqual(2, self.page.evaluate('AppState.auth.id'))
        expect(self.page.locator('#role-interface-link')).to_have_attribute('href', self.origin+'/app/')
        self.assertFalse(any(r['path']=='/tecnicos' for r in self.state.requests))
        self.page.locator('#mnav-tecnicos').click()
        expect(self.page.locator('#mobile-create-tech-form')).to_be_hidden()

    def test_unverified_role_never_creates_a_session(self):
        for role, status in [('DESCONOCIDO',200),('TECNICO',403),('SUPERVISOR',503)]:
            self.state.session_role, self.state.session_status = role,status
            self.assertFalse(self.page.evaluate('(s) => performLogin("prueba",s)', secrets.token_urlsafe(24)))
            self.assertIsNone(self.page.evaluate('AppState.auth'))
            self.assertEqual([],self.page.evaluate('AppState.tickets'))

    def test_demo_identity_form_disabled_and_direct_handler_does_not_post(self):
        self.state.demo_two_accounts = True
        self.login()
        self.page.locator('#mnav-tecnicos').click()
        expect(self.page.locator('#mobile-create-tech-form')).to_be_hidden()
        expect(self.page.locator('#identity-access-note')).to_contain_text('solo lectura')
        before=len(self.state.requests)
        self.page.evaluate('createTechnicianFromForm()')
        self.assertEqual(before,len(self.state.requests))

    def test_logout_clears_credentials_even_with_uncertain_operation(self):
        self.prepare()
        self.state.post_fault={'drop_before':True}
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Alta sin confirmar')
        self.page.evaluate('logoutOperator()')
        self.assertIsNone(self.page.evaluate('AppState.auth'))
        self.assertIsNotNone(self.page.evaluate('AppState.pendingOperation'))
        self.assertEqual([],self.page.evaluate('AppState.tickets'))
        self.assertEqual('',self.page.locator('#mobile-auth-pass').input_value())
        self.assertEqual('[]',self.page.evaluate('JSON.stringify(Object.keys(localStorage).filter(k=>/auth|password|credential/i.test(k)))'))

    def test_revoked_session_and_pagehide_clear_memory(self):
        self.login()
        self.state.auth_rejected=True
        self.page.evaluate('apiFetch("/sesion")')
        self.assertIsNone(self.page.evaluate('AppState.auth'))
        expect(self.page.locator('#btn-submit-lock')).to_be_disabled()
        self.state.auth_rejected=False
        self.login()
        self.page.evaluate('window.dispatchEvent(new PageTransitionEvent("pagehide",{persisted:true}))')
        self.assertIsNone(self.page.evaluate('AppState.auth'))
        self.assertEqual([],self.page.evaluate('AppState.tickets'))

    def test_offline_creation_has_no_local_success(self):
        self.prepare()
        self.state.post_fault = {'drop_before': True}
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Alta sin confirmar')
        self.assertEqual([], self.state.tickets)
        self.assertEqual(0, self.page.evaluate('AppState.tickets.length'))
        self.assertFalse(self.page.evaluate('AppState.machines[0].isLocked'))
        expect(self.page.locator('#tech-step-2')).to_be_visible()

    def test_offline_release_preserves_active_ticket(self):
        self.create()
        self.state.put_fault = {'drop_before': True}
        self.page.locator('#btn-unlock-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Liberación sin confirmar')
        self.assert_client_active()
        self.assertEqual('ACTIVO', self.state.tickets[0]['estado'])

    def test_lost_create_response_retries_same_key_once(self):
        self.prepare()
        self.state.post_fault = {'drop_after': True}
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Alta sin confirmar')
        self.assertEqual(1, len(self.state.tickets))
        self.assertEqual(0, self.page.evaluate('AppState.tickets.length'))
        self.page.locator('#btn-retry-operation').click()
        expect(self.page.locator('#operation-status')).to_contain_text('confirmado por el servidor')
        posts = [r for r in self.state.requests if r['method'] == 'POST']
        self.assertEqual(2, len(posts))
        self.assertEqual(posts[0]['key'], posts[1]['key'])
        self.assertEqual(['CREADO'], self.state.events)
        self.assertEqual(1, self.state.machine['bloqueosActivos'])

    def test_double_submit_sends_only_one_request(self):
        self.prepare()
        self.state.post_fault = {'delay': .2}
        self.page.locator('#btn-submit-lock').click(click_count=2)
        expect(self.page.locator('#operation-status')).to_contain_text('confirmado por el servidor')
        self.assertEqual(1, sum(r['method'] == 'POST' for r in self.state.requests))
        self.assertEqual(1, self.state.machine['bloqueosActivos'])

    def test_lost_release_response_reconciles_409_with_server(self):
        self.create()
        self.state.put_fault = {'drop_after': True}
        self.page.locator('#btn-unlock-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Liberación sin confirmar')
        self.assert_client_active()
        self.assertEqual('CERRADO', self.state.tickets[0]['estado'])
        self.page.locator('#btn-retry-operation').click()
        expect(self.page.locator('#operation-status')).to_contain_text('cero bloqueos digitales')
        self.assertEqual(['CREADO', 'LIBERADO'], self.state.events)
        self.assertEqual(0, self.state.machine['bloqueosActivos'])
        self.assertEqual('CERRADO', self.page.evaluate('AppState.tickets[0].estado'))

    def test_release_keeps_machine_blocked_with_second_ticket(self):
        self.create()
        other = dict(self.state.tickets[0], id=2, tecnicoId=2, nombreTecnico='otro-tecnico')
        self.state.tickets.append(other)
        self.state.machine.update(bloqueosActivos=2, bloqueada=True)
        self.page.locator('#btn-unlock-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('sigue bloqueada (1 activo(s))')
        self.assertTrue(self.page.evaluate('AppState.machines[0].isLocked'))
        self.assertEqual(1, self.state.machine['bloqueosActivos'])

    def test_confirmed_release_with_failed_refresh_never_claims_machine_free(self):
        self.create()
        self.state.put_fault = {'fail_reads': True}
        self.page.locator('#btn-unlock-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('CERRADO confirmado. Estado del equipo sin verificar')
        self.assertTrue(self.page.evaluate('AppState.machines[0].isLocked'))
        self.assertEqual('CERRADO', self.page.evaluate('AppState.tickets[0].estado'))

    def test_http_rejections_never_confirm_creation(self):
        self.prepare()
        for status in (401, 403, 409):
            with self.subTest(status=status):
                if not self.page.evaluate('Boolean(AppState.auth)'):
                    self.login()
                self.state.post_fault = {'status': status}
                self.page.locator('#btn-submit-lock').click()
                expect(self.page.locator('#operation-status')).to_contain_text(f'El servidor respondió {status}')
                self.assertEqual([], self.state.tickets)
                self.assertEqual(0, self.page.evaluate('AppState.tickets.length'))

    def test_500_after_commit_is_uncertain_and_retry_does_not_duplicate(self):
        self.prepare()
        self.state.post_fault = {'status': 500}
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Alta sin confirmar')
        self.page.locator('#btn-retry-operation').click()
        expect(self.page.locator('#operation-status')).to_contain_text('confirmado por el servidor')
        self.assertEqual(1, len(self.state.tickets))

    def test_invalid_success_body_never_confirms_creation(self):
        self.prepare()
        self.state.post_fault = {'incomplete': True}
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Alta sin confirmar')
        self.assertEqual(0, self.page.evaluate('AppState.tickets.length'))

    def test_malformed_json_is_uncertain(self):
        self.prepare()
        self.state.post_fault = {'malformed': True}
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Alta sin confirmar')
        self.assertEqual([], self.state.tickets)

    def test_timeout_can_retry_without_duplicate(self):
        self.prepare()
        self.page.evaluate('''() => {
          const original = SilbomHttp.request;
          window.originalRequest = original;
          SilbomHttp.request = (endpoint, opts) => original(endpoint, {...opts, timeoutMs: 50});
        }''')
        self.state.post_fault = {'delay': .2}
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Alta sin confirmar')
        self.page.evaluate('SilbomHttp.request = window.originalRequest')
        self.page.wait_for_timeout(250)
        self.page.locator('#btn-retry-operation').click()
        expect(self.page.locator('#operation-status')).to_contain_text('confirmado por el servidor')
        self.assertEqual(1, len(self.state.tickets))

    def test_deep_link_identifies_only_and_does_not_change_api_origin(self):
        self.page.goto(self.origin + '/app/?maquina=EQ-ENV-01&api=https://attacker.invalid', wait_until='networkidle')
        expect(self.page.locator('#tech-step-2')).to_be_visible()
        self.assertEqual('EQ-ENV-01', self.page.locator('#form-machine-code').inner_text())
        self.assertEqual('/api/v1', self.page.evaluate('getApiBaseUrl()'))
        self.assertFalse(any(r['method'] != 'GET' for r in self.state.requests))
        expect(self.page.locator('#btn-submit-lock')).to_be_disabled()

    def test_invalid_and_unknown_links_do_not_select_another_machine(self):
        for machine in ('bad-code', 'EQ-UNKNOWN-01', 'EQ-ZZ-99', ''):
            with self.subTest(machine=machine):
                self.page.goto(self.origin + '/app/?maquina=' + machine, wait_until='networkidle')
                expect(self.page.locator('#tech-step-1')).to_be_visible()
                self.assertIsNone(self.page.evaluate('AppState.selectedMachineId'))
                self.assertFalse(any(r['method'] != 'GET' for r in self.state.requests))

    def test_non_default_port_and_https_resolution(self):
        self.assertEqual('/api/v1', self.page.evaluate('getApiBaseUrl()'))
        self.assertEqual('https://plant.example:8443/api/v1', self.page.evaluate("SilbomHttp.baseUrl('https://plant.example:8443')"))
        self.assertFalse(self.page.evaluate("SilbomHttp.allowsCredentials('http://192.168.1.50:8080')"))
        self.page.goto(self.origin + '/', wait_until='networkidle')
        self.assertEqual('/api/v1', self.page.evaluate('API_BASE_URL'))
        self.assertTrue(self.page.evaluate('AppState.apiOnline'))

    def test_supervisor_does_not_present_failed_catalog_as_operational(self):
        self.page.goto(self.origin + '/', wait_until='networkidle')
        self.state.reads_fail = True
        self.page.evaluate('() => runSupervisorPollTick()')
        expect(self.page.locator('#kpi-active-count')).to_contain_text('Sin verificar')
        expect(self.page.locator('#kpi-plant-tag')).to_contain_text('Estado actual sin verificar')

    def test_mobile_viewports_and_long_machine_name(self):
        self.state.machine['nombre'] = 'Equipo industrial ' + 'X' * 80
        self.page.reload(wait_until='networkidle')
        self.page.locator('#manual-machine-select').select_option('EQ-ENV-01')
        for width in (320, 360, 390, 768):
            with self.subTest(width=width):
                self.page.set_viewport_size({'width': width, 'height': 640})
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                expect(self.page.locator('#btn-submit-lock')).to_be_visible()

    def test_ios_manual_install_and_apple_icon(self):
        self.page.evaluate("() => Object.defineProperty(navigator, 'userAgent', {value:'iPhone Safari', configurable:true})")
        self.page.locator('#btn-open-install-modal').click()
        expect(self.page.locator('#install-app-modal')).to_contain_text('Compartir → Añadir a pantalla de inicio')
        expect(self.page.locator('#btn-native-pwa-install')).to_be_hidden()
        self.assertEqual('SILBOM', self.page.locator('meta[name="apple-mobile-web-app-title"]').get_attribute('content'))
        icon = self.page.locator('link[rel="apple-touch-icon"]').get_attribute('href')
        response = self.page.request.get(self.origin + '/app/' + icon.removeprefix('./'))
        self.assertEqual((180, 180), struct.unpack('>II', response.body()[16:24]))
        self.page.evaluate("() => Object.defineProperty(navigator, 'standalone', {value:true, configurable:true})")
        self.page.evaluate('() => openInstallModal()')
        expect(self.page.locator('#pwa-install-status')).to_contain_text('ya está abierta')

    def test_online_event_requires_api_verification(self):
        self.prepare()
        self.page.evaluate("() => window.dispatchEvent(new Event('offline'))")
        expect(self.page.locator('#btn-submit-lock')).to_be_disabled()
        self.state.reads_fail = True
        self.page.evaluate("() => window.dispatchEvent(new Event('online'))")
        expect(self.page.locator('#operation-status')).to_contain_text('No se pudo actualizar')
        self.assertFalse(self.page.evaluate('AppState.apiOnline'))
        self.state.reads_fail = False
        self.page.evaluate("() => window.dispatchEvent(new Event('online'))")
        self.page.wait_for_function('() => AppState.apiOnline && !AppState.refreshing')
        self.assertFalse(any(r['method'] != 'GET' for r in self.state.requests))

    def test_ios_restore_does_not_resend_pending_operation(self):
        self.prepare()
        self.state.post_fault = {'drop_after': True}
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Alta sin confirmar')
        key = self.page.evaluate('AppState.pendingOperation.key')
        self.page.evaluate("() => window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted:true}))")
        self.page.wait_for_function('() => !AppState.refreshing && AppState.apiOnline')
        self.assertEqual(key, self.page.evaluate('AppState.pendingOperation.key'))
        self.assertEqual(1, sum(r['method'] == 'POST' for r in self.state.requests))
        expect(self.page.locator('#btn-retry-operation')).to_be_visible()

    def test_pwa_manifest_icons_and_offline_deep_link_shell(self):
        self.page.evaluate('() => navigator.serviceWorker.ready')
        self.page.reload(wait_until='networkidle')
        self.page.wait_for_function('() => navigator.serviceWorker.controller !== null')
        manifest = self.page.request.get(self.origin + '/app/manifest.webmanifest').json()
        self.assertEqual('/app/', manifest['scope'])
        for icon in manifest['icons']:
            response = self.page.request.get(self.origin + '/app/' + icon['src'])
            self.assertEqual(200, response.status)
            width, height = struct.unpack('>II', response.body()[16:24])
            self.assertEqual(icon['sizes'], f'{width}x{height}')
        # Un corte HTTP real permite comprobar el SW también en WebKit; el modo
        # offline del protocolo de automatización puede impedir la navegación antes del SW.
        self.state.network_down = True
        self.page.goto(self.origin + '/app/?maquina=EQ-ENV-01', wait_until='networkidle')
        expect(self.page.locator('#api-connection-badge')).to_contain_text('estado sin verificar')
        self.assertEqual([], self.page.evaluate('AppState.machines'))
        self.assertEqual('EQ-ENV-01', self.page.evaluate('AppState.pendingMachineLink'))
        keys = self.page.evaluate('''async () => (await Promise.all((await caches.keys()).map(async key =>
          (await (await caches.open(key)).keys()).map(req => ({url:req.url, auth:req.headers.has('Authorization')}))))).flat()''')
        self.assertFalse(any('/api/' in k['url'] or k['auth'] for k in keys))
        self.state.network_down = False
        self.page.locator('button[onclick="refreshConnection()"]' ).click()
        expect(self.page.locator('#tech-step-2')).to_be_visible()
        self.assertFalse(any(r['method'] != 'GET' for r in self.state.requests))

    # ---- Identificación por QR (puente Android simulado) y NFC sobre la misma lógica ----
    QR_BRIDGE = 'window.SilbomAndroidQr = {startScan(){ window.__qrStarts = (window.__qrStarts || 0) + 1; }}'
    NFC_BRIDGE = 'window.SilbomAndroidNfc = {startScan(){}, cancelScan(){}}'

    def detail_requests(self):
        return [r for r in self.state.requests if r['path'].startswith('/maquinas/')]

    def start_qr(self):
        self.page.evaluate(self.QR_BRIDGE)
        self.page.locator('#btn-start-qr').click()
        expect(self.page.locator('#qr-scan-status')).to_contain_text('Apunta la cámara al código QR de la máquina')
        expect(self.page.locator('#btn-start-qr')).to_be_disabled()
        self.assertEqual(1, self.page.evaluate('window.__qrStarts'))

    def test_qr_valid_code_opens_machine_sheet_from_api_without_writes(self):
        self.start_qr()
        self.page.evaluate('window.SilbomQr.onRead("EQ-ENV-01")')
        expect(self.page.locator('#qr-scan-status')).to_contain_text('Máquina encontrada: EQ-ENV-01 · Equipo de prueba')
        expect(self.page.locator('#tech-step-2')).to_be_visible()
        expect(self.page.locator('#form-machine-code')).to_have_text('EQ-ENV-01')
        expect(self.page.locator('#form-machine-name')).to_have_text('Equipo de prueba')
        self.assertEqual(['/maquinas/EQ-ENV-01'], [r['path'] for r in self.detail_requests()])
        self.assertEqual([], [r for r in self.state.requests if r['method'] != 'GET'])
        self.assertEqual([], self.state.events)
        expect(self.page.locator('#btn-start-qr')).to_be_enabled()

    def test_qr_duplicate_reads_only_query_once(self):
        self.start_qr()
        self.page.evaluate('Promise.all([window.SilbomQr.onRead("EQ-ENV-01"), window.SilbomQr.onRead("EQ-ENV-01")])')
        self.assertEqual(1, len(self.detail_requests()))
        self.page.evaluate('window.SilbomQr.onRead("EQ-ENV-01")')  # Sin escaneo solicitado: se ignora.
        self.assertEqual(1, len(self.detail_requests()))

    def test_qr_unknown_machine_unauthorized_and_offline_never_open_sheet(self):
        cases = [('EQ-XYZ-99', None, False, 'Máquina no registrada en SILBOM.'),
                 ('EQ-ENV-01', 401, False, 'No autorizado para consultar esta máquina.'),
                 ('EQ-ENV-01', 403, False, 'No autorizado para consultar esta máquina.'),
                 ('EQ-ENV-01', None, True, 'No se pudo conectar con el servidor.')]
        for code, status, offline, message in cases:
            with self.subTest(code=code, status=status, offline=offline):
                self.state.detail_status, self.state.network_down = status, offline
                self.page.evaluate('window.__qrStarts = 0')
                self.start_qr()
                self.page.evaluate('(c) => window.SilbomQr.onRead(c)', code)
                expect(self.page.locator('#qr-scan-status')).to_have_text(message)
                expect(self.page.locator('#operation-status')).to_contain_text(message)
                expect(self.page.locator('#tech-step-2')).to_be_hidden()
                expect(self.page.locator('#btn-start-qr')).to_be_enabled()
        self.state.network_down = False
        self.assertEqual([], [r for r in self.state.requests if r['method'] != 'GET'])

    def test_qr_invalid_content_is_rejected_without_requests(self):
        for value in ['HOLA', 'EQ-ENV', 'https://google.com', 'http://192.168.1.50:8080', '', 'eq-com-03']:
            with self.subTest(value=value):
                self.page.evaluate('window.__qrStarts = 0')
                self.start_qr()
                self.page.evaluate('(v) => window.SilbomQr.onRead(v)', value)
                expect(self.page.locator('#qr-scan-status')).to_contain_text('identificador de máquina SILBOM válido')
        self.assertEqual([], self.detail_requests())
        expect(self.page.locator('#tech-step-2')).to_be_hidden()

    def test_qr_native_errors_are_explained_and_allow_retry(self):
        cases = {'cancelled': 'Escaneo QR cancelado.', 'url_not_allowed': 'no se abrió nada',
                 'empty_code': 'El QR está vacío.', 'camera_permission_denied': 'Permite el acceso a la cámara',
                 'camera_unavailable': 'La cámara no está disponible', 'scanner_failed': 'Error interno del lector QR',
                 'scanner_unavailable': 'El lector QR no está disponible'}
        for reason, message in cases.items():
            with self.subTest(reason=reason):
                self.page.evaluate('window.__qrStarts = 0')
                self.start_qr()
                self.page.evaluate('(r) => window.SilbomQr.onError(r)', reason)
                expect(self.page.locator('#qr-scan-status')).to_contain_text(message)
                expect(self.page.locator('#btn-start-qr')).to_be_enabled()
        self.assertEqual([], self.detail_requests())

    def test_qr_without_android_bridge_explains_and_keeps_manual_selection(self):
        self.page.locator('#btn-start-qr').click()
        expect(self.page.locator('#qr-scan-status')).to_contain_text('aplicación Android instalada')
        self.page.locator('#manual-machine-select').select_option('EQ-ENV-01')
        expect(self.page.locator('#form-machine-code')).to_have_text('EQ-ENV-01')

    def test_qr_blocked_while_lock_operation_is_unconfirmed(self):
        self.prepare()
        self.state.post_fault = {'drop_before': True}
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('Alta sin confirmar')
        self.page.evaluate(self.QR_BRIDGE)
        self.page.evaluate('startNativeQrScan()')
        self.assertIsNone(self.page.evaluate('window.__qrStarts ?? null'))

    def test_nfc_still_identifies_machine_through_shared_flow(self):
        self.page.evaluate(self.NFC_BRIDGE)
        self.page.locator('#btn-start-nfc').click()
        expect(self.page.locator('#nfc-scan-status')).to_contain_text('Acerca el teléfono')
        self.page.evaluate('window.SilbomNfc.onRead("EQ-ENV-01")')
        expect(self.page.locator('#nfc-scan-status')).to_have_text('Máquina EQ-ENV-01 verificada desde el servidor.')
        expect(self.page.locator('#form-machine-code')).to_have_text('EQ-ENV-01')
        self.page.evaluate('cancelToStep1()')
        self.page.locator('#btn-start-nfc').click()
        self.page.evaluate('window.SilbomNfc.onRead("EQ-XYZ-99")')
        expect(self.page.locator('#operation-status')).to_contain_text('Máquina no registrada en SILBOM.')
        self.assertEqual(['/maquinas/EQ-ENV-01', '/maquinas/EQ-XYZ-99'], [r['path'] for r in self.detail_requests()])

    def test_qr_identified_machine_can_still_be_locked_and_released_with_session(self):
        self.login()
        self.start_qr()
        self.page.evaluate('window.SilbomQr.onRead("EQ-ENV-01")')
        expect(self.page.locator('#form-machine-code')).to_have_text('EQ-ENV-01')
        self.assertEqual([], self.state.events)  # Identificar no crea bloqueos.
        self.page.locator('#card-type-preventive').click()
        self.page.locator('#check-padlock').check()
        self.page.locator('#btn-submit-lock').click()
        expect(self.page.locator('#operation-status')).to_contain_text('confirmado por el servidor')
        self.assertEqual(['CREADO'], self.state.events)


if __name__ == '__main__':
    unittest.main()
