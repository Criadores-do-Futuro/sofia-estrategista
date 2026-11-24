import copy
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugin'))  # o pacote beditor mora em plugin/
from beditor.capcut_web_revision import prepare_revision, UnsupportedRevision

root = Path.home() / '.codex/plugins/cache/CapCut/CapCut'
choices = sorted(root.glob('*/skills/capcut-stdraft-builder/scripts'))
skill = Path(os.environ['BEDITOR_CAPCUT_BUILDER']) if os.environ.get('BEDITOR_CAPCUT_BUILDER') else (choices[-1] if choices else None)
try:
    if skill is None:
        raise ImportError('builder não instalado')
    sys.path.insert(0, str(skill))
    from apply_materials import apply_text, apply_video
    from manage_materials import update_material, update_placement, remove_material
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def new_draft():
    root = {'version':'0.1.0','segments':[{'id':'draft','type':'DRAFT','attributes':{'width':720,'height':1280,'ratio_type':'custom'}}]}
    result = apply_video(root, source='vid://abc', start_ms=0, duration_ms=1000, layer=0)
    video = result['added_segment_ids'][0]
    result = apply_text(result['draft'], content='Antes', start_ms=0, duration_ms=1000, layout={'layer':1})
    return result['draft'], video, result['added_segment_ids'][0]

@unittest.skipUnless(AVAILABLE, 'builder oficial não disponível')
class RevisionTest(unittest.TestCase):
    def revise(self, draft, operations, package='package-1'):
        return prepare_revision(draft, package, operations, update_material=update_material,
                                update_placement=update_placement, remove_material=remove_material)
    def test_texto_e_posicao_com_builder_real_preservam_snapshot(self):
        draft, video, text = new_draft(); original=copy.deepcopy(draft)
        out = self.revise(draft,[{'op':'content','segment_id':text,'text':'Depois'},
                                 {'op':'placement','segment_id':video,'start_ms':1500}])
        self.assertEqual(draft,original)
        items = {s['id']:s for s in out['draft']['segments']}
        self.assertEqual(items[text]['attributes']['content'],'Depois')
        self.assertEqual(items[video]['timeline']['start.ms'],1500)
        self.assertEqual(out['base_package_id'],'package-1')
        self.assertTrue(any('sincronismo' in w for w in out['warnings']))
    def test_texto_da_nuvem_com_patch_mantem_estilo(self):
        draft, video, text = new_draft()
        draft['segments'].append({'id':'patch','type':'PATCH','parent_id':text,
                                  'attributes':{'letter_start':0,'letter_end':5,
                                                'font':'vimo://7317175475195875841'}})
        out=self.revise(draft,[{'op':'content','segment_id':text,'text':'Novo!'}])
        itens={s['id']:s for s in out['draft']['segments']}
        self.assertEqual(itens[text]['attributes']['content'],'Novo!')
        self.assertEqual(itens['patch']['attributes']['letter_end'],5)
        self.assertEqual(next(s for s in draft['segments'] if s['id']==text)['attributes']['content'],'Antes')
        with self.assertRaises(UnsupportedRevision):
            self.revise(draft,[{'op':'content','segment_id':text,'text':'Texto mais longo'}])

    def test_remocao_e_limites(self):
        draft, video, text = new_draft(); original=copy.deepcopy(draft)
        out=self.revise(draft,[{'op':'remove','segment_id':text}])
        self.assertNotIn(text,[s['id'] for s in out['draft']['segments']])
        self.assertEqual(draft,original)
        for ops in ([{'op':'remove','segment_id':'draft'}],
                    [{'op':'content','segment_id':video,'text':'x'}],
                    [{'op':'remove','segment_id':text,'unexpected':True}],
                    [{'op':'placement','segment_id':text,'layout':{'hidden':1}}],
                    [{'op':'placement','segment_id':text,'start_ms':True}]):
            with self.subTest(ops=ops), self.assertRaises(UnsupportedRevision): self.revise(draft,ops)
        with self.assertRaises(UnsupportedRevision): self.revise(draft,[{'op':'remove','segment_id':text}],package='')
    def test_nao_edita_legenda_nem_remove_cascata(self):
        draft, video, text = new_draft()
        item=next(s for s in draft['segments'] if s['id']==text)
        item['attributes']['caption_timeline']=[{'text':'x','start.ms':0,'end.ms':100}]
        with self.assertRaises(UnsupportedRevision): self.revise(draft,[{'op':'content','segment_id':text,'text':'y'}])
        draft['segments'].append({'id':'child','type':'PATCH','parent_id':video})
        with self.assertRaises(UnsupportedRevision): self.revise(draft,[{'op':'remove','segment_id':video}])
    def test_colisao_no_builder_nao_altera_original(self):
        draft, video, text = new_draft(); before=copy.deepcopy(draft)
        with self.assertRaises(ValueError): self.revise(draft,[{'op':'placement','segment_id':text,'layout':{'layer':0}}])
        self.assertEqual(draft,before)
