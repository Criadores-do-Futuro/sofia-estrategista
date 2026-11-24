"""O motor de visão é escolhido pela máquina, e os dois falam o mesmo contrato.

O que se tranca:
- Mac com os binários Swift usa o Vision; sem eles (ou fora do Mac), o portátil;
- `BEDITOR_VISAO` força o motor (é como se compara um com o outro);
- pedir o Vision sem binário para com a instrução de compilar, em vez de um
  FileNotFoundError no meio do render;
- a cache do render carrega o motor: trocar de motor refaz, mexer no código
  que o chama não.
"""
import importlib
import os
import platform
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


class TestMotor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._env = os.environ.pop("BEDITOR_VISAO", None)
        import visao
        self.v = importlib.reload(visao)
        self._p = mock.patch.object(self.v, "BIN", Path(self.tmp.name))
        self._p.start()

    def tearDown(self):
        self._p.stop()
        if self._env is not None:
            os.environ["BEDITOR_VISAO"] = self._env
        else:
            os.environ.pop("BEDITOR_VISAO", None)
        self.tmp.cleanup()

    def _binarios(self):
        for n in ("rastrear-rosto", "recorte"):
            b = Path(self.tmp.name) / n
            b.write_text("#!/bin/sh\n")
            b.chmod(0o755)

    def test_sem_binario_e_portatil(self):
        self.assertEqual(self.v.motor(), "portatil")

    def test_mac_com_binarios_usa_vision(self):
        self._binarios()
        with mock.patch.object(self.v.platform, "system", return_value="Darwin"):
            self.assertEqual(self.v.motor(), "vision")

    def test_windows_com_binarios_nao_usa_vision(self):
        self._binarios()
        with mock.patch.object(self.v.platform, "system", return_value="Windows"):
            self.assertEqual(self.v.motor(), "portatil")

    def test_variavel_forca_o_motor(self):
        os.environ["BEDITOR_VISAO"] = "portatil"
        self._binarios()
        with mock.patch.object(self.v.platform, "system", return_value="Darwin"):
            self.assertEqual(self.v.motor(), "portatil")

    def test_vision_sem_binario_manda_compilar(self):
        with self.assertRaises(SystemExit) as e:
            self.v.rastrear_rosto("x.mov", Path(self.tmp.name) / "r.json", forcar="vision")
        self.assertIn("instalar_bin.sh", str(e.exception))


class TestCacheDoRenderCarregaOMotor(unittest.TestCase):
    def test_chave_muda_com_o_motor_e_nao_com_o_codigo(self):
        try:
            import render_analise
        except Exception as e:  # noqa: BLE001 — dependência nativa ausente nesta máquina
            self.skipTest(f"render_analise não importa: {e}")
        recs = [{"hook": None, "cartao": None, "marc": None, "leg": {"txt": "x"}}]
        with mock.patch.object(render_analise.visao, "motor", return_value="vision"):
            a = render_analise.versao_do_segmento(recs)
            self.assertEqual(a, render_analise.versao_do_segmento(recs))
        with mock.patch.object(render_analise.visao, "motor", return_value="portatil"):
            self.assertNotEqual(a, render_analise.versao_do_segmento(recs))


if __name__ == "__main__":
    unittest.main()
