import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import acabamento, cor


class TestGradeDeFabrica(unittest.TestCase):
    def test_a_grade_de_fabrica_e_a_que_o_canal_ja_usava(self):
        # Esta linha era uma constante no acabamento.py antes de cor.py existir.
        # Se alguem mexer no COR_PADRAO sem querer, o A-roll de todo mundo muda.
        self.assertEqual(
            cor.filtro(cor.COR_PADRAO),
            "eq=contrast=1.150:gamma=1.020,"
            "unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=0.85:chroma_amount=0.0")
        self.assertEqual(acabamento.IMAGEM, cor.filtro(cor.COR_PADRAO))

    def test_ficha_neutra_nao_toca_na_imagem(self):
        neutra = {"contraste": 1.0, "gama": 1.0, "nitidez": 0.0}
        self.assertEqual(cor.filtro(neutra), "null")

    def test_so_entra_no_filtro_o_que_foi_mexido(self):
        f = cor.filtro({"temperatura": 7100})
        self.assertIn("colortemperature=temperature=7100", f)
        self.assertNotIn("colorbalance", f)   # tonalidade ficou em zero
        self.assertNotIn("curves", f)         # preto e branco ficaram neutros


class TestOrdemDasFichas(unittest.TestCase):
    def test_o_guia_manda_sobre_a_preferencia_do_canal(self):
        pref = {"contraste": 1.30, "saturacao": 0.90}
        guia = {"cor": {"contraste": 1.05}}
        c = cor.da_ficha(guia, preferencia=pref)
        self.assertAlmostEqual(c["contraste"], 1.05)   # o video ganha
        self.assertAlmostEqual(c["saturacao"], 0.90)   # o canal segue valendo
        self.assertAlmostEqual(c["nitidez"], cor.COR_PADRAO["nitidez"])  # o resto e fabrica

    def test_numero_fora_da_faixa_e_preso_em_vez_de_passar(self):
        c = cor.resolver({"contraste": 9.0, "temperatura": 100})
        self.assertEqual(c["contraste"], cor.FAIXAS["contraste"][1])
        self.assertEqual(c["temperatura"], cor.FAIXAS["temperatura"][0])

    def test_preferencia_gravada_volta_inteira(self):
        with tempfile.TemporaryDirectory() as d:
            alvo = Path(d) / "cor.json"
            cor.gravar_preferencia({"saturacao": 0.88}, caminho=alvo, nota="pele")
            lida = cor.ler_preferencia(alvo)
            self.assertAlmostEqual(lida["saturacao"], 0.88)
            self.assertEqual(json.loads(alvo.read_text(encoding="utf-8"))["nota"], "pele")

    def test_arquivo_estragado_nao_derruba_o_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            alvo = Path(d) / "cor.json"
            alvo.write_text("{isto nao e json", encoding="utf-8")
            self.assertEqual(cor.ler_preferencia(alvo), {})


class TestResumo(unittest.TestCase):
    def test_resumo_diz_de_fabrica_quando_nada_mudou(self):
        self.assertEqual(cor.resumo(cor.COR_PADRAO), "de fabrica")

    def test_resumo_lista_so_o_que_difere(self):
        r = cor.resumo({"saturacao": 0.94})
        self.assertIn("saturacao 0.94", r)
        self.assertNotIn("contraste", r)


if __name__ == "__main__":
    unittest.main()
