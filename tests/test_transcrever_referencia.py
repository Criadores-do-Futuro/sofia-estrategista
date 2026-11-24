import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]/'plugin'
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('transcrever_ref',ROOT/'scripts/transcrever_referencia.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TranscricaoTest(unittest.TestCase):
    def test_tempos_palavra_e_deslocamento_verificado(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); fonte=root/'origem.mp4'; modelo=root/'modelo.pt'
            fonte.write_bytes(b'video');modelo.write_bytes(b'modelo')
            def fake(args, timeout):
                if args[0]=='ffprobe':
                    return json.dumps({'format':{'start_time':'0.0'},'streams':[{'index':2,'codec_type':'audio','start_time':'0.25'}]})
                if args[0]=='ffmpeg':
                    self.assertEqual(args[args.index('-map')+1],'0:2')
                    Path(args[-1]).write_bytes(b'wav')
                    return ''
                self.assertIn(str(modelo.resolve()),args)
                self.assertEqual(args[args.index('--word_timestamps')+1],'True')
                folder=Path(args[args.index('--output_dir')+1])
                (folder/'fonte.json').write_text(json.dumps({'segments':[{'start':.1,'end':1.,'text':' oi','words':[{'word':' oi','start':.1,'end':.4,'probability':.9}]}]}))
                return ''
            with patch.object(mod,'_execute',side_effect=fake): result=mod.transcrever(fonte,modelo,indice=2)
            self.assertEqual(result['referencial_tempos'],'container')
            self.assertEqual(result['segmentos'][0]['palavras'][0]['inicio_segundos'],.35)
            self.assertEqual(result['segmentos'][0]['palavras'][0]['fim_segundos'],.65)
            self.assertNotIn('silencios', result)

    def test_sem_inicio_e_sem_palavras_nao_fabrica_tempos(self):
        raw={'segments':[{'start':0,'end':.5,'text':'olá'}]}
        self.assertEqual(mod.normalizar(raw,0)[0]['palavras'],[])
        with self.assertRaises(ValueError): mod.normalizar({'segments':[{'start':2,'end':1,'text':'x'}]},0)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); fonte=root/'voz.wav'; modelo=root/'modelo.pt'; fonte.touch();modelo.touch()
            with patch.object(mod,'_execute',return_value='{"streams": []}'):
                with self.assertRaisesRegex(ValueError,'não existe'): mod.transcrever(fonte,modelo)

    def test_nao_expoe_saida_sensivel_em_erro(self):
        with patch.object(mod.subprocess,'run',side_effect=subprocess.CalledProcessError(1,['audio privado'])):
            with self.assertRaises(ValueError) as e: mod._execute(['whisper','audio privado'],5)
            self.assertNotIn('audio privado',str(e.exception))

if __name__=='__main__': unittest.main()
