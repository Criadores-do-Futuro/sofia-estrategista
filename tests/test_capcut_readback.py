import copy
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugin'))  # o pacote beditor mora em plugin/
from beditor.capcut_web import apply_new_plan
from beditor.capcut_readback import compare, InvalidReadback

root=Path.home()/'.codex/plugins/cache/CapCut/CapCut'
choices=sorted(root.glob('*/skills/capcut-stdraft-builder/scripts'))
skill=Path(os.environ['BEDITOR_CAPCUT_BUILDER']) if os.environ.get('BEDITOR_CAPCUT_BUILDER') else (choices[-1] if choices else None)
try:
    if skill is None: raise ImportError('builder ausente')
    sys.path.insert(0,str(skill))
    from apply_materials import apply_video, apply_audio, apply_text
    AVAILABLE=True
except ImportError:
    AVAILABLE=False


def plan():
    return {'version':'1.0','project':{'title':'Teste','editor':'capcut','creative_format':'dinamismo'},
            'assets':[{'id':'v','kind':'video','duration_ms':5000}], 'protected_speech':[],
            'clips':[{'id':'clip','asset_id':'v','track':'v1','kind':'video','source':{'start_ms':500,'end_ms':1500},
                      'timeline':{'start_ms':200,'end_ms':1200}},
                     {'id':'voz','asset_id':'v','track':'a1','kind':'audio','source':{'start_ms':300,'end_ms':1500},
                      'timeline':{'start_ms':0,'end_ms':1200}}],
            'text_layers':[{'id':'titulo','type':'lettering','track':'t1','text':'Olá',
                            'timeline':{'start_ms':200,'end_ms':1200}}]}

@unittest.skipUnless(AVAILABLE,'builder oficial indisponível')
class ReadbackTests(unittest.TestCase):
    def setUp(self):
        draft={'version':'0.1.0','segments':[{'id':'draft','type':'DRAFT','attributes':{'width':720,'height':1280,'ratio_type':'custom'}}]}
        self.plan=plan();self.sources={'v':'vid://v1'};self.layers={'video':{'v1':0},'audio':{'a1':0},'text':{'t1':1}}
        out=apply_new_plan(draft,self.plan,resources=self.sources,video_layers=self.layers['video'],text_layers=self.layers['text'],
                           audio_layers=self.layers['audio'],audio_roles={'voz':'fala'},apply_video=apply_video,apply_audio=apply_audio,apply_text=apply_text)
        self.snapshot=out['draft'];self.ids=out['segment_ids']
    def run_compare(self,snapshot=None,**kw):
        return compare(self.plan,self.snapshot if snapshot is None else snapshot,'p1',segment_ids=kw.get('ids',self.ids),resources=self.sources,
                       layers=self.layers,audio_roles={'voz':'fala'},source_proofs=kw.get('proofs'))
    def test_conforme_e_layer_aviso(self):
        self.assertEqual(self.run_compare()['status'],'conforme')
        snap=copy.deepcopy(self.snapshot)
        next(s for s in snap['segments'] if s['id']==self.ids['text:titulo'])['layout']['layer']=4
        result=self.run_compare(snap)
        self.assertEqual(result['status'],'conforme')
        self.assertIn('layer_diferente',[f['code'] for f in result['findings']])
    def test_tipo_audio_minusculo_como_retorno_do_servidor(self):
        snap=copy.deepcopy(self.snapshot)
        audio=next(s for s in snap["segments"] if s["id"]==self.ids["audio:voz"])
        audio["attributes"]["meta_type"]="sound"
        self.assertEqual(self.run_compare(snap)["status"],"conforme")
    def test_detecta_missing_tempos_fonte_texto_audio(self):
        snap=copy.deepcopy(self.snapshot)
        audio=next(s for s in snap['segments'] if s['id']==self.ids['audio:voz'])
        audio['timeline']['start.ms']=20;audio['attributes']['volume']=0.2
        text=next(s for s in snap['segments'] if s['id']==self.ids['text:titulo']);text['attributes']['content']='Errado'
        video=next(s for s in snap['segments'] if s['id']==self.ids['video:clip']);video['attributes']['source']='vid://outro'
        result=self.run_compare(snap)
        self.assertEqual(result['status'],'divergente')
        codes={f['code'] for f in result['findings']}
        self.assertTrue({'inicio','volume','texto','fonte_divergente'} <= codes)
        snap['segments']=[s for s in snap['segments'] if s['id']!=self.ids['audio:voz']]
        self.assertIn('segmento_ausente',{f['code'] for f in self.run_compare(snap)['findings']})
    def test_asset_exige_prova_e_versao(self):
        snap=copy.deepcopy(self.snapshot)
        for s in snap['segments']:
            if s['id'] in (self.ids['video:clip'],self.ids['audio:voz']):s['attributes']['source']='asset://space/media'
        self.assertEqual(self.run_compare(snap)['status'],'incompleto')
        proof={'v':{'expected':'vid://v1','actual':'asset://space/media','package_id':'p1','evidence':'conferido no upload e salvamento'}}
        self.assertEqual(self.run_compare(snap,proofs=proof)['status'],'conforme')
        proof['v']['package_id']='anterior'
        self.assertEqual(self.run_compare(snap,proofs=proof)['status'],'incompleto')
    def test_binding_ausente_ou_duplicado_e_snapshot_invalido(self):
        ids=self.ids.copy();ids.pop('video:clip')
        self.assertEqual(self.run_compare(ids=ids)['status'],'incompleto')
        ids=self.ids.copy();ids['audio:voz']=ids['video:clip']
        self.assertIn('binding_duplicado',{f['code'] for f in self.run_compare(ids=ids)['findings']})
        with self.assertRaises(InvalidReadback):self.run_compare({'segments':[]})
