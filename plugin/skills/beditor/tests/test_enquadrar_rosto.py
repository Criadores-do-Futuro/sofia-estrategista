import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import enquadrar_rosto as er

# 1080x1920 dentro de uma caixa 1080x1080: sobra 840 px na vertical
FW, FH, CW, CH = 1080, 1920, 1080, 1080


def amostra(t, topo, altura):
    return {"time": t, "top": topo, "bottom": topo + altura, "height": altura,
            "centerX": 0.5, "centerY": topo + altura / 2, "width": 0.4, "confidence": 0.9}


def trilha(f, dur=10.0, passo=0.25):
    return [amostra(i * passo, *f(i * passo)) for i in range(int(dur / passo) + 1)]


def janela(p):
    y0 = p / 100 * (FH - CH)
    return y0, y0 + CH


class TestEnquadrarRosto(unittest.TestCase):
    def test_rosto_parado_fica_parado_e_centrado(self):
        enq = er.enquadrar(trilha(lambda t: (0.40, 0.25)), FW, FH, CW, CH, duracao=10)
        ps = {k["p"] for k in enq["keyframes"]}
        self.assertEqual(len(ps), 1)
        self.assertEqual(enq["colisoes"], [])
        # faixa protegida [topo - 0,30h, base + 0,05h] centrada na caixa
        cabelo = (0.40 - 0.30 * 0.25) * FH
        queixo = (0.65 + 0.05 * 0.25) * FH
        y0, y1 = janela(ps.pop())
        self.assertAlmostEqual((cabelo + queixo) / 2, (y0 + y1) / 2, delta=5)

    def test_rosto_que_desce_e_acompanhado_sem_sair_da_caixa(self):
        amostras = trilha(lambda t: (0.25 + 0.02 * t, 0.22))
        enq = er.enquadrar(amostras, FW, FH, CW, CH, duracao=10)
        ks = enq["keyframes"]
        self.assertGreater(ks[-1]["p"], ks[0]["p"])
        for a in amostras:
            p = er._linear([k["t"] for k in ks], [k["p"] for k in ks], a["time"])
            y0, y1 = janela(p)
            self.assertLessEqual(y0, (a["top"] - 0.30 * a["height"]) * FH + 2, a["time"])
            self.assertGreaterEqual(y1, (a["bottom"] + 0.05 * a["height"]) * FH - 2, a["time"])

    def test_deteccao_isolada_errada_nao_vira_salto(self):
        amostras = trilha(lambda t: (0.40, 0.25))
        amostras[20] = amostra(amostras[20]["time"], 0.10, 0.25)   # um quadro doido
        enq = er.enquadrar(amostras, FW, FH, CW, CH, duracao=10)
        self.assertEqual(len({k["p"] for k in enq["keyframes"]}), 1)

    def test_quem_sai_do_quadro_segura_a_ultima_posicao(self):
        antes = [amostra(t / 4, 0.30, 0.25) for t in range(0, 9)]        # 0-2 s
        depois = [amostra(6 + t / 4, 0.50, 0.25) for t in range(0, 9)]   # 6-8 s
        enq = er.enquadrar(antes + depois, FW, FH, CW, CH, duracao=8)
        ks = enq["keyframes"]
        p = lambda t: er.preencher([k["t"] for k in ks], [k["p"] for k in ks], t)
        self.assertAlmostEqual(p(3.0), p(1.0), delta=1.0)   # longe da volta, parado
        self.assertGreater(p(7.5), p(3.0))                  # e volta a acompanhar

    def test_rosto_grande_demais_marca_colisao_de_cabelo_e_guarda_o_queixo(self):
        amostras = trilha(lambda t: (0.30, 0.50))   # 960 px de rosto: não cabe com cabelo
        enq = er.enquadrar(amostras, FW, FH, CW, CH, duracao=10)
        self.assertTrue(enq["colisoes"])
        self.assertEqual({c["tipo"] for c in enq["colisoes"]}, {"cabelo"})
        self.assertGreater(enq["caixaMinimaPx"], CH)
        y0, y1 = janela(enq["keyframes"][0]["p"])
        self.assertGreaterEqual(y1 + 1, (0.80 + 0.05 * 0.50) * FH)   # queixo dentro

    def test_gsap_encadeia_os_keyframes(self):
        enq = er.enquadrar(trilha(lambda t: (0.25 + 0.02 * t, 0.22)), FW, FH, CW, CH, duracao=10)
        js = er.gsap(enq)
        self.assertTrue(js.startswith('tl.set("#presenter-video"'))
        self.assertEqual(js.count("tl.to("), len(enq["keyframes"]) - 1)
        self.assertIn('ease: "none"', js)


if __name__ == "__main__":
    unittest.main()
