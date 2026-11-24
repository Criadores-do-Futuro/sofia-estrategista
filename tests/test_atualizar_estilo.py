import copy
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
spec=importlib.util.spec_from_file_location('biblioteca_test',ROOT/'scripts/biblioteca_estilos.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def manual(desc='Original'):
    return {'versao':1,'nome':'Estilo','referencias':[{'id':'r1','fonte':'video.mp4','duracao_segundos':10}],
            'observacoes':[{'id':'o1','aspecto':'zoom','estado':'indisponivel','descricao':desc,'evidencias':[]}]}

class AtualizarEstiloTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name); self.raiz=self.base/'biblioteca'; self.manual=self.base/'manual.json'
        self.manual.write_text(json.dumps(manual())); self.capa=self.base/'capa.png'; self.capa.write_bytes(b'capa')
        self.meta=mod.cadastrar_estilo(self.raiz,id_estilo='estilo',nome='Estilo',manual=str(self.manual),capa=str(self.capa))
        self.hash=self.meta['manual']['estado']['sha256']
        self.novo=self.base/'manual-novo.json';self.novo.write_text(json.dumps(manual('Alterado')))

    def test_historico_capa_e_versao_atual(self):
        atualizado=mod.atualizar_manual(self.raiz,'estilo',str(self.novo),self.hash)
        pasta=self.raiz/'estilo'
        self.assertEqual((pasta/'manual.json').read_bytes(),self.manual.read_bytes())
        self.assertEqual((pasta/'capa.png').read_bytes(),b'capa')
        self.assertEqual(atualizado['historico_manuais'][0]['sha256'],self.hash)
        loaded=mod.ler_estilo(self.raiz,'estilo',com_manual=True)
        self.assertEqual(loaded['manual_conteudo']['observacoes'][0]['descricao'],'Alterado')
        self.assertEqual(loaded['integridade'],{'manual':'integro','capa':'integro'})
        with self.assertRaisesRegex(mod.ErroBiblioteca,'conflito'):
            mod.atualizar_manual(self.raiz,'estilo',str(self.novo),self.hash)

    def test_nao_apaga_versao_atual_em_falha_atomica(self):
        with patch.object(mod.os,'replace',side_effect=OSError('falha simulada')):
            with self.assertRaises(OSError): mod.atualizar_manual(self.raiz,'estilo',str(self.novo),self.hash)
        loaded=mod.ler_estilo(self.raiz,'estilo',com_manual=True)
        self.assertEqual(loaded['manual_conteudo'],manual())
        self.assertEqual(loaded['integridade']['capa'],'integro')
        self.assertFalse((self.raiz/'estilo/.atualizacao.lock').exists())
        recuperado=mod.atualizar_manual(self.raiz,'estilo',str(self.novo),self.hash)
        self.assertEqual(recuperado['historico_manuais'][0]['sha256'],self.hash)

    def test_intervencao_externa_em_metadados_recusada(self):
        ler_original=mod.ler_estilo
        caminho=self.raiz/'estilo/estilo.json'
        def ler_e_modificar(*args, **kwargs):
            valor=ler_original(*args, **kwargs)
            alterado=json.loads(caminho.read_text()); alterado['descricao']='edição externa'
            caminho.write_text(json.dumps(alterado))
            return valor
        with patch.object(mod,'ler_estilo',side_effect=ler_e_modificar):
            with self.assertRaisesRegex(mod.ErroBiblioteca,'conflito'):
                mod.atualizar_manual(self.raiz,'estilo',str(self.novo),self.hash)
        self.assertEqual(json.loads(caminho.read_text())['descricao'],'edição externa')
        self.assertEqual((self.raiz/'estilo/manual.json').read_bytes(),self.manual.read_bytes())

    def test_recusa_invalido_lock_e_manual_adulterado(self):
        self.novo.write_text('{}')
        with self.assertRaisesRegex(mod.ErroBiblioteca,'inválido'): mod.atualizar_manual(self.raiz,'estilo',str(self.novo),self.hash)
        self.novo.write_text(json.dumps(manual('Alterado')))
        lock=self.raiz/'estilo/.atualizacao.lock';lock.touch()
        with self.assertRaisesRegex(mod.ErroBiblioteca,'lock'): mod.atualizar_manual(self.raiz,'estilo',str(self.novo),self.hash)
        lock.unlink()
        (self.raiz/'estilo/manual.json').write_text('{}')
        with self.assertRaises(mod.ErroBiblioteca): mod.atualizar_manual(self.raiz,'estilo',str(self.novo),self.hash)
        self.assertEqual((self.raiz/'estilo/manual.json').read_text(),'{}')

    def test_cli_atualiza_uma_vez_com_hash_esperado(self):
        cli=ROOT/'scripts/biblioteca_estilos.py'
        cmd=[sys.executable,str(cli),'--raiz',str(self.raiz),'atualizar','estilo','--manual',str(self.novo),'--hash-esperado',self.hash]
        first=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(first.returncode,0,first.stderr)
        self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
        self.assertEqual(json.loads((self.raiz/'estilo/estilo.json').read_text())['historico_manuais'][0]['sha256'],self.hash)

    def test_duas_atualizacoes_concorrentes_nao_substituem_uma_a_outra(self):
        outro=self.base/'terceiro.json'; outro.write_text(json.dumps(manual('Terceiro')))
        cli=ROOT/'scripts/biblioteca_estilos.py'
        base=[sys.executable,str(cli),'--raiz',str(self.raiz),'atualizar','estilo']
        primeiro=subprocess.Popen(base+['--manual',str(self.novo),'--hash-esperado',self.hash],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        segundo=subprocess.Popen(base+['--manual',str(outro),'--hash-esperado',self.hash],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        primeiro.communicate(timeout=10); segundo.communicate(timeout=10)
        self.assertEqual(sorted([primeiro.returncode,segundo.returncode]),[0,1])
        atual=mod.ler_estilo(self.raiz,'estilo',com_manual=True)
        self.assertIn(atual['manual_conteudo']['observacoes'][0]['descricao'],['Alterado','Terceiro'])
        self.assertEqual((self.raiz/'estilo/manual.json').read_bytes(),self.manual.read_bytes())

if __name__=='__main__': unittest.main()
