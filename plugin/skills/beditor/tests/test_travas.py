import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import travas


def plano(*ps):
    return {"duracaoMs": 10000, "fonteVideo": "fonte.mp4",
            "planos": [dict(p) for p in ps]}


class TestTravas(unittest.TestCase):
    def test_fecha_buraco(self):
        p = plano({"id": "P00", "tipo": "fala", "t0": 0, "t1": 4000, "duracaoMs": 4000},
                  {"id": "P01", "tipo": "fala", "t0": 5000, "t1": 9000, "duracaoMs": 4000})
        av = travas.aplicar_todas(p)
        self.assertEqual(p["planos"][0]["t1"], 5000)
        self.assertEqual(p["planos"][1]["t1"], 10000)
        self.assertTrue(any("buraco" in a for a in av))

    def test_tela_sem_modo_vira_fala(self):
        p = plano({"id": "P00", "tipo": "tela", "t0": 0, "t1": 10000, "duracaoMs": 10000, "texto": "x"})
        travas.aplicar_todas(p)
        self.assertEqual(p["planos"][0]["tipo"], "fala")

    def test_palavras_dedupe_e_vazio(self):
        p = plano({"id": "P00", "tipo": "palavras", "t0": 0, "t1": 5000, "duracaoMs": 5000, "palavras": ["a", "b"]},
                  {"id": "P01", "tipo": "palavras", "t0": 5000, "t1": 10000, "duracaoMs": 5000, "palavras": ["a", "b"]})
        travas.aplicar_todas(p)
        self.assertEqual(p["planos"][1]["tipo"], "fala")

    def test_grafico_curto_segura(self):
        p = plano({"id": "P00", "tipo": "paper", "t0": 0, "t1": 1500, "duracaoMs": 1500, "paper": {"titulo": "t"}},
                  {"id": "P01", "tipo": "fala", "t0": 1500, "t1": 10000, "duracaoMs": 8500})
        travas.aplicar_todas(p)
        self.assertEqual(p["planos"][0]["t1"], 2500)
        self.assertEqual(p["planos"][1]["t0"], 2500)


if __name__ == "__main__":
    unittest.main()
