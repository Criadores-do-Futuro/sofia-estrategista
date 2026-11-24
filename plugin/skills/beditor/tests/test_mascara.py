import subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import mascara, montador, aplicar_decisoes


class TestMascara(unittest.TestCase):
    def test_desligada_por_padrao(self):
        self.assertFalse(mascara.normalizar(None)["ligada"])
        self.assertFalse(mascara.ativa_no_solo({}))
        self.assertEqual(mascara.normalizar(True)["suavizarPct"], 30.0)

    def test_suavizar_30_e_288_px_em_1920(self):
        self.assertEqual(mascara.rampa_px(1920, 30), 288)
        self.assertEqual(mascara.rampa_px(1920, 0), 0)

    def test_cobertura_solo_cobre_o_topo_e_libera_o_rosto(self):
        cfg = {"ligada": True, "linhaPct": 20, "suavizarPct": 30}
        self.assertEqual(mascara.cobertura(0, 1920, cfg), 1.0)       # topo some
        self.assertAlmostEqual(mascara.cobertura(384, 1920, cfg), 0.5)  # na linha, meio
        self.assertEqual(mascara.cobertura(1000, 1920, cfg), 0.0)    # rosto inteiro
        # a rampa nao tem degrau: vizinhos diferem pouco
        passos = [mascara.cobertura(y, 1920, cfg) for y in range(240, 530)]
        self.assertLess(max(abs(a - b) for a, b in zip(passos, passos[1:])), 0.01)

    def test_manter_cima_inverte(self):
        cfg = {"ligada": True, "linhaPct": 20, "suavizarPct": 30, "manter": "cima"}
        self.assertEqual(mascara.cobertura(0, 1920, cfg), 0.0)
        self.assertEqual(mascara.cobertura(1900, 1920, cfg), 1.0)

    def test_split_dissolve_na_juncao_sem_fresta(self):
        g = mascara.geometria_split(1080, 1920, 840, 30)
        self.assertEqual(g["rampaPx"], 288)
        self.assertEqual(g["apoio"]["height"], 984)          # desce meia rampa
        self.assertEqual(g["rosto"]["top"], 696)             # sobe meia rampa
        self.assertEqual(g["rosto"]["top"] + g["rosto"]["height"], 1920)
        self.assertLess(g["rosto"]["top"], g["apoio"]["height"])   # sobrepostos
        self.assertEqual(g["caixaRosto"], "1080x1224")
        self.assertIn("mask-image", g["css"])

    def test_validar(self):
        self.assertEqual(mascara.validar({}), [])
        self.assertEqual(mascara.validar({"mascara": {"ligada": True, "suavizarPct": 30}}), [])
        erros = mascara.validar({"mascara": {"orientacao": "vertical", "suavizarPct": 140}})
        self.assertEqual(len(erros), 2)

    def test_png_tem_alfa_certo(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "m.png"
            mascara.png({"ligada": True, "linhaPct": 20, "suavizarPct": 30}, 108, 192, arq)
            im = Image.open(arq)
            self.assertEqual(im.size, (108, 192))
            self.assertEqual(im.getpixel((50, 0))[3], 255)
            self.assertEqual(im.getpixel((50, 150))[3], 0)

    def test_montador_sobrepoe_so_no_aroll(self):
        chamadas = []
        orig = subprocess.run
        subprocess.run = lambda cmd, **k: chamadas.append(cmd)
        try:
            montador.cortar({"tipo": "aroll", "de": 0, "ate": 2}, Path("f.mp4"),
                            Path("o.mp4"), 1080, 1920, 0, 0.0, Path("m.png"))
        finally:
            subprocess.run = orig
        cmd = chamadas[0]
        self.assertIn("m.png", cmd)
        self.assertTrue(any("overlay" in str(x) for x in cmd))

    def test_mesa_grava_no_guia_e_desligar_preserva(self):
        guia = {}
        msg = aplicar_decisoes.aplicar_mascara(guia, {"mascara": {"ligada": True, "linhaPct": 18}})
        self.assertTrue(msg and guia["mascara"]["ligada"])
        self.assertEqual(guia["mascara"]["suavizarPct"], 30.0)
        aplicar_decisoes.aplicar_mascara(guia, {"mascara": {"ligada": False, "linhaPct": 18}})
        self.assertFalse(guia["mascara"]["ligada"])
        self.assertEqual(guia["mascara"]["linhaPct"], 18.0)
        self.assertEqual(aplicar_decisoes.aplicar_mascara({}, {"mascara": {"ligada": False}}), [])


if __name__ == "__main__":
    unittest.main()
