import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'plugin'
spec = importlib.util.spec_from_file_location('localizar_sofia', ROOT / 'scripts/localizar_sofia.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SofiaTest(unittest.TestCase):
    def test_localiza_fichas_e_recusa_travessia(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'references/formatos').mkdir(parents=True)
            (root/'references/principios.md').write_text('p')
            (root/'references/formatos/dinamismo.md').write_text('d')
            result = mod.localizar(root, 'dinamismo')
            self.assertEqual(Path(result['formato']).read_text(), 'd')
            with self.assertRaises(ValueError):
                mod.localizar(root, '../../segredo')
            with self.assertRaises(ValueError):
                mod.localizar(root, 'formato-desconhecido')

    def test_sem_acervo_usa_as_fichas_que_vem_no_plugin(self):
        acervo = mod.acervo_padrao({})
        self.assertEqual(acervo, ROOT / 'skills' / 'sofia-estrategista')
        result = mod.localizar(acervo, 'dinamismo')
        self.assertTrue(Path(result['principios']).is_file())
        self.assertTrue(Path(result['formato']).is_file())

    def test_variavel_de_ambiente_vence_o_acervo_do_plugin(self):
        self.assertEqual(mod.acervo_padrao({'SOFIA_ACERVO_DIR': '/a', 'BEDITOR_SOFIA_DIR': '/b'}), Path('/a'))
        self.assertEqual(mod.acervo_padrao({'BEDITOR_SOFIA_DIR': '/b'}), Path('/b'))

    def test_todo_formato_do_catalogo_tem_ficha(self):
        acervo = ROOT / 'skills' / 'sofia-estrategista'
        fichas = [p.stem for p in (acervo / 'references' / 'formatos').glob('*.md') if p.stem != 'README']
        self.assertGreater(len(fichas), 10)
        for ficha in fichas:
            mod.localizar(acervo, ficha)
