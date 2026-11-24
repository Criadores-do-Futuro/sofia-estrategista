import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import montar

FIX = Path(__file__).resolve().parent / "fixtures"
GUIA = json.loads((FIX / "guia_bom.json").read_text(encoding="utf-8"))
PAL = [{"palavra": "primeira", "deMs": 500, "ateMs": 1500}, {"palavra": "frase", "deMs": 1600, "ateMs": 2500},
       {"palavra": "aqui.", "deMs": 2600, "ateMs": 4000},
       {"palavra": "segunda", "deMs": 5500, "ateMs": 6500}, {"palavra": "frase", "deMs": 6600, "ateMs": 8000},
       {"palavra": "longa", "deMs": 8100, "ateMs": 9500}]


class TestMontar(unittest.TestCase):
    def test_pausa_protegida_por_jcut_nao_e_cortada(self):
        # pausa 4000-5500 (1,5 s > 1,3) mas M02 tem entraAntesMs 700 -> protegida
        t = montar.trechos_mantidos(GUIA, PAL)
        self.assertEqual(t, [{"brutoDe": 0, "brutoAte": 10000}])

    def test_pausa_longa_e_cortada_com_pad(self):
        g = json.loads(json.dumps(GUIA)); g["momentos"][1]["motion"]["entraAntesMs"] = 0
        t = montar.trechos_mantidos(g, PAL)
        self.assertEqual(t, [{"brutoDe": 0, "brutoAte": 4600}, {"brutoDe": 4900, "brutoAte": 10000}])

    def test_corte_do_diretor_atravessa_palavra_e_sobrevive(self):
        """A falsa partida SEMPRE atravessa a palavra do transcript — e o que
        ela e. Num take real (2026-09-11) o Whisper colapsou a gagueira inteira
        numa palavra de 2,8 s; o diretor mandou cortar ali, e a guarda fonetica
        desfez a decisao em silencio: o video saiu com as duas tentativas. A
        guarda vale para a pausa que o script tira sozinho, nunca para o momento
        `cortar` que alguem escreveu e justificou."""
        g = json.loads(json.dumps(GUIA))
        g["momentos"] = [
            {"id": "M01", "deMs": 0, "ateMs": 2000, "decisao": "aroll", "porque": "x"},
            {"id": "M02", "deMs": 2000, "ateMs": 7000, "decisao": "cortar", "porque": "gaguejou"},
            {"id": "M03", "deMs": 7000, "ateMs": 10000, "decisao": "aroll", "porque": "x"},
        ]
        # 2000 cai dentro de «frase» (1600-2500) e 7000 dentro de «frase» (6600-8000):
        # as duas bordas atravessam palavra, que e exatamente o caso do bug.
        t = montar.trechos_mantidos(g, PAL)
        self.assertEqual(len(t), 2, "o corte do diretor foi desfeito")
        # O corte fica onde o diretor mandou, mas a borda nao pode cair DENTRO da
        # palavra seguinte («frase» comeca em 1600): `_respiro_nas_bordas` puxa a
        # saida para 40 ms antes dela — 2026-09-12, o dono ouviu «propria» decepado.
        self.assertEqual(t[0]["brutoAte"], 1600 - montar.FOLGA_VIZINHA_MS)
        self.assertEqual(t[1]["brutoDe"], 7000)

    def test_pausa_que_o_script_tira_continua_protegida(self):
        # o contrario do teste acima: sem `cortar` escrito no guia, a guarda manda
        t = montar._preservar_pronuncia(
            [{"brutoDe": 0, "brutoAte": 2000}, {"brutoDe": 7000, "brutoAte": 10000}], PAL)
        self.assertEqual(len(t), 1)

    def test_emenda_exata_na_palavra_e_restaurada(self):
        # ASR diz onde a palavra termina/comeca, mas a cauda e o ataque do
        # fonema precisam de margem. Sem ela, a falsa partida fica no video.
        t = montar._preservar_pronuncia(
            [{"brutoDe": 0, "brutoAte": 4000},
             {"brutoDe": 5500, "brutoAte": 10000}], PAL)
        self.assertEqual(t, [{"brutoDe": 0, "brutoAte": 10000}])

    def test_emenda_com_600ms_de_margem_e_preservada(self):
        t = montar._preservar_pronuncia(
            [{"brutoDe": 0, "brutoAte": 4600},
             {"brutoDe": 4900, "brutoAte": 10000}], PAL)
        self.assertEqual(t, [{"brutoDe": 0, "brutoAte": 4600},
                             {"brutoDe": 4900, "brutoAte": 10000}])

    def test_400ms_nao_basta_e_emenda_e_restaurada(self):
        t = montar._preservar_pronuncia(
            [{"brutoDe": 0, "brutoAte": 4400},
             {"brutoDe": 5100, "brutoAte": 10000}], PAL)
        self.assertEqual(t, [{"brutoDe": 0, "brutoAte": 10000}])

    def test_limite_no_meio_da_palavra_e_restaurado(self):
        t = montar._preservar_pronuncia(
            [{"brutoDe": 0, "brutoAte": 3900},
             {"brutoDe": 5600, "brutoAte": 10000}], PAL)
        self.assertEqual(t, [{"brutoDe": 0, "brutoAte": 10000}])

    def test_cortar_remove_momento(self):
        g = json.loads(json.dumps(GUIA)); g["momentos"][1]["decisao"] = "cortar"; del g["momentos"][1]["motion"]
        t = montar.trechos_mantidos(g, PAL)
        self.assertEqual(t, [{"brutoDe": 0, "brutoAte": 5500}])

    def test_tabela_e_conversao(self):
        tab = montar.tabela_corte([{"brutoDe": 0, "brutoAte": 4250}, {"brutoDe": 5250, "brutoAte": 10000}])
        self.assertEqual(tab[1]["corteDe"], 4250)
        self.assertEqual(montar.bruto_para_corte(tab, 6000), 5000)
        self.assertEqual(montar.bruto_para_corte(tab, 4800), 4250)  # dentro da pausa removida

    def test_objeto_recebe_prompt_da_ideia(self):
        g = json.loads(json.dumps(GUIA))
        mo = g["momentos"][1]["motion"]
        mo["tipo"] = "objeto"; mo["dados"] = {}
        mo["ideia"] = "dez paineis de papel creme virados de costas"
        mo["familia"] = "promessa"; mo["estado"] = "o primeiro painel vira"
        tab = montar.tabela_corte(montar.trechos_mantidos(g, PAL))
        ps = montar.planos_do_guia(g, {}, tab)
        self.assertIn("dez paineis de papel creme", ps[1]["prompt"])
        self.assertIn("o primeiro painel vira", ps[1]["prompt"])
        self.assertEqual(ps[0]["prompt"], "")   # fala nao leva prompt

    def test_planos_do_guia(self):
        tab = montar.tabela_corte(montar.trechos_mantidos(GUIA, PAL))
        ps = montar.planos_do_guia(GUIA, {}, tab)
        self.assertEqual([p["tipo"] for p in ps], ["fala", "palavras"])
        self.assertEqual(ps[1]["t0"], 5500 - 700)      # entraAntesMs aplicado
        self.assertEqual(ps[0]["t1"], ps[1]["t0"])     # vizinho cede
        self.assertEqual(ps[1]["palavras"], ["segunda", "longa"])
        self.assertFalse(ps[1]["legenda"])


if __name__ == "__main__":
    unittest.main()
