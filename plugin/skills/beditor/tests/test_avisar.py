"""O aviso registra, mostra na tela e nunca derruba quem chamou.

O que se tranca:
- o aviso vai para o log com tipo e projeto, e `--ler` só devolve os pendentes;
- `BEDITOR_SEM_AVISO=1` cala tudo (lote e teste);
- falha do `osascript` (máquina sem ele, tela bloqueada) é engolida: o render
  que terminou bem não pode morrer por causa do aviso.
"""
import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


class TestAvisar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["BEDITOR_AVISOS"] = str(Path(self.tmp.name) / "avisos.jsonl")
        os.environ.pop("BEDITOR_SEM_AVISO", None)
        import avisar
        self.a = importlib.reload(avisar)
        self.telas = []
        # `avisar.subprocess` É o módulo subprocess: atribuir direto nele vaza
        # para todo o processo e derruba os outros testes. `patch` desfaz no fim.
        self._p = mock.patch.object(self.a.subprocess, "run",
                                    side_effect=lambda *ar, **kw: self.telas.append(ar))
        self._p.start()
        self.addCleanup(self._p.stop)

    def tearDown(self):
        os.environ.pop("BEDITOR_AVISOS", None)
        os.environ.pop("BEDITOR_SEM_AVISO", None)
        self.tmp.cleanup()

    def test_registra_e_mostra(self):
        self.a.avisar("o 16 está pronto", tipo="revisar", projeto="16 - iPhone")
        self.assertEqual(len(self.telas), 1)
        pend = self.a.ler()
        self.assertEqual(len(pend), 1)
        self.assertEqual(pend[0]["tipo"], "revisar")
        self.assertEqual(pend[0]["projeto"], "16 - iPhone")
        self.assertEqual(self.a.ler(), [])          # ler marca como lido

    def test_mudo_nao_registra_nem_mostra(self):
        os.environ["BEDITOR_SEM_AVISO"] = "1"
        self.a.avisar("silêncio", tipo="aviso")
        self.assertEqual(self.telas, [])
        self.assertEqual(self.a.ler(), [])

    def test_falha_da_tela_nao_sobe(self):
        with mock.patch.object(self.a.subprocess, "run", side_effect=FileNotFoundError("osascript")):
            self.a.avisar("mesmo sem osascript o aviso fica gravado", tipo="publicar")
        self.assertEqual(len(self.a.ler()), 1)

    def test_tipo_desconhecido_para(self):
        with self.assertRaises(ValueError):
            self.a.avisar("x", tipo="grito")


if __name__ == "__main__":
    unittest.main()
