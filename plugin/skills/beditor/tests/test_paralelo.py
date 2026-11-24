"""O render e a geracao de imagem acontecem em paralelo, e uma falha e isolada.

Medido pelo dono em 90 dias: motion graphics era a etapa mais demorada da
producao (4,8h). O motivo nao era o modelo — era que cada cena subia um browser
em fila e cada imagem era uma espera de rede em fila, sem que nada disso
disputasse recurso compartilhado.

Estes testes trancam as duas propriedades que importam: o trabalho sai junto, e
uma cena que falha nao leva as outras embora.
"""
import sys
import time
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import hf  # noqa: E402

ESPERA = 0.25


class _Saida:
    """o suficiente para o `out.stat().st_size` do laco de impressao"""

    def stat(self):
        return types.SimpleNamespace(st_size=4096)


class TestRenderParalelo(unittest.TestCase):
    def setUp(self):
        self.original = hf.render_plano
        self.vistos = []

    def tearDown(self):
        hf.render_plano = self.original

    def _dublê(self, falha_em=None):
        """Troca o render por uma espera: e o que a chamada real faz enquanto o
        browser sobe. O que se testa aqui e o laco, nao o hyperframes."""
        def fn(p, projeto, saida, W, H, fps=None):
            self.vistos.append(p["id"])
            time.sleep(ESPERA)
            if p["id"] == falha_em:
                raise RuntimeError("render falhou (proposital)")
            return _Saida()
        return fn

    def test_as_cenas_saem_junto_e_nao_em_fila(self):
        alvos = [{"id": f"M{i:02d}", "tipo": "cartela"} for i in range(6)]
        hf.render_plano = self._dublê()

        t = time.time()
        hf._render_todos(alvos, None, None, 0, 0, 1)
        sequencial = time.time() - t

        t = time.time()
        hf._render_todos(alvos, None, None, 0, 0, 3)
        paralelo = time.time() - t

        self.assertEqual(len(self.vistos), 12, "toda cena tem de ser renderizada")
        # 6 cenas em 3 vias sao 2 rodadas, nao 6. Margem larga de proposito: o
        # que falharia aqui e a volta ao laco sequencial, nao ruido de medicao.
        self.assertLess(paralelo, sequencial * 0.6,
                        f"paralelo {paralelo:.2f}s não ganhou de {sequencial:.2f}s")

    def test_uma_cena_que_falha_nao_derruba_as_outras(self):
        alvos = [{"id": f"M{i:02d}", "tipo": "cartela"} for i in range(5)]
        hf.render_plano = self._dublê(falha_em="M02")

        with self.assertRaises(RuntimeError) as e:
            hf._render_todos(alvos, None, None, 0, 0, 3)

        # o erro nomeia quem falhou, e so e levantado DEPOIS de todas tentarem:
        # antes, a primeira falha jogava fora o trabalho pronto das seguintes.
        self.assertIn("M02", str(e.exception))
        self.assertEqual(len(self.vistos), 5, "as outras quatro tinham de rodar")

    def test_o_padrao_nao_sufoca_a_maquina(self):
        # cada render sobe um browser: passar dos nucleos so faz as cenas
        # disputarem o mesmo processador, e o teto e de memoria.
        n = hf._paralelo_padrao()
        self.assertGreaterEqual(n, 1)
        self.assertLessEqual(n, 4)


if __name__ == "__main__":
    unittest.main()
