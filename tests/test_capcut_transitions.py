import copy
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugin'))  # o pacote beditor mora em plugin/
from beditor.capcut_transitions import prepare_transitions, UnsupportedTransition

root=Path.home()/'.codex/plugins/cache/CapCut/CapCut'
choices=sorted(root.glob('*/skills/capcut-stdraft-builder/scripts'))
skill=Path(os.environ['BEDITOR_CAPCUT_BUILDER']) if os.environ.get('BEDITOR_CAPCUT_BUILDER') else (choices[-1] if choices else None)
try:
    if skill is None: raise ImportError('builder ausente')
    sys.path.insert(0,str(skill))
    from apply_materials import apply_video, apply_transition
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


def build():
    draft={'version':'0.1.0','segments':[{'id':'draft','type':'DRAFT','attributes':{'width':720,'height':1280,'ratio_type':'custom'}}]}
    ids=[]
    for n in range(3):
        result=apply_video(draft,source='vid://source',start_ms=1000*n,duration_ms=1000,source_start_ms=1000*n,layer=0)
        draft=result['draft'];ids.extend(result['added_segment_ids'])
    return draft,ids

@unittest.skipUnless(AVAILABLE,'builder oficial ausente')
class TransitionTests(unittest.TestCase):
    def apply(self,draft,ops,version='p1'):
        return prepare_transitions(draft,version,ops,apply_transition=apply_transition)
    def op(self,ids,a=0,b=1,duration=400):
        return {'from_segment_id':ids[a],'to_segment_id':ids[b],'source':'vimo://transition-example','duration_ms':duration}
    def test_builder_real_preserva_snapshot_e_intervalos(self):
        draft,ids=build(); before=copy.deepcopy(draft)
        out=self.apply(draft,[self.op(ids)])
        self.assertEqual(draft,before)
        index={s['id']:s for s in out['draft']['segments']}
        self.assertEqual(index[ids[0]]['attributes']['transition'],'vimo://transition-example')
        self.assertEqual(index[ids[0]]['attributes']['transition.duration.ms'],400)
        self.assertEqual(index[ids[1]]['timeline']['start.ms'],1000)
        self.assertEqual(out['base_package_id'],'p1')
        with self.assertRaises(UnsupportedTransition): self.apply(out['draft'],[self.op(ids)])
    def test_recusa_invalidos_sem_alterar_snapshot(self):
        draft,ids=build(); before=copy.deepcopy(draft)
        for ops in ([self.op(ids,0,2)], [self.op(ids,duration=1001)],
                    [self.op(ids),self.op(ids)], [self.op(ids,0,1,600),self.op(ids,1,2,600)],
                    [{**self.op(ids),'source':'https://invalid'}]):
            with self.subTest(ops=ops), self.assertRaises(UnsupportedTransition): self.apply(draft,ops)
        with self.assertRaises(UnsupportedTransition): self.apply(draft,[self.op(ids)],version='')
        self.assertEqual(draft,before)
    def test_duas_transicoes_em_intervalos_validos(self):
        draft,ids=build()
        out=self.apply(draft,[self.op(ids,0,1,400),self.op(ids,1,2,500)])
        self.assertEqual(len(out['changes']),2)
        index={s['id']:s for s in out['draft']['segments']}
        self.assertEqual(index[ids[1]]['attributes']['transition.duration.ms'],500)
