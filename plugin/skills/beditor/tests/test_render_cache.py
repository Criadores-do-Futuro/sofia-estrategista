"""A cache de segmentos refaz só o que o ajuste tocou.

O que se tranca:
- `oficina.assinatura` muda quando a função usada (ou algo que ela cita) muda,
  e NÃO muda quando a mudança é numa função que o segmento não usa;
- `funcoes_do_segmento` espelha `compor`: toda `cartao.X(...)` chamada em
  `compor` aparece em alguma receita possível. Esquecer uma faria um ajuste
  nela não refazer o segmento — vídeo errado com cara de certo.
"""
import ast
import json
import inspect
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import oficina  # noqa: E402

MODULO = textwrap.dedent('''
    LARG = 0.9
    PX = 64

    def _sombra(x):
        return x + PX

    def legenda(t):
        return _sombra(t) * LARG

    def marcador(n):
        return n + 1
''')


class TestAssinatura(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.arq = Path(self.tmp.name) / "mod.py"
        self.arq.write_text(MODULO)

    def tearDown(self):
        self.tmp.cleanup()

    def _trocar(self, velho, novo):
        self.arq.write_text(self.arq.read_text().replace(velho, novo))

    def test_mudanca_fora_do_fecho_nao_invalida(self):
        antes = oficina.assinatura(self.arq, ["legenda"])
        self._trocar("return n + 1", "return n + 2")
        self.assertEqual(antes, oficina.assinatura(self.arq, ["legenda"]))

    def test_mudanca_em_dependencia_invalida(self):
        antes = oficina.assinatura(self.arq, ["legenda"])
        self._trocar("PX = 64", "PX = 70")
        self.assertNotEqual(antes, oficina.assinatura(self.arq, ["legenda"]))

    def test_comentario_nao_invalida(self):
        antes = oficina.assinatura(self.arq, ["legenda"])
        self._trocar("def legenda(t):", "# um comentario\ndef legenda(t):")
        self.assertEqual(antes, oficina.assinatura(self.arq, ["legenda"]))

    def test_nome_inexistente_para(self):
        with self.assertRaises(KeyError):
            oficina.assinatura(self.arq, ["nao_existe"])


class TestContaDaRodada(unittest.TestCase):
    """A conta que o render presta a cada rodada: quais funções mudaram e o custo disso."""

    def setUp(self):
        try:
            import render_analise
        except Exception as e:  # noqa: BLE001 — dependência nativa ausente nesta máquina
            self.skipTest(f"render_analise não importa: {e}")
        self.r = render_analise
        self.tmp = tempfile.TemporaryDirectory()
        self.of = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_grava_e_compara_as_assinaturas(self):
        segs = [[{"hook": None, "cartao": {"tipo": "frase"}, "marc": None, "leg": None}],
                [{"hook": None, "cartao": None, "marc": None, "leg": {"txt": "x"}}]]
        primeira = self.r.prestar_contas(self.of, segs, segs)
        self.assertEqual(primeira["refeitos"], 2)
        self.assertEqual(primeira["mudadas"], [])          # primeira rodada não acusa mudança
        arq = self.of / "assinaturas.json"
        self.assertTrue(arq.exists())
        gravadas = json.loads(arq.read_text())
        self.assertEqual(set(gravadas), set(self.r.DESENHO))
        # simula um ajuste em `frase_hook`: só o trecho com frase é cobrado ao código
        gravadas["frase_hook"] = "outra-coisa"
        arq.write_text(json.dumps(gravadas))
        segunda = self.r.prestar_contas(self.of, segs, segs)
        self.assertEqual(segunda["mudadas"], ["frase_hook"])
        self.assertEqual(segunda["porCodigo"], 1)

    def test_sem_mudanca_no_codigo_nao_culpa_o_codigo(self):
        segs = [[{"hook": None, "cartao": None, "marc": None, "leg": {"txt": "x"}}]]
        self.r.prestar_contas(self.of, segs, segs)
        conta = self.r.prestar_contas(self.of, segs, segs)
        self.assertEqual(conta["mudadas"], [])
        self.assertEqual(conta["porCodigo"], 0)


class TestEspelhoDoCompor(unittest.TestCase):
    def test_toda_funcao_de_compor_esta_coberta(self):
        try:
            import render_analise
        except Exception as e:  # dependência nativa ausente nesta máquina
            self.skipTest(f"render_analise não importa: {e}")
        chamadas = {n.func.attr for n in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(render_analise.compor))))
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and isinstance(n.func.value, ast.Name) and n.func.value.id == "cartao"}
        receitas = [
            {"hook": {"quadro": "x"}, "cartao": None, "marc": None, "leg": None},
            {"hook": None, "cartao": {"tipo": "frase"}, "marc": {"n": 1}, "leg": {"txt": "x"}},
            {"hook": None, "cartao": {"tipo": "triptico"}, "marc": None, "leg": None},
            {"hook": None, "cartao": {"tipo": "logo"}, "marc": None, "leg": None},
            {"hook": None, "cartao": {"tipo": "clipe"}, "marc": None, "leg": None},
        ]
        cobertas = set(render_analise.funcoes_do_segmento(receitas))
        self.assertEqual(chamadas - cobertas, set())


if __name__ == "__main__":
    unittest.main()
