"""O catálogo da biblioteca lê o nome certo, mede o que importa e não remede o que não mudou.

Três coisas que, erradas, custam caro no formato `analise`:

  - o nome da faixa vira `titulo`/`autor` no `provas.json` — errar aqui é
    publicar procedência errada;
  - o índice de eventos é o que decide qual música pode ser cama; um contador
    que dispara no silêncio de cabeça ou ignora a entrada da bateria escolhe a
    faixa errada em silêncio;
  - o catálogo de 185 faixas leva minutos para medir; se a chave de conteúdo
    falhar, cada `catalogar` paga tudo de novo.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import biblioteca  # noqa: E402


class TestNomeMusica(unittest.TestCase):
    def test_padrao_completo_com_uploader_do_youtube(self):
        d = biblioteca.parse_nome_musica(
            "17 Felicidade_Alegria Skank - Garota Nacional (Instrumental) - Playback Music (youtube).mp3",
            "FELICIDADE ALEGRIA")
        self.assertEqual(d["numero"], 17)
        self.assertEqual(d["clima"], "FELICIDADE ALEGRIA")
        self.assertEqual(d["artista"], "Skank")
        self.assertEqual(d["titulo"], "Garota Nacional")
        self.assertEqual(d["versao"], "Instrumental")
        self.assertEqual(d["canal"], "Playback Music")
        self.assertEqual(d["origem"], "youtube")
        self.assertEqual(d["licenca"], "desconhecida")
        self.assertEqual(d["risco"], "content-id")
        self.assertFalse(d["vocal"])

    def test_titulo_antes_do_artista_quando_o_parentese_marca_o_titulo(self):
        d = biblioteca.parse_nome_musica("13 Determinação_Força In the End (Instrumental) - Linkin Park.mp3", "X")
        self.assertEqual((d["artista"], d["titulo"]), ("Linkin Park", "In the End"))
        self.assertEqual(d["origem"], "desconhecida")
        self.assertIsNone(d["canal"])

    def test_id_do_youtube_entre_colchetes_conta_como_origem_youtube(self):
        d = biblioteca.parse_nome_musica(
            "12 Determinação_Força Imagine Dragons Believer Official Instrumental [YVGBQ-vdOvI].mp3", "X")
        self.assertEqual(d["origem"], "youtube")
        self.assertEqual(d["titulo"], "Imagine Dragons Believer")
        self.assertEqual(d["versao"], "Instrumental")

    def test_karaoke_e_caixa_alta(self):
        d = biblioteca.parse_nome_musica(
            "18 Nostalgia_Saudade MILTON NASCIMENTO - TRAVESSIA ( KARAOKE ) - Karaokê Club (youtube).mp3", "X")
        self.assertEqual(d["versao"], "Karaokê")
        self.assertEqual(d["titulo"], "TRAVESSIA")
        self.assertEqual(d["canal"], "Karaokê Club")

    def test_sem_vocal_nao_e_vocal(self):
        self.assertFalse(biblioteca.tem_vocal("Killing In The Name (Instrumental NO VOCAL BLEED)"))
        self.assertFalse(biblioteca.tem_vocal("Paciência - Lenine - Backtracking sem Vocal"))
        self.assertTrue(biblioteca.tem_vocal("Faixa com vocal guia"))

    def test_nome_sem_numero_nem_separador_nao_derruba(self):
        d = biblioteca.parse_nome_musica("Anunciação.mp3", "FELICIDADE ALEGRIA")
        self.assertIsNone(d["numero"])
        self.assertEqual(d["titulo"], "Anunciação")
        self.assertIsNone(d["versao"])


class TestMarcaLogo(unittest.TestCase):
    def test_marcas_do_acervo(self):
        casos = {"logo-chatgpt-01.webp": "chatgpt", "kling-ai-logo.jpg": "kling",
                 "logo-davinci-resolve.png": "davinci", "logo-gemini-flash.webp": "gemini",
                 "logo-claude-ai.png": "claude", "logo-premiere-pro.png": "premiere",
                 "logo-kling-pagamento.png": "kling", "logo-wan-ai.jpg": "wan"}
        for nome, marca in casos.items():
            self.assertEqual(biblioteca.marca_do_nome(nome), marca, nome)


class TestPixFmt(unittest.TestCase):
    def test_alfa_pelo_pix_fmt(self):
        self.assertTrue(biblioteca.pix_fmt_tem_alfa("yuva420p"))
        self.assertTrue(biblioteca.pix_fmt_tem_alfa("rgba"))
        self.assertFalse(biblioteca.pix_fmt_tem_alfa("yuv420p"))
        self.assertFalse(biblioteca.pix_fmt_tem_alfa(None))


class TestEventos(unittest.TestCase):
    """Série sintética a 100 ms; cada 10 amostras é uma janela de 1 s."""

    def test_pad_continuo_da_zero(self):
        serie = [-20.0] * 600          # 60 s parado
        self.assertEqual(biblioteca.eventos_por_minuto(serie), 0.0)

    def test_entrada_de_bateria_conta_e_a_saida_do_silencio_nao(self):
        # 2 s de silêncio digital, 28 s a −30, 30 s a −18: um único evento (o salto de 12 dB)
        serie = [-120.7] * 20 + [-30.0] * 280 + [-18.0] * 300
        self.assertEqual(biblioteca.eventos_por_minuto(serie), 1.0)

    def test_salto_abaixo_de_6_db_nao_conta(self):
        serie = [-30.0] * 300 + [-25.0] * 300
        self.assertEqual(biblioteca.eventos_por_minuto(serie), 0.0)

    def test_transiente_de_uma_amostra_e_apagado_pela_media(self):
        # uma baqueta de 100 ms a −5 dentro de uma janela a −30 sobe a média 2,5 dB: não é evento
        serie = [-30.0] * 300 + [-5.0] + [-30.0] * 299
        self.assertEqual(biblioteca.eventos_por_minuto(serie), 0.0)

    def test_normaliza_por_minuto(self):
        # 30 s com dois saltos → 4 por minuto
        serie = [-30.0] * 100 + [-20.0] * 100 + [-30.0] * 50 + [-20.0] * 50
        self.assertEqual(biblioteca.eventos_por_minuto(serie), 4.0)


class TestCama(unittest.TestCase):
    def _item(self, arq, ev, lra=5.0, dur=200.0, vocal=False, clima="A"):
        return {"arq": arq, "classe": "audio", "eventosMin": ev, "lra": lra, "dur": dur, "vocal": vocal,
                "clima": clima, "titulo": arq, "artista": "x", "lufs": -14.0}

    def test_ordena_por_eventos_depois_lra_e_filtra_curtas_e_vocais(self):
        itens = {
            "a": self._item("a", 2.0),
            "b": self._item("b", 0.5, lra=9.0),
            "c": self._item("c", 0.5, lra=3.0),
            "curta": self._item("curta", 0.0, dur=60.0),
            "voc": self._item("voc", 0.0, vocal=True),
        }
        esc = biblioteca.escolher_cama(itens, n=5)
        self.assertEqual([v["arq"] for v in esc], ["c", "b", "a"])

    def test_bloco_do_plano_tem_o_formato_do_render(self):
        bloco = biblioteca.bloco_plano("/lib", [self._item("Faixa Um", 0.1)])
        (k, m), = bloco["musicas"].items()
        self.assertTrue(k.isalnum())
        self.assertEqual(m["arq"], "/lib/Faixa Um")
        self.assertEqual(m["tipo"], "trilha")
        self.assertEqual(m["src"], 0.0)
        self.assertIn("licenca", m)
        for chave in ("titulo", "autor", "url"):
            self.assertIn(chave, m)


class TestSfx(unittest.TestCase):
    def test_gatilhos_sem_som_explicam_o_motivo(self):
        for g in ("pb", "destaque", "modo1"):
            arq, motivo = biblioteca.sfx_para(g, {}, None)
            self.assertIsNone(arq)
            self.assertTrue(motivo)

    def test_marcador_e_hit_pelo_catalogo(self):
        itens = {"Hit.mp3": {"arq": "Hit.mp3", "classe": "audio"}, "Woosh Fast.mp3": {"arq": "Woosh Fast.mp3", "classe": "audio"}}
        arq, _ = biblioteca.sfx_para("marcador", itens, "/sfx")
        self.assertEqual(str(arq), "/sfx/Hit.mp3")
        arq, _ = biblioteca.sfx_para("cartao", itens, "/sfx")
        self.assertEqual(str(arq), "/sfx/Woosh Fast.mp3")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "sem ffmpeg")
class TestIncremental(unittest.TestCase):
    """Dois arquivos de 2 s gerados pelo lavfi; a segunda rodada não pode medir de novo."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="biblioteca-"))
        for nome, freq in (("Hit.wav", 440), ("Woosh Fast.wav", 220)):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration=2",
                            "-ar", "48000", str(self.tmp / nome)], check=True)
        (self.tmp / "README.md").write_text("ignorado")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_segunda_rodada_reaproveita_e_terceira_remede_o_que_mudou(self):
        cat, novos, erros = biblioteca.catalogar_pasta(self.tmp, "sfx", n=1)
        self.assertEqual(novos, 2)
        self.assertEqual(erros, [])
        self.assertTrue((self.tmp / "catalogo.json").exists())
        hit = cat["itens"]["Hit.wav"]
        self.assertAlmostEqual(hit["dur"], 2.0, delta=0.1)
        self.assertEqual(hit["sr"], 48000)
        self.assertIsInstance(hit["lufs"], float)
        self.assertEqual(hit["eventosMin"], 0.0)   # seno constante: nenhum evento

        original = biblioteca.medir_audio
        chamadas = []
        biblioteca.medir_audio = lambda arq: chamadas.append(arq) or original(arq)
        try:
            cat2, novos2, _ = biblioteca.catalogar_pasta(self.tmp, "sfx", n=1)
            self.assertEqual(novos2, 0)
            self.assertEqual(chamadas, [])
            self.assertEqual(cat2["itens"]["Hit.wav"]["lufs"], hit["lufs"])

            # renomear não remede; trocar o conteúdo remede só aquele
            os.rename(self.tmp / "Woosh Fast.wav", self.tmp / "Woosh.wav")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=880:duration=2",
                            "-ar", "48000", str(self.tmp / "Hit.wav")], check=True)
            cat3, novos3, _ = biblioteca.catalogar_pasta(self.tmp, "sfx", n=1)
            self.assertEqual(novos3, 1)
            self.assertEqual([Path(c).name for c in chamadas], ["Hit.wav"])
            self.assertIn("Woosh.wav", cat3["itens"])
            self.assertNotIn("Woosh Fast.wav", cat3["itens"])

            # --forcar remede tudo
            chamadas.clear()
            _, novos4, _ = biblioteca.catalogar_pasta(self.tmp, "sfx", forcar=True, n=1)
            self.assertEqual(novos4, 2)
        finally:
            biblioteca.medir_audio = original

    def test_arquivo_ilegivel_entra_com_erro_sem_derrubar(self):
        (self.tmp / "quebrado.wav").write_bytes(b"isto nao e audio")
        cat, _, erros = biblioteca.catalogar_pasta(self.tmp, "sfx", n=1)
        self.assertEqual(len(erros), 1)
        self.assertIn("erro", cat["itens"]["quebrado.wav"])
        self.assertNotIn("erro", cat["itens"]["Hit.wav"])
        j = json.loads((self.tmp / "catalogo.json").read_text())
        self.assertEqual(len(j["itens"]), 3)


if __name__ == "__main__":
    unittest.main()
