import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'plugin'
SCRIPT=ROOT/'scripts/analisar_trilhas_audio.py'

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg ausente')
class TrilhasAudioTest(unittest.TestCase):
    def test_duas_trilhas_tem_medidas_independentes(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp); source=p/'entrada.mkv'; output=p/'audios.json'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=s=48x48:r=5:d=1',
                '-f','lavfi','-i','sine=frequency=440:duration=1',
                '-itsoffset','0.2','-f','lavfi','-i','anullsrc=channel_layout=mono:sample_rate=44100:d=1',
                '-map','0:v','-map','1:a','-map','2:a','-c:v','mpeg4','-c:a','pcm_s16le',str(source)],check=True)
            cmd=['python3',str(SCRIPT),str(source),'--saida',str(output)]
            run=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            self.assertEqual(run.returncode,0,run.stderr)
            result=json.loads(output.read_text())
            self.assertEqual([t['indice_stream'] for t in result['trilhas']],[1,2])
            self.assertIsNotNone(result['trilhas'][0]['nivel_medio_dbfs'])
            self.assertLess(result['trilhas'][1]['nivel_medio_dbfs'], -80)
            self.assertTrue(result['trilhas'][1]['inicio_verificado'])
            self.assertAlmostEqual(result['trilhas'][1]['inicio_segundos'], .2, places=2)
            self.assertGreaterEqual(result['trilhas'][1]['silencios'][0]['inicio_segundos'], .19)
            self.assertGreater(len(result['trilhas'][1]['silencios']),0)
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            pipeline=ROOT/'scripts/analisar_referencias_estilo.py'
            dest=p/'analise'
            combined=subprocess.run(['python3',str(pipeline),str(source),'--nome','Duas trilhas','--saida',str(dest)],capture_output=True,text=True,timeout=60)
            self.assertEqual(combined.returncode,0,combined.stderr)
            tracks=json.loads((dest/'ref-1-trilhas-audio.json').read_text())['trilhas']
            self.assertEqual([t['indice_stream'] for t in tracks],[1,2])

if __name__=='__main__': unittest.main()
