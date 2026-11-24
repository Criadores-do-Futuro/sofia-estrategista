import copy, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validar, gerar_guia_md

FIX = Path(__file__).resolve().parent / "fixtures"
CONTATO = {"takeMs": 10000, "frases": [
    {"id": "F000", "deMs": 500, "ateMs": 4000, "pausaAntesMs": 500, "pausaDepoisMs": 1500},
    {"id": "F001", "deMs": 5500, "ateMs": 9500, "pausaAntesMs": 1500, "pausaDepoisMs": 0}]}


def bom():
    return json.loads((FIX / "guia_bom.json").read_text(encoding="utf-8"))


class TestValidar(unittest.TestCase):
    def test_bom_passa(self):
        self.assertEqual(validar.validar(bom(), CONTATO), [])

    def test_buraco(self):
        g = bom(); g["momentos"][1]["deMs"] = 6000
        self.assertTrue(any("buraco" in e for e in validar.validar(g, CONTATO)))

    def test_sobreposicao(self):
        g = bom(); g["momentos"][1]["deMs"] = 5000
        self.assertTrue(any("sobrep" in e for e in validar.validar(g, CONTATO)))

    def test_nao_termina_no_fim(self):
        g = bom(); g["momentos"][-1]["ateMs"] = 9000
        self.assertTrue(any("fim do take" in e for e in validar.validar(g, CONTATO)))

    def test_motion_curto(self):
        g = bom(); g["momentos"][0]["ateMs"] = 8000; g["momentos"][1]["deMs"] = 8000
        self.assertTrue(any("2500" in e for e in validar.validar(g, CONTATO)))

    def test_movimento_vazio(self):
        g = bom(); g["momentos"][1]["motion"]["movimento"] = "o texto aparece"
        self.assertTrue(any("movimento" in e for e in validar.validar(g, CONTATO)))

    def test_motion_sem_decisao(self):
        g = bom(); g["momentos"][0]["motion"] = g["momentos"][1]["motion"]
        self.assertTrue(any("M01" in e and "motion" in e for e in validar.validar(g, CONTATO)))

    def test_densidade_fora_sem_justificativa(self):
        g = bom(); g["momentos"][1]["decisao"] = "aroll"; del g["momentos"][1]["motion"]
        self.assertTrue(any("densidade" in e for e in validar.validar(g, CONTATO)))

    def test_entra_antes_maior_que_pausa(self):
        g = bom(); g["momentos"][1]["motion"]["entraAntesMs"] = 2000
        self.assertTrue(any("entraAntesMs" in e for e in validar.validar(g, CONTATO)))

    def test_tela_sem_modo(self):
        g = bom(); m = g["momentos"][1]["motion"]; m["tipo"] = "tela"; m["dados"] = {}
        self.assertTrue(any("tela" in e and "modo" in e for e in validar.validar(g, CONTATO)))

    def test_mesmo_tipo_seguido_sem_porque(self):
        g = bom(); m0 = g["momentos"][0]
        m0["decisao"] = "motion"; m0["motion"] = copy.deepcopy(g["momentos"][1]["motion"])
        m0["motion"]["entraAntesMs"] = 0
        g["densidade"]["previstoPct"] = 100; g["densidade"]["justificativa"] = "fixture"
        self.assertTrue(any("repet" in e for e in validar.validar(g, CONTATO)))

    def test_objeto_que_pede_numero_e_roteamento_errado(self):
        g = bom(); m = g["momentos"][1]["motion"]
        m["tipo"] = "objeto"; m["dados"] = {}
        m["ideia"] = "dez paineis de papel creme, numerados, virados de costas"
        self.assertTrue(any("codigo" in e for e in validar.validar(g, CONTATO)))

    def test_familia_exige_estado(self):
        g = bom(); g["momentos"][1]["motion"]["familia"] = "cards"
        self.assertTrue(any("familia" in e for e in validar.validar(g, CONTATO)))


class TestGuiaMd(unittest.TestCase):
    def test_render_tem_tabela_e_cabecalho(self):
        md = gerar_guia_md.render(bom())
        self.assertIn("## Arco", md)
        self.assertIn("| M02 | 00:05.5 → 00:10.0 | motion", md)
        self.assertIn("as duas palavras da frase empilham", md)
        self.assertIn("45%", md)


if __name__ == "__main__":
    unittest.main()


class TestNegacaoESoTexto(unittest.TestCase):
    """As duas travas que nasceram do corte em que a voz dizia 'elas nao sao
    inteligentes' e a tela escrevia INTELIGENTES."""

    def _com_palavras(self, fala, dados):
        g = bom()
        m = g["momentos"][1]
        m["decisao"] = "motion"
        m["fala"] = fala
        m["motion"] = {"tipo": "palavras", "ideia": "as capacidades negadas",
                       "movimento": "entram uma a uma, ganham risco, saem por varredura",
                       "entrada": "corte", "saida": "corte", "dados": dados}
        return g

    def test_fala_nega_e_tela_afirma(self):
        g = self._com_palavras("Elas nao sao inteligentes.",
                               {"palavras": ["INTELIGENTES"]})
        self.assertTrue(any("nega inteligentes" in e for e in validar.validar(g, CONTATO)))

    def test_riscar_resolve(self):
        g = self._com_palavras("Elas nao sao inteligentes.",
                               {"palavras": ["INTELIGENTES"], "riscar": True})
        self.assertFalse(any("nega" in e for e in validar.validar(g, CONTATO)))

    def test_fala_afirmativa_nao_acusa(self):
        g = self._com_palavras("Sao quatro camadas.", {"palavras": ["CAMADAS"]})
        self.assertFalse(any("nega" in e for e in validar.validar(g, CONTATO)))

    def test_teto_de_planos_so_texto(self):
        g = bom()
        base = g["momentos"][1]
        base["decisao"] = "motion"
        base["motion"] = {"tipo": "palavras", "ideia": "x",
                          "movimento": "entra, acumula, sai",
                          "entrada": "corte", "saida": "corte",
                          "dados": {"palavras": ["UM"]}}
        # oito planos de motion, todos de texto: e o retrato do guia que errou
        tipos = ["palavras"] * 8
        g["momentos"] = [g["momentos"][0]] + [
            dict(base, id=f"MX{i}", deMs=5500 + i, ateMs=5501 + i,
                 motion=dict(base["motion"], tipo=t)) for i, t in enumerate(tipos)]
        erros = validar.validar(g, CONTATO)
        self.assertTrue(any("so-texto" in e for e in erros))

    def test_tipos_desenhados_exigem_palavras(self):
        g = self._com_palavras("Sao quatro camadas.", {})
        g["momentos"][1]["motion"]["tipo"] = "camadas"
        self.assertTrue(any("`camadas` sem dados.palavras" in e
                            for e in validar.validar(g, CONTATO)))
