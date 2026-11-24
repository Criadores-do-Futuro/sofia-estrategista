import subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import medir


def video(dir_, preto):
    v = dir_ / ("preto.mp4" if preto else "ok.mp4")
    if preto:
        fontes = ["-f", "lavfi", "-i", "color=c=gray:s=320x568:r=30:d=2",
                  "-f", "lavfi", "-i", "color=c=black:s=320x568:r=30:d=2",
                  "-f", "lavfi", "-i", "color=c=gray:s=320x568:r=30:d=2"]
        fc = ["-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]", "-map", "[v]"]
        audio_idx = "3"
    else:
        fontes = ["-f", "lavfi", "-i", "color=c=gray:s=320x568:r=30:d=6"]
        fc = ["-map", "0:v"]
        audio_idx = "1"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *fontes,
                    "-f", "lavfi", "-i", "sine=frequency=220:sample_rate=48000:duration=6",
                    *fc, "-map", f"{audio_idx}:a", "-shortest",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", str(v)], check=True)
    return v


PLANO = {"duracaoMs": 6000, "planos": [
    {"id": "P00", "tipo": "fala", "t0": 0, "t1": 3000, "duracaoMs": 3000},
    {"id": "P01", "tipo": "tela", "t0": 3000, "t1": 6000, "duracaoMs": 3000}]}


class TestMedir(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.ok, cls.preto = video(d, False), video(d, True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_sem_preto_passa_no_quadro(self):
        erros = [e for e in medir.avaliar(self.ok, PLANO) if "preto" in e]
        self.assertEqual(erros, [])

    def test_com_preto_falha_e_aponta_plano(self):
        erros = medir.avaliar(self.preto, PLANO)
        self.assertTrue(any("preto" in e and ("P00" in e or "P01" in e) for e in erros), erros)

    def test_cobertura(self):
        p = {"duracaoMs": 6000, "planos": [dict(PLANO["planos"][0])]}
        self.assertTrue(any("cobertura" in e for e in medir.avaliar(self.ok, p)))


if __name__ == "__main__":
    unittest.main()
