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
from analisar_audio import _estado_arquivo
spec=importlib.util.spec_from_file_location('transcript_manual',ROOT/'scripts/adicionar_transcricao_ao_manual.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class AcrescentarTranscricaoTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.source=self.base/'ref.mp4';self.source.write_bytes(b'video')
        self.manual={'versao':1,'nome':'Estilo','referencias':[{'id':'r1','fonte':str(self.source),'duracao_segundos':3}],
                     'observacoes':[{'id':'o','aspecto':'corte','estado':'indisponivel','descricao':'Não avaliado','evidencias':[]}]}
        self.trans={'versao':1,'fonte':str(self.source),'estado_fonte':_estado_arquivo(self.source),'indice_trilha':1,
                    'referencial_tempos':'container','deslocamento_segundos':0.25,
                    'segmentos':[{'texto':' fala pessoal','inicio_segundos':.5,'fim_segundos':1.5,
                                  'palavras':[{'texto':' fala','inicio_segundos':.5,'fim_segundos':.8,'probabilidade':.9}]}]}

    def test_preserva_origem_nao_inclui_conteudo_privado_por_padrao(self):
        antes=copy.deepcopy(self.manual); result=mod.incorporar(self.manual,self.trans,'r1')
        self.assertEqual(self.manual,antes)
        self.assertEqual(result['observacoes'][0],antes['observacoes'][0])
        obs=result['observacoes'][1]
        self.assertEqual(obs['estado'],'inferido')
        self.assertEqual(obs['evidencias'][0]['inicio_segundos'],.5)
        self.assertNotIn('pessoal',json.dumps(result))
        incluido=mod.incorporar(self.manual,self.trans,'r1',incluir_texto=True)
        self.assertIn('pessoal',incluido['observacoes'][1]['valor']['texto'])
        self.assertEqual(incluido['observacoes'][1]['valor']['palavras'][0]['probabilidade'],.9)

    def test_recusa_tempo_nao_confiavel_fonte_diferente_ou_alterada_e_duplicatas(self):
        for caso in ('tempo','referencial','fonte','index','palavra','duplicata'):
            t=copy.deepcopy(self.trans);m=copy.deepcopy(self.manual)
            if caso=='tempo':t['segmentos'][0]['fim_segundos']=4
            if caso=='referencial':t['referencial_tempos']='inicio_da_trilha'
            if caso=='fonte':t['fonte']=str(self.base/'outro.mp4')
            if caso=='index':t['indice_trilha']=True
            if caso=='palavra':t['segmentos'][0]['palavras'][0]['fim_segundos']=8
            if caso=='duplicata':m=mod.incorporar(m,t,'r1')
            with self.subTest(caso=caso), self.assertRaises(ValueError):mod.incorporar(m,t,'r1')
        self.source.write_bytes(b'dados alterados')
        with self.assertRaisesRegex(ValueError,'mudou'):mod.incorporar(self.manual,self.trans,'r1')

    def test_vazio_nao_afirma_ausencia_de_fala_e_cli_sem_sobrescrever(self):
        trans=copy.deepcopy(self.trans);trans['segmentos']=[]
        result=mod.incorporar(self.manual,trans,'r1')
        self.assertEqual(result['observacoes'][-1]['estado'],'indisponivel')
        self.assertIn('não prova ausência',result['observacoes'][-1]['descricao'])
        m=self.base/'m.json';t=self.base/'t.json';o=self.base/'saida.json'
        m.write_text(json.dumps(self.manual));t.write_text(json.dumps(self.trans))
        cmd=[sys.executable,str(ROOT/'scripts/adicionar_transcricao_ao_manual.py'),str(m),str(t),'--referencia','r1','--saida',str(o)]
        self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
        dados=o.read_bytes()
        self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
        self.assertEqual(o.read_bytes(),dados)

if __name__=='__main__': unittest.main()
