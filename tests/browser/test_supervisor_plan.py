"""Plano real de supervisión y sincronización HTTP con la interfaz móvil; sin BD productiva."""
import base64
import copy
import json
import os
from pathlib import Path
import secrets
import threading
import unittest
from urllib.parse import urlsplit
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright, expect
from test_mobile import Handler, Scenario, MACHINE

CATALOG = [
    {'id':'EQ-COM-03','nombre':'Compresor de Tornillo','area':'Sala de Máquinas','mtbf':718.5},
    {'id':'EQ-MEZ-01','nombre':'Mezclador Industrial de Cinta','area':'Área de Preparación','mtbf':715},
    {'id':'EQ-EXT-02','nombre':'Extrusora de Polímeros','area':'Área de Moldeo','mtbf':171.3},
    {'id':'EQ-PR-04','nombre':'Prensa Hidráulica 200T','area':'Área de Estampado','mtbf':356},
    {'id':'EQ-TR-01','nombre':'Cinta Transportadora Principal','area':'Logística y Despacho','mtbf':None},
]
class PlanHandler(Handler):
    def api(self):
        path=urlsplit(self.path).path.removeprefix('/api/v1');state=self.server.scenario
        if self.command=='GET' and path in ('/maquinas','/sesion'):
            auth=self.headers.get('Authorization','')
            username=base64.b64decode(auth[6:]).decode().split(':',1)[0] if auth.startswith('Basic ') else None
            state.requests.append({'method':'GET','path':path,'authenticated':bool(auth)})
            if state.reads_fail:return self.reply(503,{'mensaje':'No disponible'})
            if path=='/sesion':
                if not username or state.auth_rejected:return self.reply(401,{})
                if state.session_status!=200:return self.reply(state.session_status,{})
                role=state.role_override or ('SUPERVISOR' if username=='supervisor-test' else 'TECNICO')
                identity=2 if username=='tecnico-dos' else 1
                return self.reply(200,{'id':identity,'username':username,'nombre':'Identidad de prueba','rol':role,'modoDosCuentas':False,'identidadesSoloLectura':False})
            if state.bad_catalog is not None:return self.reply(200,state.bad_catalog)
            return self.reply(200,[copy.deepcopy(state.machine)]+copy.deepcopy(state.catalog))
        return super().api()

class SupervisorPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),PlanHandler);cls.server.daemon_threads=True
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.origin=f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw=sync_playwright().start();cls.engine=os.environ.get('SILBOM_BROWSER','chromium')
        launch={}
        if cls.engine=='chromium':
            launch['args']=['--no-sandbox','--disable-dev-shm-usage']
            if os.environ.get('CHROMIUM_PATH'):launch['executable_path']=os.environ['CHROMIUM_PATH']
        cls.browser=getattr(cls.pw,cls.engine).launch(**launch)
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def setUp(self):
        self.state=Scenario();self.state.role_override=None;self.state.bad_catalog=None
        self.state.catalog=[dict(row,bloqueada=False,bloqueosActivos=0) for row in CATALOG]
        self.state.machine=dict(MACHINE,nombre='Envasadora Rotativa Automática',area='Línea de Envasado 1',bloqueada=True,bloqueosActivos=2,mtbf=233.8)
        self.state.tickets=[{'id':i,'maquinaId':'EQ-ENV-01','tecnicoId':i,'nombreTecnico':f'tecnico-{i}',
                             'estado':'ACTIVO','tipoIntervencion':'PREVENTIVA','motivo':'Prueba','confirmacionCandadoDs594':True,
                             'horaInicio':'2026-11-13T12:00:00'} for i in (1,2)]
        self.server.scenario=self.state
        self.context=self.browser.new_context(viewport={'width':1440,'height':1000},service_workers='block')
        self.page=self.context.new_page();self.page.set_default_timeout(7000);self.errors=[]
        self.page.on('pageerror',lambda error:self.errors.append(str(error)))
        self.page.goto(self.origin+'/index.html',wait_until='networkidle')
    def tearDown(self):
        self.context.close();self.assertEqual(self.errors,[])
    def login(self,username='supervisor-test',page=None):
        page=page or self.page
        self.assertTrue(page.evaluate('(args)=>performLogin(args.user,args.password)',{'user':username,'password':secrets.token_urlsafe(24)}))
    def open_plan(self):
        self.login();self.page.locator('#supervisor-tab-plan').click()
        expect(self.page.locator('#supervisor-plan-panel')).to_be_visible()
        self.page.locator('#point-EQ-ENV-01').wait_for()
    def metrics(self):
        return [self.page.locator('#stat-'+key).inner_text() for key in ('total','locked','free','locks')]
    def assert_gray(self):
        expect(self.page.locator('.machine-marker[data-state="unknown"]')).to_have_count(6)
        self.assertEqual(self.metrics(),['6','—','—','—'])
        expect(self.page.locator('#detail-count')).to_have_text('Sin verificar')
        expect(self.page.locator('#detail-mtbf')).to_have_text('Sin verificar')

    def test_role_verified_supervisor_only_and_logout_purges_plan(self):
        expect(self.page.locator('#supervisor-view-tabs')).to_be_hidden()
        self.assertFalse(self.page.evaluate('setSupervisorSection("plan")'))
        self.login('tecnico-uno');expect(self.page.locator('#supervisor-view-tabs')).to_be_hidden()
        self.assertFalse(self.page.evaluate('setSupervisorSection("plan")'))
        self.page.evaluate('logoutOperator()');self.open_plan()
        self.assertEqual(self.metrics(),['6','1','5','2'])
        self.page.evaluate('logoutOperator()')
        expect(self.page.locator('#supervisor-plan-panel')).to_be_hidden()
        self.assertEqual(self.page.locator('.machine-marker').count(),0)
        self.assertIsNone(self.page.evaluate('AppState.auth'))
        self.open_plan();expect(self.page.locator('.machine-marker')).to_have_count(6)
        self.page.evaluate('dispatchEvent(new PageTransitionEvent("pagehide"))')
        expect(self.page.locator('#supervisor-view-tabs')).to_be_hidden()
        self.assertEqual(self.page.locator('.machine-marker').count(),0)

    def test_unverified_role_cannot_open_plan(self):
        for role,status in [('DESCONOCIDO',200),('SUPERVISOR',403),('SUPERVISOR',503)]:
            self.state.role_override=role;self.state.session_status=status
            self.assertFalse(self.page.evaluate('(password)=>performLogin("supervisor-test",password)',secrets.token_urlsafe(24)))
            self.assertFalse(self.page.evaluate('setSupervisorSection("plan")'))
            expect(self.page.locator('#supervisor-view-tabs')).to_be_hidden()

    def test_real_catalog_selection_analysis_and_read_only_controls(self):
        self.open_plan();before=len(self.state.requests)
        self.page.locator('#point-EQ-PR-04').click()
        expect(self.page.locator('#detail-name')).to_have_text('Prensa Hidráulica 200T')
        self.assertEqual(self.page.evaluate('AppState.selectedMachineId'),'EQ-PR-04')
        self.page.locator('#open-analysis').click()
        expect(self.page.locator('#supervisor-overview-panel')).to_be_visible()
        expect(self.page.locator('#mtbf-machine-name')).to_contain_text('EQ-PR-04')
        expect(self.page.locator('.machine-status-card[aria-pressed="true"]')).to_contain_text('EQ-PR-04')
        self.page.locator('#supervisor-tab-plan').click()
        expect(self.page.locator('#point-EQ-PR-04')).to_have_attribute('aria-pressed','true')
        self.assertEqual(before,len(self.state.requests),'Navegar no debe consultar ni escribir en la API')
        self.assertEqual(self.page.locator('[data-demo-count],#scenario,.demo-panel').count(),0)
        self.assertFalse(any(r['method']!='GET' for r in self.state.requests))

    def test_mobile_releases_are_reflected_after_poll_and_preserve_multiloto(self):
        self.open_plan()
        for username,remaining in [('tecnico-uno',1),('tecnico-dos',0)]:
            mobile=self.context.new_page();mobile.set_default_timeout(7000);mobile.on('pageerror',lambda error:self.errors.append(str(error)))
            mobile.goto(self.origin+'/app/index.html',wait_until='networkidle');self.login(username,mobile)
            mobile.locator('#mnav-operar').click()
            mobile.locator('#manual-machine-select').select_option('EQ-ENV-01')
            mobile.locator('#btn-step2-view-active').click()
            mobile.locator('#btn-unlock-lock').click()
            expect(mobile.locator('#operation-status')).to_contain_text('cero bloqueos digitales' if remaining==0 else 'sigue bloqueada')
            self.assertEqual(self.state.machine['bloqueosActivos'],remaining)
            self.page.bring_to_front()
            self.page.evaluate('runSupervisorPollTick()')
            expect(self.page.locator('#detail-count')).to_have_text(str(remaining))
            expect(self.page.locator('#point-EQ-ENV-01')).to_have_attribute('data-state','locked' if remaining else 'free')
            self.assertEqual(self.metrics(),['6',str(int(remaining>0)),str(5+int(remaining==0)),str(remaining)])
            mobile.close()
        puts=[r for r in self.state.requests if r['method']=='PUT'];self.assertEqual(len(puts),2)

    def test_failed_refresh_gray_then_restores_from_api(self):
        self.open_plan();self.state.reads_fail=True
        self.page.evaluate('runSupervisorPollTick()');self.assert_gray()
        self.state.reads_fail=False;self.state.machine.update(bloqueada=True,bloqueosActivos=1)
        self.page.locator('#refresh').click()
        expect(self.page.locator('#detail-count')).to_have_text('1')
        self.assertEqual(self.metrics(),['6','1','5','1'])
        self.assertFalse(any(r['method']!='GET' for r in self.state.requests))

    def test_online_does_not_confirm_until_successful_read(self):
        self.open_plan();self.state.reads_fail=True
        self.page.evaluate('dispatchEvent(new Event("offline"))');self.assert_gray()
        self.page.evaluate('dispatchEvent(new Event("online"))')
        self.page.wait_for_function('() => !AppState.pollRequest');self.assert_gray()
        self.state.reads_fail=False
        self.page.evaluate('dispatchEvent(new Event("online"))')
        self.page.wait_for_function('() => !AppState.pollRequest && AppState.machinesConfirmed')
        expect(self.page.locator('#detail-count')).to_have_text('2')

    def test_stale_and_visibility_restore_require_new_read(self):
        self.open_plan()
        self.page.evaluate('AppState.machinesLastVerifiedAt=Date.now()-31000')
        self.page.wait_for_function('() => AppState.machinesConfirmed===false');self.assert_gray()
        self.page.evaluate('runSupervisorPollTick()')
        expect(self.page.locator('#detail-count')).to_have_text('2')
        self.page.evaluate('Object.defineProperty(document,"hidden",{value:true,configurable:true});document.dispatchEvent(new Event("visibilitychange"))')
        self.assert_gray()
        self.state.reads_fail=True
        self.page.evaluate('Object.defineProperty(document,"hidden",{value:false,configurable:true});document.dispatchEvent(new Event("visibilitychange"))')
        self.page.wait_for_function('() => !AppState.pollRequest');self.assert_gray()
        self.state.reads_fail=False;self.page.evaluate('runSupervisorPollTick()')
        expect(self.page.locator('#detail-count')).to_have_text('2')

    def test_malformed_duplicate_and_inconsistent_catalog_never_turns_green(self):
        self.open_plan()
        for payload in ([self.state.machine,self.state.machine],dict(error='invalid'),b'<html>proxy</html>',
                        [dict(self.state.machine,bloqueada=False)], [dict(self.state.machine,nombre='')]):
            self.state.bad_catalog=payload;self.page.evaluate('runSupervisorPollTick()');self.assert_gray()
        self.state.bad_catalog=None;self.page.evaluate('runSupervisorPollTick()')
        expect(self.page.locator('#detail-count')).to_have_text('2')

    def test_missing_and_unmapped_machines_are_not_invented(self):
        self.state.catalog=self.state.catalog[:-1];self.open_plan()
        expect(self.page.locator('#point-EQ-TR-01')).to_have_attribute('data-state','unknown')
        self.assertEqual(self.metrics(),['6','—','—','—'])
        self.page.locator('#point-EQ-TR-01').click();expect(self.page.locator('#open-analysis')).to_be_disabled()
        self.state.catalog.append(dict(self.state.machine,id='EQ-EXTRA-01',nombre='Equipo extra'))
        self.page.evaluate('runSupervisorPollTick()')
        expect(self.page.locator('#unmapped')).to_contain_text('no tienen posición')

    def test_revoked_session_removes_plan(self):
        self.open_plan();self.state.auth_rejected=True
        self.page.evaluate('runSupervisorPollTick()')
        expect(self.page.locator('#supervisor-plan-panel')).to_be_hidden()
        self.assertEqual(self.page.locator('.machine-marker').count(),0)

    def test_keyboard_camera_themes_and_responsive(self):
        self.open_plan();point=self.page.locator('#point-EQ-COM-03');point.focus();point.press('Enter')
        expect(self.page.locator('#detail-code')).to_have_text('EQ-COM-03')
        self.page.locator('#zoom-in').click();expect(self.page.locator('#zoom-level')).to_have_text('150 %')
        self.page.locator('#fit-plan').click();expect(self.page.locator('#zoom-level')).to_have_text('100 %')
        self.page.locator('#supervisor-tab-plan').focus();self.page.keyboard.press('ArrowLeft')
        expect(self.page.locator('#supervisor-tab-overview')).to_have_attribute('aria-selected','true')
        self.page.keyboard.press('ArrowRight');expect(self.page.locator('#supervisor-plan-panel')).to_be_visible()
        for width in (390,768,1024,1440):
            self.page.set_viewport_size({'width':width,'height':1000})
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
        self.page.set_viewport_size({'width':1440,'height':1000})
        self.page.locator('#theme-toggle').click()
        self.assertEqual(self.page.locator('#supervisor-plan-host').get_attribute('data-theme'),'light')
        self.page.locator('#theme-toggle').click()
        self.page.emulate_media(reduced_motion='reduce')
        self.assertEqual(self.page.locator('.marker-disc').first.evaluate('(el)=>getComputedStyle(el).transitionDuration'),'0s')

    def test_untrusted_catalog_text_is_not_html(self):
        self.state.machine['nombre']='<img src=x onerror="window.injected=true">'
        self.state.machine['area']='<script>window.injected=true</script>'
        self.state.machine['mtbf']=-1
        self.open_plan()
        expect(self.page.locator('#detail-name')).to_have_text(self.state.machine['nombre'])
        expect(self.page.locator('#detail-mtbf')).to_have_text('No calculable')
        self.assertIsNone(self.page.evaluate('window.injected'))
        self.assertEqual(self.page.locator('#supervisor-plan-host img').count(),0)
