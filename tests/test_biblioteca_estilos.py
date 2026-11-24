import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'plugin/scripts/biblioteca_estilos.py'

class BibliotecaTest(unittest.TestCase):
    def test_salva_lista_capa_e_impede_manual_alterado(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t); root = base/'biblioteca'; manual = base/'manual.json'; capa = base/'capa.png'
            manual.write_text(json.dumps({'versao':1,'nome':'Estilo','referencias':[{'id':'r','fonte':'origem','duracao_segundos':1}], 'observacoes':[{'id':'o','aspecto':'som','estado':'indisponivel','descricao':'a verificar','evidencias':[]}]}))
            capa.write_bytes(b'capa de teste')
            def run(*args): return subprocess.run(['python3', str(SCRIPT), '--raiz', str(root), *args], text=True, capture_output=True)
            self.assertEqual(run('cadastrar','--id','meu-estilo','--nome','Estilo','--manual',str(manual),'--capa',str(capa)).returncode,0)
            items=json.loads(run('listar','--json').stdout)
            self.assertEqual(items[0]['id'],'meu-estilo')
            self.assertEqual(Path(items[0]['capa_caminho']).read_bytes(),capa.read_bytes())
            self.assertEqual(run('mostrar','meu-estilo','--manual').returncode,0)
            self.assertNotEqual(run('cadastrar','--id','meu-estilo','--nome','x','--manual',str(manual)).returncode,0)
            self.assertNotEqual(run('mostrar','../outro').returncode,0)
            (root/'meu-estilo/manual.json').write_text('{}')
            self.assertNotEqual(run('mostrar','meu-estilo','--manual').returncode,0)
            self.assertTrue(manual.exists())
    def test_recusa_manual_invalido(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t); manual=base/'manual.json'; manual.write_text('{}')
            result=subprocess.run(['python3',str(SCRIPT),'--raiz',str(base/'lib'),'cadastrar','--id','teste','--nome','Teste','--manual',str(manual)],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((base/'lib/teste').exists())
