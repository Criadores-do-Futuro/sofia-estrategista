import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'plugin'
spec = importlib.util.spec_from_file_location('mudancas', ROOT / 'scripts/detectar_mudancas_visuais.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class MudancasVisuaisTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'quadros.jsonl'
        self.addCleanup(self.temp.cleanup)
    def gravar(self, items):
        self.path.write_text(''.join(json.dumps(x)+'\n' for x in items))
    def dados(self):
        frames = [{'quadro': i, 'pts_segundos': i / 10, 'pontuacao_mudanca': score}
                  for i, score in enumerate([0, 12, 24, 0, 11])]
        return frames + [{'tipo': 'resumo', 'fonte': '/video.mp4', 'quadros_medidos': 5,
                          'quadros_sem_pts': 0, 'processamento_sem_erro': True,
                          'contagem_compativel': True}]
    def test_agrupa_picos_consecutivos_sem_afirmar_corte(self):
        self.gravar(self.dados())
        result = mod.detectar(self.path)
        self.assertEqual(len(result['candidatos']), 2)
        self.assertEqual(result['candidatos'][0]['pico_segundos'], .2)
        self.assertEqual(result['candidatos'][0]['quadros'], 2)
        self.assertIn('falsos positivos', result['limites'][0])
    def test_recusa_incompleto_sem_pontuacao_e_ordem_errada(self):
        data = self.dados()
        for mutation in ('truncado', 'missing', 'ordem'):
            altered = [x.copy() for x in data]
            if mutation == 'truncado': altered.pop()
            elif mutation == 'missing': altered[2].pop('pontuacao_mudanca')
            else: altered[2]['quadro'] = 7
            self.gravar(altered)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): mod.detectar(self.path)
    def test_limite_invalido(self):
        self.gravar(self.dados())
        for limit in (0, 101, float('nan'), True):
            with self.subTest(limit=limit), self.assertRaises(ValueError): mod.detectar(self.path, limit)
