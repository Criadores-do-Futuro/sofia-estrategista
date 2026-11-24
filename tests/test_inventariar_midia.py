import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'plugin'
spec = importlib.util.spec_from_file_location('inventariar', ROOT / 'scripts/inventariar_midia.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg ausente')
class InventarioTest(unittest.TestCase):
    def test_identidade_e_preservacao(self):
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder) / 'entrada.mp4'
            out = Path(folder) / 'inventario.json'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=size=32x32:rate=5:duration=1','-c:v','mpeg4',str(video)],check=True)
            cmd = ['python3',str(ROOT/'scripts/inventariar_midia.py'),str(video),'--saida',str(out),'--origem','fonte informada']
            self.assertEqual(subprocess.run(cmd).returncode, 0)
            record = json.loads(out.read_text())
            self.assertEqual(record['origem_informada'], 'fonte informada')
            self.assertEqual(record['bytes'], video.stat().st_size)
            self.assertEqual(len(record['sha256']), 64)
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertTrue(video.exists())
