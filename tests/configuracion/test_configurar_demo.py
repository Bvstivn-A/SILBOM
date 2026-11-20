import contextlib
import importlib.util
import io
from pathlib import Path
import secrets
import subprocess
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('demo_config',Path(__file__).resolve().parents[2]/'scripts/configurar-demo.py')
config=importlib.util.module_from_spec(spec);spec.loader.exec_module(config)

class ConfigurarDemoTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        subprocess.run(['git','init','-q',str(self.root)],check=True,capture_output=True)
        (self.root/'.gitignore').write_text('.env\n.env.*\n')
        self.env=self.root/'.env';self.db_secret=secrets.token_urlsafe(24)
        self.original='DB_URL=jdbc:postgresql://localhost/silbom\nDB_PASSWORD='+self.db_secret+'\nENCRYPTION_SECRET=valor-local-conservado\n'
        self.env.write_text(self.original)
    def tearDown(self):self.temp.cleanup()
    def run_config(self,values):
        values=iter(values);output=io.StringIO()
        with contextlib.redirect_stdout(output):config.configure(self.env,lambda _:next(values))
        self.assertNotIn(self.db_secret,output.getvalue());return output.getvalue()
    def test_configura_y_no_imprime_secretos(self):
        a,b=secrets.token_urlsafe(24),secrets.token_urlsafe(24)
        output=self.run_config([a,a,b,b]);new=self.env.read_text()
        self.assertTrue(new.startswith(self.original));self.assertIn('SILBOM_DEMO_TWO_USERS_ONLY=true',new)
        self.assertIn('SILBOM_DEMO_SUPERVISOR_USERNAME=supervisor',new)
        self.assertNotIn(a,output);self.assertNotIn(b,output);self.assertEqual(0o600,self.env.stat().st_mode&0o777)
    def test_repetir_conserva_secretos_existentes(self):
        a,b=secrets.token_urlsafe(24),secrets.token_urlsafe(24)
        self.run_config([a,a,b,b]);before=self.env.read_bytes();self.run_config([])
        self.assertEqual(before,self.env.read_bytes())
    def test_clave_corta_no_modifica(self):
        with self.assertRaises(ValueError):self.run_config(['x'])
        self.assertEqual(self.original,self.env.read_text())
    def test_confirmacion_distinta_no_modifica(self):
        with self.assertRaises(ValueError):self.run_config([secrets.token_urlsafe(24),secrets.token_urlsafe(24)])
        self.assertEqual(self.original,self.env.read_text())
    def test_archivo_versionado_no_modifica(self):
        subprocess.run(['git','-C',str(self.root),'add','-f','.env'],check=True,capture_output=True)
        with self.assertRaises(ValueError):self.run_config([])
        self.assertEqual(self.original,self.env.read_text())
    def test_symlink_no_modifica(self):
        other=self.root/'original';self.env.rename(other);self.env.symlink_to(other)
        with self.assertRaises(ValueError):self.run_config([])
        self.assertEqual(self.original,other.read_text())
    def test_duplicados_no_modifica(self):
        self.env.write_text(self.original+'SILBOM_DEMO_TWO_USERS_ONLY=false\nSILBOM_DEMO_TWO_USERS_ONLY=true\n')
        before=self.env.read_bytes()
        with self.assertRaises(ValueError):self.run_config([])
        self.assertEqual(before,self.env.read_bytes())
    def test_saltos_de_linea_no_admitidos(self):
        with self.assertRaises(ValueError):config.validate_password(secrets.token_urlsafe(24)+'\n')

if __name__=='__main__':unittest.main()
