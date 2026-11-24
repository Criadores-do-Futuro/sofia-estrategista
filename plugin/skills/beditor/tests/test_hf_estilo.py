import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import estilos, hf, hf_vox, montar

PLANO = {"id": "M01", "t0": 0, "t1": 3000, "tipo": "cartela", "texto": "uma frase curta",
         "entrada": "corte", "saida": "corte"}


class TestEstiloNoMotion(unittest.TestCase):
    def test_o_modulo_ja_nasce_com_o_padrao_da_casa(self):
        hf.aplicar_estilo()
        self.assertEqual(hf.ESTILO_ATUAL, "vox")
        self.assertTrue(hf.FUNDO and hf.FONTE_TITULO and hf.CARTAO)

    def test_trocar_de_estilo_troca_a_pagina_inteira(self):
        hf.aplicar_estilo("vox")
        vox = hf.html_do_plano(dict(PLANO))
        hf.aplicar_estilo("noturno")
        noturno = hf.html_do_plano(dict(PLANO))
        self.assertIn(estilos.MOTION["vox"]["tokens"]["FUNDO"], vox)
        self.assertNotIn(estilos.MOTION["vox"]["tokens"]["FUNDO"], noturno)
        self.assertIn(estilos.MOTION["noturno"]["tokens"]["FUNDO"], noturno)

    def test_noturno_continua_com_o_acabamento_medido_no_canal(self):
        # o estilo do canal nao pode ter mudado com a galeria: vinheta fechada,
        # meio-tom branco, grade de luz
        hf.aplicar_estilo("noturno")
        pagina = hf.html_do_plano(dict(PLANO))
        self.assertIn("rgba(0,0,0,0.92)", pagina)
        self.assertIn('opacity="0.16"', pagina)
        self.assertIn("rgba(255,255,255,0.03)", pagina)

    def test_papel_nao_leva_vinheta_preta_nem_grade_de_luz(self):
        hf.aplicar_estilo("vox")
        pagina = hf.html_do_plano(dict(PLANO))
        self.assertNotIn("rgba(0,0,0,0.92)", pagina)
        self.assertIn("display:none", pagina)                 # a grade some
        self.assertIn(estilos.acabamento("vox")["halftone_cor"], pagina)

    def test_imagem_gerada_carrega_a_materia_do_estilo(self):
        mo = {"tipo": "objeto", "ideia": "uma poltrona de avião"}
        for nome in estilos.MOTION:
            e = estilos.MOTION[nome]
            prompt = montar.prompt_de_imagem(mo, e["materia"], e.get("moldes"))
            self.assertIn(e["materia"][:40], prompt)

    def test_vox_desenha_colagem_e_nao_o_cartao_do_noturno(self):
        # o dono recusou a primeira versao: "nao tem nada de parecido com o vox
        # style" — era o layout do noturno repintado. Colagem e composicao, nao cor.
        hf.aplicar_estilo("vox")
        pagina = hf.html_do_plano({"id": "M1", "t0": 0, "t1": 4000, "tipo": "cartela",
                                   "linhas": ["uma linha", "outra linha"], "acender": "outra linha"})
        for peca in ("grade-tec", "grifo", "anot", "Playfair Display", "Courier Prime"):
            self.assertIn(peca, pagina, peca)
        # o CSS da tipografia do noturno viaja no cabecalho de toda pagina; o que
        # importa e que ela nao DESENHA nada aqui — por isso o teste olha o corpo
        corpo = pagina.split("<body>", 1)[1]
        self.assertNotIn("matte-text", corpo)
        self.assertIn("manchete", corpo)

    def test_noturno_continua_com_o_desenho_dele(self):
        hf.aplicar_estilo("noturno")
        pagina = hf.html_do_plano({"id": "M1", "t0": 0, "t1": 4000, "tipo": "cartela",
                                   "texto": "uma linha"})
        corpo = pagina.split("<body>", 1)[1]
        self.assertIn("matte-text", corpo)
        self.assertNotIn("grade-tec", corpo)

    def test_asset_no_vox_vira_recorte_com_fita(self):
        hf.aplicar_estilo("vox")
        pagina = hf.html_do_plano({"id": "M2", "t0": 0, "t1": 4000, "tipo": "objeto",
                                   "asset": "x.jpg", "texto": "um rótulo"})
        self.assertIn("recorte", pagina)
        self.assertIn("fita", pagina)
        self.assertIn("grayscale(1)", pagina)        # arquivo em preto e branco
        self.assertIn("clip-path:polygon", pagina)   # a borda de tesoura

    def test_molde_proprio_do_estilo_vence_o_molde_generico(self):
        mo = {"tipo": "personagem", "ideia": "alguém esperando"}
        vox = montar.prompt_de_imagem(mo, "", estilos.MOTION["vox"]["moldes"])
        noturno = montar.prompt_de_imagem(mo, "", estilos.MOTION["noturno"]["moldes"])
        self.assertIn("paper cutout silhouette", vox)
        self.assertIn("featureless smooth white humanoid", noturno)


class TestGestosMenores(unittest.TestCase):
    """Os quatro gestos que separam a colagem animada do gráfico de template.
    A decupagem está em `skills/motion-vox/referencias/gestos-menores.md`."""

    def setUp(self):
        hf.aplicar_estilo("vox")

    def _pagina(self, tipo="cartela", **extra):
        p = {"id": "M1", "t0": 0, "t1": 4000, "tipo": tipo, "texto": "uma linha"}
        p.update(extra)
        return hf.html_do_plano(p)

    def test_passos_segura_o_valor_por_dois_frames(self):
        # 0.5s a 30fps = 15 frames; on twos = 8 degraus (arredondado)
        self.assertEqual(hf_vox.passos(0.5), "steps(8)")
        self.assertEqual(hf_vox.passos(0.4), "steps(6)")
        # entrada curtíssima nunca cai abaixo de 2 degraus, senão vira corte
        self.assertEqual(hf_vox.passos(0.02), "steps(2)")

    def test_tipografia_de_apoio_entra_em_passos(self):
        pagina = self._pagina()
        self.assertIn("steps(", pagina)

    def test_a_manchete_em_serifa_nao_e_travada(self):
        # corpo grande em passos lê como falha de render, não como escolha
        _, _, js = hf_vox.cartela({"linhas": ["uma", "duas"], "acender": "duas"})
        ln = [t for t in js.split(";") if "'.ln'" in t]
        self.assertTrue(ln, "a manchete deveria ter uma entrada própria")
        self.assertNotIn("steps(", ln[0])

    def test_o_marca_texto_entra_mordido_e_nao_varrendo(self):
        _, _, js = hf_vox.cartela({"linhas": ["uma", "duas"], "acender": "duas"})
        self.assertIn("keyframes", js)          # avanço em pedaços desiguais
        self.assertIn("0.18,0.22", js)          # o par que segura entre passos

    def test_o_fundo_se_move_uma_vez_so_por_cena(self):
        for tipo in ("cartela", "palavras", "dado", "indice", "camadas"):
            _, _, js = hf_vox.CORPOS[tipo]({"texto": "x", "palavras": ["a", "b"]})
            self.assertEqual(js.count(".fibra"), 1, f"{tipo}: fundo móvel duplicado")

    def test_a_fibra_e_maior_que_o_quadro(self):
        # com inset:0 o passo do fundo móvel exporia a borda do papel
        self.assertIn("inset:-8%", hf_vox.css_papel())

    def test_a_lente_so_afeta_a_borda(self):
        css = hf_vox.css_verniz()
        self.assertIn("backdrop-filter", css)
        self.assertIn("mask-image", css)        # o miolo é mascarado para fora
        self.assertIn("radial-gradient", css)

    def test_toda_composicao_do_vox_leva_a_lente(self):
        for tipo in ("cartela", "palavras", "dado", "indice", "camadas", "objeto"):
            corpo, _, _ = hf_vox.CORPOS[tipo]({"texto": "x", "palavras": ["a"],
                                               "asset": "a.png"})
            self.assertIn('class="lente"', corpo, f"{tipo}: sem borda de lente")

    def test_o_noturno_nao_herda_nada_disso(self):
        hf.aplicar_estilo("noturno")
        pagina = self._pagina()
        self.assertNotIn('class="lente"', pagina)


class TestPosicionamento(unittest.TestCase):
    """O destaque circula a palavra certa e o texto cabe na área segura?

    Este estilo erra posição com facilidade: a colagem gira e rasga de propósito,
    e toda medida calculada em Python descola da métrica real da fonte assim que
    o texto quebra linha. Ler o código não acusa — o caso curto sempre passa. Só
    medindo no navegador, que é o que `conferir_layout.py` faz.
    """

    def test_nenhuma_composicao_do_vox_sai_torta(self):
        try:
            import conferir_layout
        except ImportError as e:                      # pragma: no cover
            self.skipTest(f"conferir_layout indisponível: {e}")
        try:
            problemas = conferir_layout.conferir("vox")
        except Exception as e:                        # pragma: no cover
            # sem browser ou sem rede (o gsap vem de CDN) o teste não tem o que
            # medir — pular é honesto; passar em silêncio não seria.
            self.skipTest(f"sem navegador para medir: {type(e).__name__}: {e}")
        self.assertEqual(problemas, [], "\n" + "\n".join(problemas))

    def _regra_da_anot(self, css):
        return sorted(l.strip() for l in css.splitlines() if ".anot.elastica" in l)

    def test_a_posicao_da_elipse_nao_depende_do_conteudo(self):
        """O invariante que tranca a regressão.

        Enquanto a elipse saía de `acesa * 114` e `ativo * 122`, o CSS mudava
        conforme o texto — e era exatamente aí que ela circulava a linha errada.
        Ancorada no alvo, a regra é a MESMA para qualquer conteúdo: quem move a
        elipse passa a ser a caixa real do elemento, medida pelo navegador.
        """
        curto = hf_vox.cartela({"linhas": ["ab", "cd"], "acender": "cd"})[1]
        longo = hf_vox.cartela({"linhas": ["uma linha bem mais longa que a outra",
                                           "e a que importa de verdade aqui"],
                                "acender": "importa"})[1]
        primeira = hf_vox.cartela({"linhas": ["a que importa", "b", "c"],
                                   "acender": "importa"})[1]
        self.assertTrue(self._regra_da_anot(curto), "a cartela perdeu a elipse elástica")
        self.assertEqual(self._regra_da_anot(curto), self._regra_da_anot(longo))
        self.assertEqual(self._regra_da_anot(curto), self._regra_da_anot(primeira))

        base = {"palavras": ["um", "dois", "tres"]}
        p = hf_vox.indice({**base, "acender": "um"})[1]
        u = hf_vox.indice({**base, "acender": "tres"})[1]
        self.assertTrue(self._regra_da_anot(p), "o índice perdeu a elipse elástica")
        self.assertEqual(self._regra_da_anot(p), self._regra_da_anot(u))

    def test_a_elipse_ancorada_estica_sem_engordar_o_traco(self):
        svg = hf_vox.anotacao("elipse", 760, 200, elastica=True)
        self.assertIn('preserveAspectRatio="none"', svg)      # estica nos dois eixos
        self.assertIn("non-scaling-stroke", svg)              # a caneta não engorda
        self.assertNotIn("width=", svg)                       # quem dá a medida é o alvo


if __name__ == "__main__":
    unittest.main()
