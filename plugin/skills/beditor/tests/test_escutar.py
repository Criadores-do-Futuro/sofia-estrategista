import json, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import escutar


def wav_com_blocos(caminho, blocos, duracao=6.0):
    """Tom onde ha fala, silencio no resto. `blocos` em segundos."""
    filtros = []
    for de, ate in blocos:
        filtros.append(f"sine=frequency=220:duration={ate - de}"
                       f",adelay={int(de * 1000)}|{int(de * 1000)}")
    entradas = []
    for f in filtros:
        entradas += ["-f", "lavfi", "-i", f]
    n = len(filtros)
    mistura = "".join(f"[{i}:a]" for i in range(n)) + f"amix=inputs={n}:normalize=0[a]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *entradas,
                    "-filter_complex", mistura, "-map", "[a]",
                    "-t", str(duracao), "-ar", "8000", "-ac", "1",
                    str(caminho)], check=True)
    return caminho


def transcript(palavras):
    return {"text": "", "language": "pt", "segments": [
        {"start": palavras[0][1], "end": palavras[-1][2], "text": "",
         "words": [{"word": w, "start": a, "end": b} for w, a, b in palavras]}]}


class TestFalsaPartida(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _escutar(self, blocos, palavras):
        w = wav_com_blocos(self.dir / "a.wav", blocos)
        j = self.dir / "a.json"
        j.write_text(json.dumps(transcript(palavras)), encoding="utf-8")
        return escutar.escutar(w, j)

    def test_acha_a_tentativa_que_o_transcript_engoliu(self):
        # e a forma exata do caso real: fala, silencio de 1,2 s, fala de novo,
        # e o transcript conta UMA palavra em cima dos dois blocos
        achados = self._escutar([(1.0, 1.6), (2.8, 4.2)],
                                [("bom", 0.5, 1.0), ("treinar", 1.0, 4.2), ("dia", 4.2, 4.6)])
        self.assertEqual(len(achados), 1)
        a = achados[0]
        self.assertEqual(a["tipo"], "falsa-partida")
        # O corte comeca no inicio da TENTATIVA, nao da palavra engolida: as
        # palavras coladas antes dela fazem parte do que foi dito e repetido.
        # No take real isso e a diferenca entre cortar «treinar» e cortar
        # «Entao eu decidi treinar» — so a segunda tira a gagueira.
        self.assertAlmostEqual(a["deMs"], 500, delta=60)
        self.assertIn("bom", a["texto"])
        self.assertGreater(a["ateMs"], 2000)
        self.assertLess(a["ateMs"], 2800)

    def test_o_corte_para_no_ponto_final_da_frase_anterior(self):
        # a frase de cima terminou; ela nao entra no corte por estar colada
        achados = self._escutar([(1.0, 1.6), (2.8, 4.2)],
                                [("pronto.", 0.5, 0.98), ("treinar", 1.0, 4.2)])
        self.assertEqual(len(achados), 1)
        self.assertAlmostEqual(achados[0]["deMs"], 1000, delta=60)
        self.assertNotIn("pronto", achados[0]["texto"])

    def test_palavra_arrastada_sem_pausa_dentro_nao_e_falsa_partida(self):
        # "naaaaao" longo e uma palavra so, com voz continua: nada a cortar
        achados = self._escutar([(1.0, 3.4)],
                                [("nao", 1.0, 3.4), ("mesmo", 3.5, 3.9)])
        self.assertEqual(achados, [])

    def test_silencio_puro_dentro_da_palavra_nao_inventa_corte(self):
        achados = self._escutar([(1.0, 1.3)],
                                [("oi", 1.0, 3.6), ("tchau", 3.7, 4.0)])
        self.assertEqual(achados, [])


class TestRepeticaoNoTexto(unittest.TestCase):
    def _so_texto(self, palavras):
        # exercita a deteccao literal sem passar pelo audio
        return escutar.repeticoes_literais(
            [{"word": w, "start": a, "end": b} for w, a, b in palavras])

    def test_acha_a_frase_que_recomeca(self):
        p = [("Entao", 1.0, 1.3), ("eu", 1.3, 1.4), ("decidi", 1.4, 1.9),
             ("Entao", 2.6, 2.9), ("eu", 2.9, 3.0), ("decidi", 3.0, 3.5),
             ("treinar", 3.5, 4.0), ("tudo", 4.0, 4.4)]
        a = self._so_texto(p)
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0]["tipo"], "repeticao")
        self.assertEqual(a[0]["deMs"], 1000)

    def test_anafora_nao_e_gagueira(self):
        # "ele ja faz a pesquisa. Ele ja faz a edicao. Ele ja faz o corte" —
        # falso positivo real de 2026-09-11. Duas guardas derrubam: a primeira
        # tentativa FECHOU com ponto, e o n-grama volta tres vezes.
        p = [("Ele", 1.0, 1.2), ("ja", 1.2, 1.3), ("faz", 1.3, 1.6),
             ("a", 1.6, 1.7), ("pesquisa.", 1.7, 2.2),
             ("Ele", 2.5, 2.7), ("ja", 2.7, 2.8), ("faz", 2.8, 3.1),
             ("a", 3.1, 3.2), ("edicao.", 3.2, 3.7),
             ("Ele", 4.0, 4.2), ("ja", 4.2, 4.3), ("faz", 4.3, 4.6),
             ("o", 4.6, 4.7), ("corte.", 4.7, 5.2)]
        self.assertEqual(self._so_texto(p), [])

    def test_enfase_colada_nao_conta(self):
        p = [("muito", 1.0, 1.3), ("muito", 1.31, 1.6), ("bom", 1.6, 1.9),
             ("muito", 2.5, 2.8), ("muito", 2.81, 3.1), ("bom", 3.1, 3.4)]
        # sem pausa entre as duas primeiras: enfase, nao retomada
        for a in self._so_texto(p):
            self.assertNotEqual(a["deMs"], 1000)


class TestMarkdown(unittest.TestCase):
    def test_sem_achado_diz_que_nao_ouviu_nada(self):
        self.assertIn("Nenhuma falsa partida", escutar.em_markdown([]))

    def test_com_achado_mostra_tempo_e_motivo(self):
        md = escutar.em_markdown([{"tipo": "falsa-partida", "deMs": 36080, "ateMs": 37740,
                                   "porque": "porque sim", "retomada": None}])
        self.assertIn("0:36.08", md)
        self.assertIn("1660 ms", md)
        self.assertIn("porque sim", md)


if __name__ == "__main__":
    unittest.main()
