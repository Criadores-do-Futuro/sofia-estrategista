import copy
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugin'))  # o pacote beditor mora em plugin/
from beditor.capcut_web import apply_new_plan, UnsupportedWebPlan

root = Path.home() / '.codex/plugins/cache/CapCut/CapCut'
choices = sorted(root.glob('*/skills/capcut-stdraft-builder/scripts'))
SKILL = Path(os.environ['BEDITOR_CAPCUT_BUILDER']) if os.environ.get('BEDITOR_CAPCUT_BUILDER') else (choices[-1] if choices else None)
try:
    if SKILL is None:
        raise ImportError('builder não instalado')
    sys.path.insert(0, str(SKILL))
    from apply_materials import apply_video, apply_audio, apply_text
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def source_plan():
    return {'version':'1.0', 'project':{'title':'Teste','editor':'capcut','creative_format':'dinamismo'},
            'assets':[{'id':'v','kind':'video','duration_ms':5000}], 'protected_speech':[],
            'clips':[{'id':'a','asset_id':'v','track':'v1','kind':'video','source':{'start_ms':500,'end_ms':1500},
                      'timeline':{'start_ms':0,'end_ms':1000}, 'carries_source_audio':True}],
            'text_layers':[{'id':'t','type':'lettering','track':'t1','text':'Olá',
                            'timeline':{'start_ms':0,'end_ms':1000}}]}


def draft():
    return {'version':'0.1.0','segments':[{'id':'draft','type':'DRAFT','attributes':{'width':720,'height':1280,'ratio_type':'custom'}}]}

@unittest.skipUnless(AVAILABLE, 'builder oficial do CapCut não disponível')
class CapCutWebTests(unittest.TestCase):
    def apply(self, original, plan, **kw):
        return apply_new_plan(original, plan, resources=kw.get('resources', {'v':'vid://example-video'}),
                              video_layers={'v1':0}, text_layers={'t1':1}, apply_video=apply_video, apply_text=apply_text,
                              apply_audio=apply_audio, audio_layers=kw.get('audio_layers', {'a1':0, 'a2':1}),
                              audio_roles=kw.get('audio_roles', {}), audio_volumes=kw.get('audio_volumes', {}), text_layouts=kw.get('text_layouts'))
    def test_builder_real_preserva_entrada_e_traduz_tempos(self):
        original=draft(); before=copy.deepcopy(original); result=self.apply(original,source_plan())
        self.assertEqual(original,before)
        index={s['id']:s for s in result['draft']['segments']}
        video=index[result['segment_ids']['video:a']]
        text=index[result['segment_ids']['text:t']]
        self.assertEqual(video['attributes']['start.ms'],500)
        self.assertEqual(video['timeline']['duration.ms'],1000)
        self.assertEqual(video['attributes']['volume'],1.0)
        self.assertEqual(text['attributes']['content'],'Olá')
        self.assertEqual(text['layout']['layer'],1)
        self.assertTrue(any('SOURCE_RANGE_UNVERIFIED' in w for w in result['warnings']))
    def test_layout_de_texto_e_validacao(self):
        result=self.apply(draft(),source_plan(),text_layouts={'t':{'position_y':-0.7}})
        text=next(s for s in result['draft']['segments'] if s['id']==result['segment_ids']['text:t'])
        self.assertEqual(text['layout']['position_y'], -0.7)
        with self.assertRaises(UnsupportedWebPlan): self.apply(draft(),source_plan(),text_layouts={'t':{'position_y':2}})
        with self.assertRaises(UnsupportedWebPlan): self.apply(draft(),source_plan(),text_layouts={'t':{'position_y':10**500}})
        with self.assertRaises(UnsupportedWebPlan): self.apply(draft(),source_plan(),text_layouts={'nao-existe':{}})
    def test_nao_reaplica_ou_descarta_conteudo(self):
        original=draft(); plan=source_plan(); result=self.apply(original,plan)
        with self.assertRaises(UnsupportedWebPlan): self.apply(result['draft'],plan)
        plan['text_layers'][0]['type']='caption'
        with self.assertRaises(UnsupportedWebPlan): self.apply(original,plan)
        plan['text_layers'][0]['type']='lettering'; plan['text_layers'][0]['style']={'font':'Arial'}
        with self.assertRaises(UnsupportedWebPlan): self.apply(original,plan)
        self.assertEqual(len(original['segments']),1)
    def test_audio_independente_com_j_cut_e_trilha(self):
        plan=source_plan()
        plan['clips'][0]['carries_source_audio']=False
        plan['clips'][0]['timeline']={'start_ms':200,'end_ms':1200}
        plan['clips'].append({'id':'fala','asset_id':'v','track':'a1','kind':'audio',
                              'source':{'start_ms':300,'end_ms':1500},'timeline':{'start_ms':0,'end_ms':1200}})
        plan['assets'].append({'id':'musica','kind':'audio','duration_ms':3000})
        plan['clips'].append({'id':'trilha','asset_id':'musica','track':'a2','kind':'audio',
                              'source':{'start_ms':100,'end_ms':1300},'timeline':{'start_ms':0,'end_ms':1200}})
        result=self.apply(draft(),plan,resources={'v':'vid://example-video','musica':'sid://example-music'},
                          audio_roles={'fala':'fala','trilha':'musica'},audio_volumes={'trilha':0.2})
        segments={s['id']:s for s in result['draft']['segments']}
        video=segments[result['segment_ids']['video:a']]
        speech=segments[result['segment_ids']['audio:fala']]
        music=segments[result['segment_ids']['audio:trilha']]
        self.assertEqual(video['attributes']['volume'],0)
        self.assertEqual(video['timeline']['start.ms'],200)
        self.assertEqual(speech['timeline']['start.ms'],0)
        self.assertEqual(speech['attributes']['start.ms'],300)
        self.assertEqual(speech['attributes']['meta_type'],'SOUND')
        self.assertEqual(music['attributes']['meta_type'],'MUSIC')
        self.assertEqual(music['attributes']['volume'],0.2)
        self.assertEqual(speech['layout']['layer'],0)
        self.assertEqual(music['layout']['layer'],1)
        self.assertTrue(any('Fala mapeada' in w for w in result['warnings']))
    def test_audio_exige_papel_e_recusa_duplicacao(self):
        plan=source_plan()
        plan['clips'].append({'id':'voz','asset_id':'v','track':'a1','kind':'audio',
                              'source':{'start_ms':500,'end_ms':1500},'timeline':{'start_ms':0,'end_ms':1000}})
        with self.assertRaises(UnsupportedWebPlan): self.apply(draft(),plan)
        with self.assertRaises(UnsupportedWebPlan): self.apply(draft(),plan,audio_roles={'voz':'fala'})
        plan['clips'][0]['carries_source_audio']=False
        for volume in (-1, 5, float('nan'), True):
            with self.subTest(volume=volume), self.assertRaises(UnsupportedWebPlan):
                self.apply(draft(),plan,audio_roles={'voz':'fala'},audio_volumes={'voz':volume})

    def test_recusa_midia_local(self):
        with self.assertRaises(UnsupportedWebPlan): self.apply(draft(),source_plan(),resources={'v':'file:///tmp/x.mp4'})
