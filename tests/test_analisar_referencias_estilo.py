import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'plugin'
SCRIPT = ROOT / 'scripts/analisar_referencias_estilo.py'

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg ausente')
class AnaliseReferenciasTest(unittest.TestCase):
    def test_duas_referencias_com_audio_e_sem_audio_nao_sobrescreve(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); v1 = base/'com-audio.mp4'; v2 = base/'sem-audio.mp4'; out = base/'analise'
            subprocess.run(['ffmpeg', '-v','error','-f','lavfi','-i','color=c=red:s=64x64:r=10:d=1',
                            '-f','lavfi','-i','sine=frequency=440:duration=1','-c:v','mpeg4','-c:a','aac','-shortest',str(v1)], check=True)
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=64x64:r=10:d=1',
                            '-c:v','mpeg4',str(v2)],check=True)
            cmd = ['python3',str(SCRIPT),str(v1),str(v2),'--nome','Teste','--saida',str(out)]
            first = subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            self.assertEqual(first.returncode,0,first.stderr)
            registro=json.loads((out/'analise.json').read_text())
            manual=json.loads((out/'manual.json').read_text())
            self.assertEqual(len(registro['referencias']),2)
            self.assertEqual(len(manual['referencias']),2)
            self.assertEqual(len(registro['referencias'][0]['sha256']),64)
            self.assertTrue((out/'capa.jpg').stat().st_size > 0)
            self.assertTrue(any(o['id']=='audio-ref-2-ausente' for o in manual['observacoes']))
            before=(out/'manual.json').read_bytes()
            again=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            self.assertNotEqual(again.returncode,0)
            self.assertEqual((out/'manual.json').read_bytes(),before)
            self.assertTrue(v1.exists())
            self.assertTrue(v2.exists())

if __name__ == '__main__': unittest.main()
