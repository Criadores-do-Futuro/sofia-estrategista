import re, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import estilos, legenda_hf as L


def tamanhos(corpo):
    return [int(x) for x in re.findall(r"font-size:(\d+)px", corpo)]


class TestHook(unittest.TestCase):
    def test_padrao_do_hook_e_a_serifa_aprovada_pelo_dono(self):
        # 2026-09-11: "o hook visual prefiro como estava antes do vox";
        # 2026-09-12: "use montserrat no hook visual" — a mesma voz da legenda
        pagina = L.html_legenda([], {"linhas": ["pov:", "Life with"]}, 1080, 1920, 5.0)
        self.assertIn("font-family:'Montserrat'", pagina)
        self.assertIn(estilos.HOOK["editorial"]["cor_destaque_texto"], pagina)

    def test_vox_continua_na_galeria_do_hook(self):
        pagina = L.html_legenda([], {"linhas": ["pov:", "Life with"]}, 1080, 1920, 5.0,
                                guia={"estilos": {"hook": "vox"}})
        self.assertIn("font-family:'Archivo Black'", pagina)
        self.assertIn(estilos.HOOK["vox"]["barra_destaque"], pagina)   # a barra âmbar
        self.assertIn("Archivo+Black", L.FONTES)

    def test_editorial_bate_com_a_referencia_aprovada(self):
        pagina = L.html_legenda([], {"linhas": ["pov:", "Life with"]}, 1080, 1920, 5.0,
                                guia={"estilos": {"hook": "editorial"}})
        self.assertIn("font-family:'Montserrat'", pagina)
        self.assertIn("font-weight:800", pagina)
        self.assertIn(estilos.HOOK["editorial"]["cor_destaque_texto"], pagina)
        self.assertIn(estilos.HOOK["editorial"]["cor_texto"], pagina)

    def test_primeira_linha_em_destaque_tem_a_classe_dest(self):
        tok = estilos.HOOK["vox"]
        corpo, _ = L._hook_html({"linhas": ["pov:", "Life", "with"]}, 1080, 1920, tok)
        self.assertEqual(corpo.count('class="hk dest"'), 1)
        self.assertIn('class="hk dest" id="hk0"', corpo)

    def test_destaque_nulo_deixa_so_uma_classe(self):
        tok = estilos.HOOK["vox"]
        corpo, _ = L._hook_html({"linhas": ["a", "b"], "destaque": None}, 1080, 1920, tok)
        self.assertNotIn("dest", corpo)

    def test_linha_maiuscula_longa_nao_estoura_a_margem_util(self):
        # regressao: a barra do estilo vox come espaco extra e a folga precisa
        # sobrar pra isso — sem ela a linha caiu por cima da margem de 6%
        tok = estilos.HOOK["vox"]
        corpo, _ = L._hook_html(
            {"linhas": ["pov:", "terminei o e-book", "em uma tarde"]}, 1080, 1920, tok)
        t = tamanhos(corpo)
        linha = "terminei o e-book"
        self.assertLessEqual(t[1] * 0.66 * (len(linha) + 1), 1080 * 0.82 + 1)

    def test_linha_serifada_longa_encolhe_para_caber(self):
        tok = estilos.HOOK["editorial"]
        corpo, _ = L._hook_html(
            {"linhas": ["curta", "uma linha comprida demais aqui"]}, 1080, 1920, tok)
        t = tamanhos(corpo)
        self.assertLessEqual(t[1] * 0.54 * len("uma linha comprida demais aqui"), 1080 * 0.88 + 1)

    def test_perna_descendente_afasta_a_linha_de_baixo_na_editorial(self):
        # a entrelinha apertada (0,8) so existe no estilo editorial; o vox usa 1,12
        tok = estilos.HOOK["editorial"]
        corpo, _ = L._hook_html({"linhas": ["pov:", "Life", "with"]}, 1080, 1920, tok)
        folgas = re.findall(r"margin-top:([\d.]+)em", corpo)
        self.assertEqual(folgas, ["0.00", "0.14", "0.00"])   # só abaixo do 'p'


class TestLegenda(unittest.TestCase):
    def test_padrao_da_casa_e_vox_com_barra(self):
        pagina = L.html_legenda([(0, 1000, "claude mudou tudo")], {}, 1080, 1920, 3.0)
        self.assertIn("font-family:'Archivo Black'", pagina)
        self.assertIn(estilos.LEGENDA["vox"]["barra"], pagina)

    def test_editorial_mantem_o_preset_sem_barra(self):
        pagina = L.html_legenda([(0, 1000, "claude mudou tudo")], {}, 1080, 1920, 3.0,
                                guia={"estilos": {"legenda": "editorial"}})
        self.assertIn("font-family:'Montserrat'", pagina)
        # a barra so aparece na regra `.lg .chip` (legenda); com editorial ela
        # some dali, mesmo que o hook (ainda em vox, por padrao) continue com a sua
        linha_lg = re.search(r"\.lg \.chip\{[^}]*\}", pagina).group()
        self.assertNotIn("background:", linha_lg)


if __name__ == "__main__":
    unittest.main()
