import shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sdr


def clipe(caminho, hlg):
    # HLG de verdade é HEVC 10 bits, como o iPhone grava: um H.264 de 8 bits só
    # marcado como HLG o avconvert deixa passar com a marca. A marcação vai pelo
    # parâmetro do codificador — a opção genérica não chega ao stream do .mov
    video = ["-c:v", "libx265", "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1", "-x265-params",
             "colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:log-level=error"] \
        if hlg else ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                     "-x264-params", "transfer=bt709:colorprim=bt709:colormatrix=bt709"]
    subprocess.run(["ffmpeg", "-y", "-v", "error",
                    "-f", "lavfi", "-i", "testsrc=s=320x568:r=30:d=2",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
                    *video, "-c:a", "pcm_s16le", "-shortest", str(caminho)], check=True)
    return caminho


class TestSdr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.hlg = clipe(d / "take.mov", hlg=True)
        cls.sdr_ = clipe(d / "outro.mov", hlg=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_reconhece_hlg_e_sdr(self):
        self.assertEqual(sdr.hdr(self.hlg), "HLG")
        self.assertIsNone(sdr.hdr(self.sdr_))

    def test_trava_recusa_hdr_e_deixa_passar_sdr(self):
        with self.assertRaises(SystemExit) as c:
            sdr.exigir_sdr(self.hlg)
        self.assertIn(".sdr.mov", str(c.exception.code))
        self.assertEqual(sdr.exigir_sdr(self.hlg, aceitar=True), "HLG")
        self.assertIsNone(sdr.exigir_sdr(self.sdr_))

    def test_saida_padrao_mora_ao_lado_do_take(self):
        self.assertEqual(sdr.saida_padrao(Path("brutos/take001.mov")),
                         Path("brutos/take001.sdr.mov"))

    def test_transcricao_do_bruto_serve_ao_sdr(self):
        d = Path(self.tmp.name)
        (d / "take.whisper.json").write_text("{}", encoding="utf-8")
        novo = sdr.ligar_transcricao(d / "take.mov", d / "take.sdr.mov")
        self.assertEqual(novo.name, "take.sdr.whisper.json")
        self.assertTrue(novo.is_symlink())
        self.assertEqual(novo.read_text(encoding="utf-8"), "{}")

    @unittest.skipUnless(shutil.which("xcrun") and sys.platform == "darwin", "avconvert é do macOS")
    def test_converte_mantendo_relogio_e_audio_original(self):
        saida = sdr.converter(self.hlg)
        self.assertIsNone(sdr.hdr(saida))
        self.assertAlmostEqual(sdr.duracao(saida), sdr.duracao(self.hlg), delta=0.05)
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                            "-show_entries", "stream=codec_name", "-of", "csv=p=0",
                            str(saida)], capture_output=True, text=True, check=True)
        self.assertEqual(r.stdout.strip(), "pcm_s16le")


if __name__ == "__main__":
    unittest.main()
