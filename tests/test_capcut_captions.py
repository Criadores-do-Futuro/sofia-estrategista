import copy
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugin'))  # o pacote beditor mora em plugin/
from beditor.capcut_captions import apply_recognized, UnsupportedCaptions

root = Path.home()/'.codex/plugins/cache/CapCut/CapCut'
choices = sorted(root.glob('*/skills/capcut-stdraft-builder/scripts'))
skill = Path(os.environ['BEDITOR_CAPCUT_BUILDER']) if os.environ.get('BEDITOR_CAPCUT_BUILDER') else (choices[-1] if choices else None)
try:
    if skill is None:
        raise ImportError('builder não instalado')
    sys.path.insert(0,str(skill))
    from apply_materials import apply_video
    from apply_captions import apply_captions
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


def root_draft():
    return {'version':'0.1.0','segments':[{'id':'draft','type':'DRAFT','attributes':{'width':720,'height':1280,'ratio_type':'custom'}}]}


def query():
    return {'next_action':'none','resources':[{'vid':'v1','status':0,'utterances':[{'text':'Olá', 'start_time':1000,'end_time':1500}]}]}

@unittest.skipUnless(AVAILABLE,'builder oficial indisponível')
class CaptionsTests(unittest.TestCase):
    def setUp(self):
        added=apply_video(root_draft(),source='vid://v1',start_ms=100,source_start_ms=500,duration_ms=2000,layer=0)
        self.draft=added['draft']; self.sid=added['added_segment_ids'][0]
        self.bindings=[{'resource':{'vid':'v1'},'segment_ids':[self.sid]}]
    def apply(self,draft=None,q=None,bindings=None,complete=True,proofs=None):
        return apply_recognized(self.draft if draft is None else draft,'p1',query() if q is None else q,
                                self.bindings if bindings is None else bindings,apply_captions=apply_captions,
                                complete_query_result=complete,source_proofs=proofs)
    def test_aplica_tempos_da_fonte_e_preserva_snapshot(self):
        original=copy.deepcopy(self.draft); out=self.apply()
        self.assertEqual(self.draft,original)
        self.assertEqual(out['base_package_id'],'p1')
        self.assertEqual(len(out['added_segment_ids']),1)
        caption=next(s for s in out['draft']['segments'] if s['id']==out['added_segment_ids'][0])
        self.assertEqual(caption['timeline']['start.ms'],600)
        self.assertEqual(caption['timeline']['duration.ms'],500)
        self.assertEqual(caption['attributes']['content'],'Olá')
        with self.assertRaises(UnsupportedCaptions): self.apply(draft=out['draft'])
    def test_exige_lote_completo_e_identidade(self):
        for q,complete in (({'next_action':'poll_caption','resources':[]},True),(query(),False),
                           ({'next_action':'none','resources':[{'vid':'v1','status':2}]},True)):
            with self.subTest(q=q,complete=complete), self.assertRaises(UnsupportedCaptions): self.apply(q=q,complete=complete)
        with self.assertRaises(UnsupportedCaptions):
            self.apply(bindings=[{'resource':{'vid':'v1'},'segment_ids':['inexistente']}])
        changed=copy.deepcopy(self.draft)
        next(s for s in changed['segments'] if s['id']==self.sid)['attributes']['source']='vid://outro'
        with self.assertRaises(UnsupportedCaptions): self.apply(draft=changed)
    def test_asset_exige_vinculo_comprovado_nesta_versao(self):
        changed=copy.deepcopy(self.draft)
        next(s for s in changed['segments'] if s['id']==self.sid)['attributes']['source']='asset://workspace/1'
        with self.assertRaises(UnsupportedCaptions): self.apply(draft=changed)
        proof={self.sid:{'source':'asset://workspace/1','package_id':'p1','resource':{'vid':'v1'},'evidence':'vínculo verificado no upload'}}
        out=self.apply(draft=changed,proofs=proof)
        self.assertEqual(len(out['added_segment_ids']),1)
        proof[self.sid]['package_id']='p-antigo'
        with self.assertRaises(UnsupportedCaptions): self.apply(draft=changed,proofs=proof)
    def test_workspace_ids_iguais_em_workspaces_distintos(self):
        second=apply_video(self.draft,source='asset://w2/1',start_ms=2200,duration_ms=1000,layer=0)
        changed=second['draft']; sid2=second['added_segment_ids'][0]
        next(s for s in changed['segments'] if s['id']==self.sid)['attributes']['source']='asset://w1/1'
        bindings=[{'resource':{'workspace_id':'w1','resource_id':'same'},'segment_ids':[self.sid]},
                  {'resource':{'workspace_id':'w2','resource_id':'same'},'segment_ids':[sid2]}]
        proof={self.sid:{'source':'asset://w1/1','package_id':'p1','resource':bindings[0]['resource'],'evidence':'mapeamento'},
               sid2:{'source':'asset://w2/1','package_id':'p1','resource':bindings[1]['resource'],'evidence':'mapeamento'}}
        q={'next_action':'none','resources':[{'workspace_id':'w1','resource_id':'same','status':0,'utterances':[{'text':'Um','start_time':600,'end_time':900}]},
                                             {'workspace_id':'w2','resource_id':'same','status':0,'utterances':[{'text':'Dois','start_time':100,'end_time':400}]}]}
        out=self.apply(draft=changed,q=q,bindings=bindings,proofs=proof)
        self.assertEqual(len(out['added_segment_ids']),2)
