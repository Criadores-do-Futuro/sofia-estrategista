import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugin'))  # o pacote beditor mora em plugin/
from beditor.davinci_preflight import prepare, ResolvePreflightError


def plan():
    return {'version':'1.0','project':{'title':'Teste','editor':'davinci','creative_format':'dinamismo'},
            'assets':[{'id':'v','kind':'video','duration_ms':2000}], 'protected_speech':[],
            'clips':[{'id':'c','asset_id':'v','kind':'video','track':'v1',
                      'source':{'start_ms':0,'end_ms':1000},'timeline':{'start_ms':0,'end_ms':1000}}]}

class PreflightTest(unittest.TestCase):
    def setUp(self):
        self.snapshot={'complete':True,'timeline_id':'tl','version_token':'snapshot-1','items':[]}
        self.media={'v':{'clip_id':'pool','source_fps':'25'}}
    def call(self,s):
        return prepare(plan(),self.media,{'v1':1},'25',s)
    def test_nenhuma_escrita_e_fontes_preservadas(self):
        snapshot=copy.deepcopy(self.snapshot); self.assertEqual(self.call(snapshot)['prepared']['params']['clip_infos'][0]['end_frame'],25)
        self.assertEqual(snapshot,self.snapshot)
    def test_colisao_mesma_pista_bloqueia_mas_audio_ou_pista_diferente_nao(self):
        for kind, track, fails in [('video',1,True),('audio',1,False),('video',2,False)]:
            s=copy.deepcopy(self.snapshot); s['items']=[{'kind':kind,'track_index':track,'start_frame':10,'end_frame':30}]
            if fails:
                with self.assertRaises(ResolvePreflightError): self.call(s)
            else: self.assertTrue(self.call(s))
    def test_sem_retrato_completo_ou_intervalo_invalido_bloqueia(self):
        s=copy.deepcopy(self.snapshot); s['complete']=False
        with self.assertRaises(ResolvePreflightError): self.call(s)
        s=copy.deepcopy(self.snapshot); s['items']=[{'kind':'video','track_index':1,'start_frame':0,'end_frame':0}]
        with self.assertRaises(ResolvePreflightError): self.call(s)
