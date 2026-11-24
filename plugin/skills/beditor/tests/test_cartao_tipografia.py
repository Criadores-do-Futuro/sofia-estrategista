"""Os dois registros tipograficos do formato `analise`, sem render de video.

Decisao do dono em 2026-09-15, com duas capturas de referencia em mao:

    "use legendas assim quando for ilustrar pontos, partes, etapas, e use
    legendas assim para os dialogos"

A primeira captura e um titulo em duas vozes (sans geometrica negrito caixa
baixa + serifa italica menor encostada por baixo); a segunda e a legenda de
dialogo (sans regular, caixa baixa, branca, corpo pequeno, so sombra difusa).
Isso virou o registro `minusculo`, que passou a ser o padrao; o registro
anterior ficou como `explicativo` para os videos 14 e 15 renderizarem igual.

Estes testes existem porque a prova que temos do registro novo e um master de
111 segmentos do projeto 16 — cara, lenta e conferida com o olho. O que quebra
em silencio nao e o desenho, e a mecanica por baixo dele: o eixo de peso da
fonte variavel deixar de ser aplicado, a caixa do texto deixar de ser
normalizada, uma linha longa estourar a borda. Sao essas costuras que os testes
seguram, em imagem sintetica, em menos de um segundo.
"""
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import cartao


def quadro():
    """Fundo escuro liso: qualquer pixel diferente dele e tinta do texto."""
    return Image.new("RGB", (cartao.W, cartao.H), (20, 20, 20))


def pintado(img, base):
    """Colunas e linhas onde `img` difere de `base`. Devolve (ys, xs)."""
    dif = np.abs(np.array(img).astype(int) - np.array(base).astype(int)).sum(axis=2)
    return np.nonzero(dif)


def tinta(camada):
    """Linhas e colunas com alpha > 0 numa camada RGBA."""
    return np.nonzero(np.array(camada)[:, :, 3])


class TestTipografia(unittest.TestCase):
    def tearDown(self):
        # o registro e estado de modulo: um teste que troca e nao devolve
        # contamina o proximo, e o padrao do formato e o `minusculo`
        cartao.tipografia("minusculo")

    # a) o interruptor

    def test_tipografia_alterna_e_recusa_nome_desconhecido(self):
        self.assertEqual(cartao.tipografia(), "minusculo")   # o padrao do modulo
        self.assertEqual(cartao.tipografia("explicativo"), "explicativo")
        self.assertEqual(cartao.tipografia(), "explicativo")
        self.assertEqual(cartao.tipografia("minusculo"), "minusculo")
        # nome errado tem de explodir na hora: cair num registro qualquer em
        # silencio muda o master inteiro sem ninguem ver
        with self.assertRaises(ValueError):
            cartao.tipografia("maiusculo")
        self.assertEqual(cartao.tipografia(), "minusculo")

    # b) as duas fontes variaveis

    def test_as_duas_fontes_variaveis_estao_no_repositorio(self):
        self.assertTrue(cartao.SANS_VAR.exists(), f"falta {cartao.SANS_VAR.name}")
        self.assertTrue(cartao.SERIF_IT_VAR.exists(), f"falta {cartao.SERIF_IT_VAR.name}")

    def test_sans_e_serifa_carregam_as_familias_certas(self):
        # `_fonte_var` cai na fonte do sistema quando o arquivo nao abre, e essa
        # queda e silenciosa — sem este teste o registro novo renderizaria em
        # Arial sem ninguem notar ate ver o master
        familia_sans, _ = cartao.sans(100, 800).getname()
        self.assertEqual(familia_sans, "Montserrat")
        familia_serifa, estilo_serifa = cartao.serifa_italica(100, 400).getname()
        self.assertEqual(familia_serifa, "Fraunces")
        self.assertIn("Italic", estilo_serifa)

    # c) o eixo de peso

    def test_o_eixo_de_peso_da_sans_muda_o_desenho(self):
        # `set_variation_by_axes` falha calado dentro de um try/except. A prova
        # de que o peso chegou na letra e a largura: a mesma palavra no mesmo
        # corpo ocupa mais em 800 do que em 300
        d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        larga = d.textbbox((0, 0), "peso", font=cartao.sans(100, 800))[2]
        fina = d.textbbox((0, 0), "peso", font=cartao.sans(100, 300))[2]
        self.assertGreater(larga, fina)

    # d) e e) a caixa, nos dois registros

    def test_no_minusculo_a_legenda_baixa_a_caixa(self):
        # o `.upper()` saiu do `render_analise.py` e entrou no `legenda()`: quem
        # escreve a receita nao decide mais a caixa, o registro decide. Em
        # `minusculo` o texto desce, entao as duas grafias dao a MESMA imagem
        cartao.tipografia("minusculo")
        alta = cartao.legenda(quadro(), "TEXTO EM CAIXA ALTA")
        baixa = cartao.legenda(quadro(), "texto em caixa alta")
        self.assertEqual(alta.tobytes(), baixa.tobytes())
        self.assertNotEqual(alta.tobytes(), quadro().tobytes())   # escreveu algo

    def test_no_explicativo_a_legenda_sobe_a_caixa(self):
        # pelo mesmo motivo, e na direcao oposta: o registro antigo normaliza
        # para cima, e os videos 14 e 15 dependem disso para renderizar igual
        cartao.tipografia("explicativo")
        alta = cartao.legenda(quadro(), "TEXTO EM CAIXA ALTA")
        baixa = cartao.legenda(quadro(), "texto em caixa alta")
        self.assertEqual(alta.tobytes(), baixa.tobytes())

    def test_os_dois_registros_desenham_legendas_diferentes(self):
        # se os dois caissem no mesmo desenho, o campo `dados.estilos.legenda`
        # nao estaria escolhendo nada
        cartao.tipografia("minusculo")
        nova = cartao.legenda(quadro(), "a atencao")
        cartao.tipografia("explicativo")
        antiga = cartao.legenda(quadro(), "a atencao")
        self.assertNotEqual(nova.tobytes(), antiga.tobytes())

    # f) g) o titulo em duas vozes

    def test_titulo_duas_vozes_ocupa_altura_e_cabe_no_quadro(self):
        camada = Image.new("RGBA", (cartao.W, cartao.H), (0, 0, 0, 0))
        altura = cartao.titulo_duas_vozes(camada, ["temas", "universais"], 1,
                                          int(cartao.H * 0.30))
        self.assertGreater(altura, 0)
        ys, xs = tinta(camada)
        self.assertGreater(len(ys), 0, "o titulo nao escreveu nada")
        # a serifa sobe 22% do proprio corpo para encostar na sans: se o `y`
        # pedido estiver perto do topo, ela sai por cima do quadro
        self.assertGreater(ys.min(), 0)
        self.assertLess(ys.max(), cartao.H - 1)
        self.assertGreater(xs.min(), 0)
        self.assertLess(xs.max(), cartao.W - 1)

    def test_linha_longa_encolhe_ate_caber(self):
        # o titulo entra em 185 px e desce de 6 em 6 ate a sans mais larga
        # caber em 90% do quadro. Sem essa conta, «3 principios» saia pelas
        # bordas — foi o defeito que a conta corrigiu
        curto = Image.new("RGBA", (cartao.W, cartao.H), (0, 0, 0, 0))
        alt_curto = cartao.titulo_duas_vozes(curto, ["temas"], 0, 500)
        longo = Image.new("RGBA", (cartao.W, cartao.H), (0, 0, 0, 0))
        alt_longo = cartao.titulo_duas_vozes(longo, ["dominar a internet brasileira"], 0, 500)
        self.assertLess(alt_longo, alt_curto, "a linha longa nao encolheu")
        ys, xs = tinta(longo)
        # a tinta medida inclui o halo da sombra difusa, que vaza alguns pixels
        # para fora da letra — por isso a margem aqui e 96%, nao os 90% da conta
        self.assertLessEqual(xs.max() - xs.min(), int(cartao.W * 0.96))
        self.assertGreater(xs.min(), 0)
        self.assertLess(xs.max(), cartao.W - 1)

    # h) o marcador de capitulo

    def test_marcador_com_nome_longo_nao_estoura_a_borda_direita(self):
        # o nome do capitulo encolhe ate caber, como a legenda faz. Deixar
        # estourar corta a palavra na borda, que foi o defeito do primeiro
        # master do 14
        cartao.tipografia("minusculo")
        base = quadro()
        img = cartao.marcador(base.copy(), 1,
                              "um nome de capitulo bastante longo para testar a borda",
                              0.9, 2.0)
        ys, xs = pintado(img, base)
        self.assertGreater(len(xs), 0, "o marcador nao escreveu nada")
        self.assertLess(xs.max(), cartao.W - 1, "o nome encostou na borda direita")
        self.assertGreaterEqual(xs.min(), 0)
        self.assertLess(ys.max(), cartao.H - 1)

    def test_marcador_desenha_nos_dois_registros_e_sao_diferentes(self):
        base = quadro()
        cartao.tipografia("minusculo")
        nova = cartao.marcador(base.copy(), 1, "tema universal", 0.9, 2.0)
        cartao.tipografia("explicativo")
        antiga = cartao.marcador(base.copy(), 1, "tema universal", 0.9, 2.0)
        self.assertNotEqual(nova.tobytes(), base.tobytes())
        self.assertNotEqual(antiga.tobytes(), base.tobytes())
        self.assertNotEqual(nova.tobytes(), antiga.tobytes())


if __name__ == "__main__":
    unittest.main()
