import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'plugin'
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('preparar_estilo', ROOT / 'scripts/preparar_estilo.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class PrepararEstiloTest(unittest.TestCase):
    def test_cadastra_sem_transcricao_e_preserva_referencia(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t); video=base/'video.mp4'; video.write_bytes(b'fonte')
            manual={'versao':1,'nome':'Teste','referencias':[{'id':'ref-1','fonte':str(video),'duracao_segundos':1}], 'observacoes':[{'id':'o','aspecto':'som','estado':'indisponivel','descricao':'revisar','evidencias':[]}]}
            def preparar(videos,nome,out):
                out.mkdir(); (out/'manual.json').write_text(json.dumps(manual)); (out/'capa.jpg').write_bytes(b'capa')
                return {'limites':['Sem análise semântica']}
            with patch.object(mod,'preparar',preparar):
                resultado=mod.executar([video],'Teste','teste',base/'analise',base/'biblioteca')
                self.assertEqual(resultado['id'],'teste')
                self.assertEqual(video.read_bytes(),b'fonte')
                self.assertTrue((base/'biblioteca/teste/capa.jpg').is_file())
                with self.assertRaises(ValueError):
                    mod.executar([video],'Teste','teste',base/'outra',base/'biblioteca')
                self.assertFalse((base/'outra').exists())
