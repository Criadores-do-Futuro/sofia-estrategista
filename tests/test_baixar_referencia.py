import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'plugin'
spec = importlib.util.spec_from_file_location('baixar_ref', ROOT / 'scripts/baixar_referencia.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class BaixarReferenciaTest(unittest.TestCase):
    def test_video_unico_sem_url_armazenada(self):
        url='https://example.com/video?secret=SEGREDO-TESTE'
        calls=[]
        def executar(args, timeout):
            calls.append(args)
            if args[0]=='ffprobe': return '{"streams":[{"codec_type":"video"}]}'
            self.assertIn('--no-playlist',args)
            self.assertIn('--no-cookies',args)
            if '--dump-single-json' in args:
                return json.dumps({'id':'video'})
            template=Path(args[args.index('-o')+1]); video=Path(str(template).replace('%(ext)s','mp4'))
            video.write_bytes(b'video de teste')
            return str(video)+'\n'
        with tempfile.TemporaryDirectory() as tmp, patch.object(mod, 'executar', side_effect=executar):
            target=Path(tmp)/'referencia'
            resultado=mod.baixar(url,target)
            self.assertEqual(Path(resultado['arquivo']).read_bytes(),b'video de teste')
            self.assertNotIn('SEGREDO-TESTE',json.dumps(resultado))
            self.assertEqual([p.name for p in target.iterdir()],['referencia.mp4'])
            self.assertEqual(len(calls),3)
            with self.assertRaises(ValueError): mod.baixar(url,target)

    def test_playlist_e_enderecos_nao_publicos(self):
        for url in ('file:///etc/passwd', 'https://u:pass@example.com/x', 'http://127.0.0.1/a', 'http://localhost/a'):
            with self.subTest(url=url), self.assertRaises(ValueError): mod.validar_url(url)
        with tempfile.TemporaryDirectory() as tmp, patch.object(mod, 'executar',return_value='{"_type":"playlist","entries":[]}') as called:
            with self.assertRaisesRegex(ValueError,'playlists'):
                mod.baixar('https://example.com/list',Path(tmp)/'output')
            self.assertEqual(called.call_count,1)
            self.assertFalse((Path(tmp)/'output').exists())

    def test_erro_da_ferramenta_nao_vaza_url(self):
        import subprocess
        with patch.object(mod.subprocess,'run',side_effect=subprocess.CalledProcessError(1,['yt-dlp','secret'])):
            with self.assertRaises(ValueError) as e:
                mod.executar(['yt-dlp','secret'],1)
            self.assertNotIn('secret',str(e.exception))

if __name__ == '__main__': unittest.main()
