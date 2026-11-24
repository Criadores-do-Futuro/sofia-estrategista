import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'plugin'

class RegrasDistribuicaoTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('git'), 'git ausente')
    def test_git_ignora_dados_em_qualquer_subdiretorio(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            subprocess.run(['git','init','-q',str(base)],check=True)
            shutil.copyfile(ROOT/'.gitignore',base/'.gitignore')
            ignorados=['.env','a/.env.local','a/credentials.json','x/service-account-prod.json',
                       'x/chave.pem','x/video.mp4','x/audio.wav','media/qualquer.json',
                       'a/.npmrc','x/token.json','node_modules/lib.js','x/capa.png','x/quadros.jsonl',
                       'x/manual.json','x/analise.json','x/ref-1-transcricao.json','x/ref-1-trilhas-audio.json']
            for nome in ignorados:
                result=subprocess.run(['git','check-ignore','-q','--no-index',nome],cwd=base)
                self.assertEqual(result.returncode,0,nome)
            for nome in ['scripts/app.py','tests/test_app.py','motion/template/animation.js']:
                result=subprocess.run(['git','check-ignore','-q','--no-index',nome],cwd=base)
                self.assertEqual(result.returncode,1,nome)

    @unittest.skipUnless(shutil.which('npm'), 'npm ausente')
    def test_pacote_motion_so_inclui_arquivos_previstos(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'motion'
            shutil.copytree(ROOT/'motion',base,ignore=shutil.ignore_patterns('node_modules'))
            for nome in ['template/segredo.env','template/credenciais.json','template/video.mp4',
                         'template/token.json','template/chave.pem']:
                (base/nome).write_text('EXEMPLO')
            env=os.environ.copy(); env['npm_config_cache']=str(Path(d)/'cache')
            proc=subprocess.run(['npm','pack','--dry-run','--json','--ignore-scripts','--offline'],
                                cwd=base,env=env,text=True,capture_output=True,check=True)
            paths={item['path'] for item in json.loads(proc.stdout)[0]['files']}
            self.assertEqual(paths,{'package.json','README.md','bin/motion.mjs',
                                    'template/index.html','template/animation.js','template/motion.json'})

if __name__=='__main__': unittest.main()
