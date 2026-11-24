import json, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import contato, tempo


def fixture_take(dir_):
    take = dir_ / "take.mp4"
    # 10 s: 0-5 s vermelho parado, 5-10 s testsrc (barra que anda: imagem alta);
    # audio: tom nos primeiros 5 s, silencio depois (voz alta -> baixa)
    subprocess.run(["ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", "color=c=red:s=1080x1920:r=30:d=5",
        "-f", "lavfi", "-i", "testsrc=s=1080x1920:r=30:d=5",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=5",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono:d=5",
        "-filter_complex",
        "[0:v][1:v]concat=n=2:v=1:a=0[v];[2:a][3:a]concat=n=2:v=0:a=1[a]",
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(take)], check=True)
    ws = {"text": "", "language": "pt", "segments": [
        {"start": 0.5, "end": 4.0, "text": " primeira frase aqui.", "words": [
            {"word": " primeira", "start": 0.5, "end": 1.5},
            {"word": " frase", "start": 1.6, "end": 2.5},
            {"word": " aqui.", "start": 2.6, "end": 4.0}]},
        {"start": 5.5, "end": 9.5, "text": " segunda frase longa", "words": [
            {"word": " segunda", "start": 5.5, "end": 6.5},
            {"word": " frase", "start": 6.6, "end": 8.0},
            {"word": " longa", "start": 8.1, "end": 9.5}]}]}
    w = dir_ / "take.whisper.json"
    w.write_text(json.dumps(ws), encoding="utf-8")
    return take, w


class TestContato(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.take, cls.whisper = fixture_take(cls.dir)
        cls.frases = tempo.frases(tempo.carregar_palavras(cls.whisper))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_voz_cai_na_segunda_frase(self):
        voz = contato.medir_voz(self.take, self.frases)
        self.assertGreater(voz[0], voz[1])
        self.assertGreater(voz[0], 100)   # % da media do take

    def test_imagem_sobe_na_segunda_frase(self):
        rec = tempo.recorte_9x16(1080, 1920)
        img = contato.medir_imagem(self.take, self.frases, rec)
        self.assertGreater(img[1], img[0])

    def test_quadros_um_por_frase_mais_a_cada_3s(self):
        q = contato.quadros_de(self.frases, passo_ms=3000)
        # frase 1 (3,5 s): 1 quadro; frase 2 (4 s): meio + 1 extra
        self.assertEqual([x["frase"] for x in q], [0, 1, 1])
        self.assertTrue(all(0 <= x["ms"] <= 10000 for x in q))

    def test_alinhar_roteiro(self):
        rot = "Titulo\n\nPrimeira frase aqui.\n\nOutra coisa completamente diferente."
        al = contato.alinhar_roteiro(self.frases, rot)
        self.assertEqual(al[0], "Primeira frase aqui.")
        self.assertIsNone(al[1])

    def test_cli_escreve_tudo(self):
        out = self.dir / "guia"
        subprocess.run([sys.executable, str(Path(contato.__file__)),
            "--take", str(self.take), "--falas", str(self.whisper),
            "--branding", "none", "--out", str(out)], check=True)
        self.assertTrue((out / "fala.md").exists())
        self.assertTrue((out / "contato-01.jpg").exists())
        idx = json.loads((out / "contato.json").read_text(encoding="utf-8"))
        self.assertEqual(idx["takeMs"], 10000)
        self.assertEqual(len(idx["frases"]), 2)
        # No passo padrão (6000) nenhuma das duas frases é longa o bastante para
        # ganhar extra — sobra o quadro do meio de cada uma. O que este teste
        # tranca não é o número, é a garantia: **toda frase aparece**. Frase sem
        # quadro nenhum é frase que o diretor decide às cegas.
        self.assertEqual(sorted(q["frase"] for q in idx["quadros"]), [0, 1])
        fala = (out / "fala.md").read_text(encoding="utf-8")
        self.assertIn("ritmo", fala)
        self.assertIn("— pausa 1,5 s", fala)
        self.assertIn("preset", (out / "branding.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
