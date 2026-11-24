import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1] / 'plugin'
SCRIPT = ROOT / "scripts" / "analisar_audio.py"
spec = importlib.util.spec_from_file_location("analisar_audio", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg e ffprobe necessários")
class AnalisarAudioTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.raiz = Path(self.pasta.name)

    def tearDown(self):
        self.pasta.cleanup()

    def gerar(self, nome, *args):
        caminho = self.raiz / nome
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args, str(caminho)],
                       check=True, capture_output=True)
        return caminho

    def test_detecta_silencio_real_sem_chamar_ruido_de_efeito(self):
        arquivo = self.gerar("tom-silencio.wav", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                             "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=1",
                             "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]", "-map", "[out]")
        resultado = mod.analisar(arquivo)
        self.assertTrue(resultado["processamento_sem_erro"])
        self.assertTrue(resultado["possui_audio"])
        self.assertIsNotNone(resultado["nivel_medio_dbfs"])
        self.assertEqual(len(resultado["silencios"]), 1)
        self.assertAlmostEqual(resultado["silencios"][0]["inicio_segundos"], 1, delta=0.03)
        self.assertAlmostEqual(resultado["silencios"][0]["fim_segundos"], 2, delta=0.03)
        self.assertNotIn("efeitos", resultado)

    def test_audio_totalmente_silencioso_registra_limite_da_medicao(self):
        arquivo = self.gerar("silencio.wav", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=1")
        resultado = mod.analisar(arquivo)
        self.assertTrue(resultado["processamento_sem_erro"])
        self.assertTrue(resultado["nivel_medio_dbfs"] is None or resultado["nivel_medio_dbfs"] <= -90)
        self.assertTrue(any("16 bits" in item for item in resultado["limites"]))
        self.assertEqual(len(resultado["silencios"]), 1)

    def test_referencia_sem_audio_e_reportada_sem_fingir_medicao(self):
        arquivo = self.gerar("sem-audio.mkv", "-f", "lavfi", "-i", "color=c=black:s=32x32:r=5:d=1", "-c:v", "ffv1")
        resultado = mod.analisar(arquivo)
        self.assertFalse(resultado["possui_audio"])
        self.assertFalse(resultado["processamento_sem_erro"])
        self.assertEqual(resultado["silencios"], [])

    def test_audio_atrasado_preserva_tempo_no_container(self):
        arquivo = self.gerar("atrasado.mkv", "-f", "lavfi", "-i", "color=c=black:s=32x32:r=10:d=2",
                             "-itsoffset", "0.5", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=1",
                             "-c:v", "ffv1", "-c:a", "pcm_s16le")
        resultado = mod.analisar(arquivo)
        self.assertTrue(resultado["trilha"]["deslocamento_verificado"])
        self.assertAlmostEqual(resultado["silencios"][0]["inicio_segundos"], 0.5, delta=0.03)
        self.assertAlmostEqual(resultado["silencios"][0]["fim_segundos"], 1.5, delta=0.03)

    def test_nao_sobrescreve_saida_nem_aceita_limite_invalido(self):
        arquivo = self.gerar("tom.wav", "-f", "lavfi", "-i", "sine=frequency=440:duration=1")
        saida = self.raiz / "saida.json"
        saida.write_text("original", encoding="utf-8")
        processo = subprocess.run([sys.executable, str(SCRIPT), str(arquivo), "--saida", str(saida)], capture_output=True, text=True)
        self.assertNotEqual(processo.returncode, 0)
        self.assertEqual(saida.read_text(encoding="utf-8"), "original")
        with self.assertRaises(mod.AnaliseErro):
            mod.analisar(arquivo, ruido_db=float("nan"))

    def test_saida_json_cli_e_reproduzivel(self):
        arquivo = self.gerar("tom.wav", "-f", "lavfi", "-i", "sine=frequency=440:duration=1")
        saida = self.raiz / "saida.json"
        processo = subprocess.run([sys.executable, str(SCRIPT), str(arquivo), "--saida", str(saida)], capture_output=True, text=True)
        self.assertEqual(processo.returncode, 0, processo.stderr)
        self.assertTrue(json.loads(saida.read_text(encoding="utf-8"))["processamento_sem_erro"])


if __name__ == "__main__":
    unittest.main()
