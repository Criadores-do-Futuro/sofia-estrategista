"""Os cortes de cada voz saem da medição, não de um número da casa.

O que se tranca:
- uma ressonância estreita somada a um espectro liso é achada, na frequência
  certa, com corte de 3 a 4 dB;
- espectro liso não ganha corte inventado;
- a presença de 3,2 kHz nunca é cortada;
- os cortes entram na cadeia antes da presença, e sem cortes a cadeia é a da casa;
- cortes fixados na marca mandam; sem fixar, cada take é medido e a medição fica
  guardada na marca.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import acabamento  # noqa: E402
import voz  # noqa: E402


def _ruido(pasta, af=None):
    arq = Path(pasta) / "v.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anoisesrc=d=8:c=pink:a=0.3:seed=7",
                    *(["-af", af] if af else []), str(arq)], check=True)
    return arq


class TestMedir(unittest.TestCase):
    def test_acha_ressonancia_na_frequencia_certa(self):
        with tempfile.TemporaryDirectory() as t:
            cortes = voz.medir(_ruido(t, "equalizer=f=900:t=q:w=4:g=9"))
        perto = [c for c in cortes if abs(c["f"] - 900) / 900 < 0.08]
        self.assertTrue(perto, cortes)
        self.assertIn(perto[0]["g"], (-3.0, -4.0))

    def test_espectro_liso_nao_ganha_corte(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(voz.medir(_ruido(t)), [])

    def test_presenca_nunca_e_cortada(self):
        with tempfile.TemporaryDirectory() as t:
            cortes = voz.medir(_ruido(t, "equalizer=f=3200:t=q:w=4:g=9"))
        self.assertFalse([c for c in cortes if 2700 < c["f"] < 3800], cortes)


class TestCadeia(unittest.TestCase):
    def test_cortes_antes_da_presenca(self):
        c = acabamento.cadeia_voz([{"f": 1900, "g": -4.0, "q": 4.0}])
        self.assertLess(c.index("equalizer=f=1900"), c.index("equalizer=f=3200"))
        self.assertEqual(acabamento.cadeia_voz(None), acabamento.VOZ)
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=d=0.2", "-af", c,
                        "-f", "null", "-"], check=True)


class TestMarca(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = Path(self.tmp.name)
        self._env = {k: os.environ.get(k) for k in ("BEDITOR_CONFIG", "BEDITOR_MARCA")}
        os.environ["BEDITOR_CONFIG"] = str(r / "config.json")
        os.environ["BEDITOR_MARCA"] = "cliente"
        (r / "config.json").write_text(json.dumps({"versao": 1, "pastas": {"marcas": str(r / "marcas")}}),
                                       encoding="utf-8")
        (r / "marcas" / "cliente").mkdir(parents=True)
        self.arq = r / "marcas" / "cliente" / "marca.json"
        self.arq.write_text(json.dumps({"nome": "Cliente"}), encoding="utf-8")
        self.take = _ruido(r, "equalizer=f=900:t=q:w=4:g=9")

    def tearDown(self):
        for k, v in self._env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.tmp.cleanup()

    def test_mede_cada_take_e_guarda_a_medicao(self):
        cortes = voz.cortes_para(self.take, log=lambda m: None)
        guardado = json.loads(self.arq.read_text(encoding="utf-8"))["voz"]
        self.assertEqual(guardado["cortes"], cortes)
        self.assertFalse(guardado["fixo"])

    def test_cortes_fixados_mandam(self):
        fixos = [{"f": 1234, "g": -3.0, "q": 4.0}]
        self.arq.write_text(json.dumps({"nome": "Cliente", "voz": {"cortes": fixos, "fixo": True}}),
                            encoding="utf-8")
        self.assertEqual(voz.cortes_para(self.take, log=lambda m: None), fixos)


if __name__ == "__main__":
    unittest.main()
