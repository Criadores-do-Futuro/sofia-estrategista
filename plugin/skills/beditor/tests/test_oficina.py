"""`oficina.Cronometro` é o histórico de máquina do projeto: uma linha por execução.

O que se tranca: grava UMA linha por saída do bloco, faz append (a segunda
execução não apaga a primeira — o histórico É o dado), registra rc=1 quando a
etapa estoura e NÃO engole a exceção: medir não é tratar erro.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import oficina  # noqa: E402


class TestCronometro(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # pasta que ainda não existe: o cronômetro tem de criá-la
        self.pasta = Path(self.tmp.name) / "edicao" / "oficina"

    def tearDown(self):
        self.tmp.cleanup()

    def _linhas(self):
        return [json.loads(l) for l in (self.pasta / "telemetria.jsonl").read_text().splitlines() if l]

    def test_grava_uma_linha_com_os_campos(self):
        with oficina.Cronometro(self.pasta, "transcrever", args={"takes": 3}) as c:
            c.extra["palavras"] = 337
        ls = self._linhas()
        self.assertEqual(len(ls), 1)
        l = ls[0]
        self.assertEqual(l["etapa"], "transcrever")
        self.assertEqual(l["args"], {"takes": 3})
        self.assertEqual(l["palavras"], 337)
        self.assertEqual(l["rc"], 0)
        self.assertGreaterEqual(l["segundos"], 0)
        self.assertLessEqual(l["inicio"], l["fim"])
        for k in ("script", "inicio", "fim", "segundos"):
            self.assertIn(k, l)

    def test_append_nunca_sobrescreve(self):
        with oficina.Cronometro(self.pasta, "cortar"):
            pass
        with oficina.Cronometro(self.pasta, "renderizar"):
            pass
        self.assertEqual([l["etapa"] for l in self._linhas()], ["cortar", "renderizar"])

    def test_excecao_registra_rc_1_e_continua_propagando(self):
        with self.assertRaises(RuntimeError):
            with oficina.Cronometro(self.pasta, "medir"):
                raise RuntimeError("estourou")
        ls = self._linhas()
        self.assertEqual(len(ls), 1)
        self.assertEqual(ls[0]["rc"], 1)


if __name__ == "__main__":
    unittest.main()
