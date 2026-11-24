import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'plugin'
CLI = ROOT / 'motion/bin/motion.mjs'
CHROME = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')

@unittest.skipUnless(shutil.which('node') and shutil.which('ffmpeg') and CHROME.exists() and (ROOT / 'motion/node_modules/playwright-core').exists(), 'Node, FFmpeg, Chrome e playwright-core necessários')
class MotionTest(unittest.TestCase):
    def test_preview_review_render_and_changed_project(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp); project = temp / 'project'; review = temp / 'review.json'; output = temp / 'animation.mp4'
            def run(*args, ok=True):
                result = subprocess.run(['node', str(CLI), *map(str, args)], capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode == 0, ok, result.stderr)
                return result
            run('init', '--projeto', project)
            (project / 'motion.json').write_text(json.dumps({'width': 160, 'height': 120, 'fps': 5, 'duration': 0.6}))
            run('approve', '--projeto', project, '--registro', review)
            run('render', '--projeto', project, '--registro', review, '--saida', output)
            probe = subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','default=nw=1:nk=1', str(output)], capture_output=True,text=True,check=True)
            self.assertEqual(probe.stdout.strip(), '3')
            original = output.read_bytes()
            run('render', '--projeto', project, '--registro', review, '--saida', output, ok=False)
            self.assertEqual(output.read_bytes(), original)
            (project / 'animation.js').write_text('window.drawMotion = () => {};')
            run('render', '--projeto', project, '--registro', review, '--saida', temp/'new.mp4', ok=False)
            self.assertFalse((temp/'new.mp4').exists())
