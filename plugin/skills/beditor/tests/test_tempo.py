import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import tempo

WHISPER = {"text": "", "language": "pt", "segments": [
    {"start": 0.5, "end": 2.0, "text": " oi tudo bem.", "words": [
        {"word": " oi", "start": 0.5, "end": 0.8},
        {"word": " tudo", "start": 0.9, "end": 1.3},
        {"word": " bem.", "start": 1.4, "end": 2.0}]},
    {"start": 3.5, "end": 4.2, "text": " entao vamos", "words": [
        {"word": " entao", "start": 3.5, "end": 3.9},
        {"word": " vamos", "start": 3.9, "end": 4.2}]},
]}


class TestTempo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.arq = Path(self.tmp.name) / "w.json"
        self.arq.write_text(json.dumps(WHISPER), encoding="utf-8")

    def test_palavras_em_ms_sem_espacos(self):
        p = tempo.carregar_palavras(self.arq)
        self.assertEqual(p[0], {"palavra": "oi", "deMs": 500, "ateMs": 800})
        self.assertEqual(len(p), 5)

    def test_frases_quebram_em_pausa_e_pontuacao(self):
        f = tempo.frases(tempo.carregar_palavras(self.arq), pausa_ms=900)
        self.assertEqual([x["texto"] for x in f], ["oi tudo bem.", "entao vamos"])
        self.assertEqual(f[0]["pausaDepoisMs"], 1500)
        self.assertEqual(f[1]["pausaAntesMs"], 1500)
        self.assertEqual(f[0]["pausaAntesMs"], 500)

    def test_ts(self):
        self.assertEqual(tempo.ts(83130), "01:23.1")

    def test_recorte(self):
        self.assertEqual(tempo.recorte_9x16(3840, 2160), (1215, 2160, 1312, 0))
        self.assertEqual(tempo.recorte_9x16(1080, 1920), (1080, 1920, 0, 0))


if __name__ == "__main__":
    unittest.main()
