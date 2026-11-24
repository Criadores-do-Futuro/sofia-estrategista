import copy, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import direcao, validar, gerar_guia_md

FIX = Path(__file__).resolve().parent / "fixtures"


def bom():
    return json.loads((FIX / "guia_bom.json").read_text(encoding="utf-8"))


class TestDirecao(unittest.TestCase):
    def test_guia_completo_passa(self):
        self.assertEqual(direcao.validar(bom()), [])

    def test_direcao_exige_os_oito_itens(self):
        g = bom(); del g["direcaoMotion"]["camera"]; g["direcaoMotion"]["som"] = " "
        erros = direcao.validar(g)
        self.assertTrue(any("`camera`" in e and "`som`" in e for e in erros))
        self.assertEqual(len(direcao.DIRECAO), 8)

    def test_cada_cena_exige_os_cinco_itens(self):
        g = bom(); del g["momentos"][1]["motion"]["cena"]["cameraTransicao"]
        self.assertTrue(any("M02" in e and "cameraTransicao" in e for e in direcao.validar(g)))
        g = bom(); del g["momentos"][1]["motion"]["cena"]
        self.assertTrue(any("M02" in e and "sem `cena`" in e for e in validar.validar(g)))

    def test_texto_de_no_maximo_seis_palavras(self):
        g = bom(); g["momentos"][1]["motion"]["cena"]["texto"] = "um dois tres quatro cinco seis sete"
        self.assertTrue(any("7 palavras" in e for e in direcao.validar(g)))

    def test_cena_sem_texto_e_permitida_se_declarada(self):
        g = bom(); g["momentos"][1]["motion"]["cena"]["texto"] = ""
        self.assertEqual(direcao.validar(g), [])
        self.assertIn("Sem texto na tela", direcao.cenas(g)[0][1])

    def test_formato_sem_motion_nao_pede_direcao(self):
        g = bom(); g["momentos"][1]["decisao"] = "aroll"; del g["momentos"][1]["motion"]
        del g["direcaoMotion"]
        self.assertEqual(direcao.validar(g), [])
        self.assertEqual(direcao.markdown(g), [])

    def test_prompt_traz_os_cinco_itens_e_o_estilo(self):
        (m, p), = direcao.cenas(bom())
        c = m["motion"]["cena"]
        for trecho in (c["naTela"], "«segunda longa»", c["visual"], c["cameraTransicao"], c["som"],
                       bom()["direcaoMotion"]["estiloAnimacao"]):
            self.assertIn(trecho, p)
        self.assertIn("última cena", p)

    def test_guia_md_tem_direcao_e_prompts(self):
        md = gerar_guia_md.render(bom())
        self.assertIn("## Direção de motion", md)
        self.assertIn("## Prompt de cada cena", md)
        self.assertIn("**Câmera (parada, zoom, pan, shake):**", md)


if __name__ == "__main__":
    unittest.main()
