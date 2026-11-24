import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'plugin'
SCRIPT = ROOT / 'skills/sofia-editora/scripts/analisar_quadros.py'


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg necessário')
class QuadrosTest(unittest.TestCase):
    def test_registra_mudanca_de_cena_sem_descartar_quadros(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video, output = root / 'corte.mp4', root / 'dados.jsonl'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'color=black:size=160x90:rate=10:duration=1', '-f', 'lavfi', '-i',
                            'color=white:size=160x90:rate=10:duration=1', '-filter_complex',
                            '[0:v][1:v]concat=n=2:v=1:a=0', '-c:v', 'mpeg4', str(video)], check=True)
            result = subprocess.run([sys.executable, str(SCRIPT), str(video), '--saida', str(output)],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual(lines[-1]['quadros_medidos'], 20)
            peak = max(lines[:-1], key=lambda item: item['pontuacao_mudanca'])
            self.assertAlmostEqual(peak['pts_segundos'], 1.0)
            self.assertGreater(peak['pontuacao_mudanca'], 10)

    def test_processa_todos_quadros_e_preserva_saida_existente(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video, output = root / 'video.mp4', root / 'dados.jsonl'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'testsrc2=size=160x90:rate=10:duration=2', '-c:v', 'mpeg4',
                            str(video)], check=True)
            result = subprocess.run([sys.executable, str(SCRIPT), str(video), '--saida', str(output)],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual(len(lines), 21)
            self.assertEqual(lines[-1]['quadros_medidos'], 20)
            self.assertTrue(lines[-1]['contagem_compativel'])
            self.assertEqual(lines[-1]['quadros_sem_pts'], 0)
            self.assertEqual(lines[0]['pts_segundos'], 0.0)
            self.assertEqual(lines[-2]['pts_segundos'], 1.9)
            self.assertTrue(all('luma_media' in item and 'saturacao_media' in item and
                                'pontuacao_mudanca' in item for item in lines[:-1]))
            manual = root / 'manual.json'
            generator = ROOT / 'scripts/gerar_manual_medido.py'
            generated = subprocess.run([sys.executable, str(generator), str(output), '--duracao', '2',
                                        '--nome', 'Teste', '--saida', str(manual)], capture_output=True, text=True)
            self.assertEqual(generated.returncode, 0, generated.stderr)
            observations = json.loads(manual.read_text())['observacoes']
            self.assertEqual(sum(x['estado'] == 'medido' for x in observations), 2)
            self.assertTrue(any(x['aspecto'] == 'som e efeitos sonoros' and x['estado'] == 'indisponivel'
                                for x in observations))
            multi = root / 'manual-multiplo.json'
            result_multi = subprocess.run([sys.executable, str(generator), str(output), str(output),
                                          '--duracao', '2', '--duracao', '2', '--nome', 'Duas referências',
                                          '--saida', str(multi)], capture_output=True, text=True)
            self.assertEqual(result_multi.returncode, 0, result_multi.stderr)
            multi_data = json.loads(multi.read_text())
            self.assertEqual(len(multi_data['referencias']), 2)
            self.assertEqual(sum(x['estado'] == 'medido' for x in multi_data['observacoes']), 4)
            partial = root / 'parcial.jsonl'
            partial.write_text('\n'.join(json.dumps(line) for line in lines[:-2] + [lines[-1]]) + '\n')
            rejected = subprocess.run([sys.executable, str(generator), str(partial), '--duracao', '2',
                                       '--nome', 'Teste', '--saida', str(root / 'incompleto.json')],
                                      capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            original = output.read_bytes()
            again = subprocess.run([sys.executable, str(SCRIPT), str(video), '--saida', str(output)],
                                   text=True, capture_output=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(output.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
