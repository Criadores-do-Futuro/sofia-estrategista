import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugin'))  # o pacote beditor mora em plugin/
from beditor.davinci_plan import translate, UnsupportedResolvePlan


def plan():
    return {'version':'1.0', 'project':{'title':'teste','editor':'davinci','creative_format':'dinamismo'},
            'assets':[{'id':'take','kind':'video','duration_ms':3000}], 'protected_speech':[],
            'clips':[{'id':'v','asset_id':'take','track':'v1','kind':'video','source':{'start_ms':1000,'end_ms':2000},'timeline':{'start_ms':0,'end_ms':1000}},
                     {'id':'a','asset_id':'take','track':'a1','kind':'audio','source':{'start_ms':1000,'end_ms':2000},'timeline':{'start_ms':0,'end_ms':1000}}]}

class ResolvePlanTests(unittest.TestCase):
    def setUp(self):
        self.media={'take':{'clip_id':'pool-1','source_fps':'24'}}
        self.tracks={'v1':1,'a1':1}
    def test_positioned_video_audio_are_separate(self):
        result=translate(plan(),self.media,self.tracks,'30')
        v,a=result['params']['clip_infos']
        self.assertEqual((v['start_frame'],v['end_frame'],v['record_frame'],v['media_type']), (24,48,0,1))
        self.assertEqual((a['start_frame'],a['end_frame'],a['track_index'],a['media_type']), (24,48,1,2))
    def test_misalignment_and_missing_pool_ids_fail(self):
        p=plan();p['clips'][0]['source']['start_ms']=1001;p['clips'][0]['timeline']['end_ms']=999
        with self.assertRaises(UnsupportedResolvePlan): translate(p,self.media,self.tracks,'30')
        with self.assertRaises(UnsupportedResolvePlan): translate(plan(),{},self.tracks,'30')
    def test_overlapping_track_and_text_do_not_get_discarded(self):
        p=plan();p['clips'].append(copy.deepcopy(p['clips'][0]));p['clips'][-1]['id']='v2'
        with self.assertRaisesRegex(UnsupportedResolvePlan,'sobreposição'): translate(p,self.media,self.tracks,'30')
        p=plan();p['text_layers']=[{'id':'t','type':'lettering','track':'t1','text':'Oi','timeline':{'start_ms':0,'end_ms':1000}}]
        with self.assertRaisesRegex(UnsupportedResolvePlan,'Legendas'): translate(p,self.media,self.tracks,'30')
    def test_explicit_editor_and_audio_policy(self):
        p=plan();p['project']['editor']='capcut'
        with self.assertRaises(UnsupportedResolvePlan): translate(p,self.media,self.tracks,'30')
        p=plan();p['clips'][0]['carries_source_audio']=True
        with self.assertRaises(UnsupportedResolvePlan): translate(p,self.media,self.tracks,'30')
