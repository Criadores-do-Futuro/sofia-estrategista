import sys, tempfile, unittest
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "painel"))
import gerar


class TestPainel(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = self.raiz = Path(self.tmp.name)
        for p, t in {"skills/beditor/referencias/x.md": "regra do corte",
                     "skills/beditor/scripts/x.py": "def cortar(): pass",
                     "skills/beditor/tests/test_x.py": "    def test_corta(self): pass",
                     "Entregas/05 - video 1080x1920.mp4": ""}.items():
            (r / p).parent.mkdir(parents=True, exist_ok=True)
            (r / p).write_text(t, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def conf(self, ev):
        return [gerar.conferir(e, self.raiz, self.raiz / "Entregas") for e in ev]

    def test_trecho_que_sumiu_quebra_a_evidencia(self):
        c = self.conf(["skills/beditor/referencias/x.md#regra que nao existe"])[0]
        self.assertFalse(c["ok"])
        self.assertIn("trecho", c["motivo"])

    def test_nivel_sobe_so_com_a_evidencia_da_classe(self):
        regra = "skills/beditor/referencias/x.md#regra do corte"
        maq = "skills/beditor/scripts/x.py#def cortar"
        teste = "skills/beditor/tests/test_x.py#def test_corta"
        self.assertEqual(gerar.provado(self.conf([regra])), 2)
        self.assertEqual(gerar.provado(self.conf([regra, maq])), 2)   # máquina sem teste
        self.assertEqual(gerar.provado(self.conf([regra, maq, teste])), 3)
        self.assertEqual(gerar.provado(self.conf([regra, maq, teste, "entrega:05 - *"])), 4)
        self.assertEqual(gerar.provado(self.conf([maq])), 1)

    def test_entrega_sem_pasta_montada_nao_conta_nem_quebra(self):
        c = gerar.conferir("entrega:05 - *", self.raiz, self.raiz / "nao-montado")
        self.assertIsNone(c["ok"])

    def test_celula_declarada_alta_cai_ate_a_prova(self):
        crit = {"id": "cortes", "base": {"nivel": 3, "evidencias": []}}
        fmt = {"reconhecido": True, "celulas": {"cortes": {
            "nivel": 4, "evidencias": ["skills/beditor/referencias/x.md#regra do corte"]}}}
        x = gerar.celula(crit, fmt, self.raiz, None)
        self.assertEqual((x["declarado"], x["efetivo"]), (4, 2))
        self.assertIn("sustentam 2", x["motivo"])

    def test_formato_nao_reconhecido_herda_no_maximo_1(self):
        base = {"nivel": 3, "evidencias": ["skills/beditor/referencias/x.md#regra do corte",
                                           "skills/beditor/scripts/x.py",
                                           "skills/beditor/tests/test_x.py#def test_corta"]}
        crit = {"id": "cortes", "base": base}
        self.assertEqual(gerar.celula(crit, {"reconhecido": True}, self.raiz, None)["efetivo"], 3)
        x = gerar.celula(crit, {"reconhecido": False}, self.raiz, None)
        self.assertEqual(x["efetivo"], 1)
        self.assertTrue(x["herdada"])

    def test_criterios_do_repo_nao_tem_evidencia_quebrada(self):
        import yaml
        dados = yaml.safe_load((RAIZ / "painel/criterios.yaml").read_text(encoding="utf-8"))
        estado = gerar.calcular(dados)
        self.assertEqual(estado["quebradas"], 0)
        self.assertEqual(len(estado["criterios"]), 7)


if __name__ == "__main__":
    unittest.main()
