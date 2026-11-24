import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'plugin'
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('enriquecer_manual',ROOT/'scripts/enriquecer_manual_estilo.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def manual():
    return {'versao':1,'nome':'Referência','referencias':[{'id':'r1','fonte':'arquivo.mp4','duracao_segundos':10}],
            'observacoes':[{'id':'inicial','aspecto':'tracking','estado':'indisponivel','descricao':'Ainda não revisado','evidencias':[]}]}


def observacao():
    return {'id':'zoom-1','aspecto':'zoom','estado':'inferido','descricao':'Aproximação parece começar com a fala',
            'confianca':.7,'evidencias':[{'referencia_id':'r1','inicio_segundos':1,'fim_segundos':2,'modalidade':'audiovisual','nota':'Conferir no original'}]}

class EnriquecerTest(unittest.TestCase):
    def test_preserva_anteriores_e_nao_muta_entrada(self):
        origem=manual(); antes=copy.deepcopy(origem); nova=observacao()
        resultado=mod.enriquecer(origem,[nova])
        self.assertEqual(origem,antes)
        self.assertEqual(resultado['observacoes'][0],antes['observacoes'][0])
        self.assertEqual(resultado['observacoes'][1],nova)
        self.assertIsNot(resultado['observacoes'][1],nova)

    def test_rejeita_evidencia_fora_da_fonte_duplicados_e_falta_de_evidencia(self):
        for modo in ('tempo','ref','id','evidencia'):
            nova=observacao()
            if modo=='tempo': nova['evidencias'][0]['fim_segundos']=11
            elif modo=='ref': nova['evidencias'][0]['referencia_id']='outra'
            elif modo=='id': nova['id']='inicial'
            else: nova['evidencias']=[]
            with self.subTest(modo=modo), self.assertRaises(ValueError): mod.enriquecer(manual(),[nova])

    def test_cli_recusa_sobrescrita_e_numero_nao_finito(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); origem=root/'manual.json'; obs=root/'observacoes.json'; saida=root/'novo.json'
            origem.write_text(json.dumps(manual()));obs.write_text(json.dumps([observacao()]))
            cmd=[sys.executable,str(ROOT/'scripts/enriquecer_manual_estilo.py'),str(origem),'--observacoes',str(obs),'--saida',str(saida)]
            primeiro=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(primeiro.returncode,0,primeiro.stderr)
            antes=saida.read_bytes()
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertEqual(saida.read_bytes(),antes)
            obs.write_text('[{"confianca": NaN}]')
            novo=root/'outro.json';cmd[-1]=str(novo)
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertFalse(novo.exists())

if __name__=='__main__': unittest.main()
