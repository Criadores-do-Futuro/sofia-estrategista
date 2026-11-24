import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import estilos


class TestEstilos(unittest.TestCase):
    def test_padrao_da_casa_por_elemento(self):
        # hook e o `editorial` (a serifa que o dono aprovou); o resto e vox
        self.assertEqual(estilos.escolher(None, "hook"), "editorial")
        for elemento in ("legenda", "motion", "musica", "sfx"):
            self.assertEqual(estilos.escolher(None, elemento), "vox")
            self.assertEqual(estilos.escolher({}, elemento), "vox")

    def test_guia_escolhe_por_cima_do_padrao(self):
        guia = {"estilos": {"hook": "editorial"}}
        self.assertEqual(estilos.escolher(guia, "hook"), "editorial")
        self.assertEqual(estilos.escolher(guia, "legenda"), "vox")  # não escolhido, cai no padrão

    def test_padrao_do_canal_vence_o_padrao_da_casa_mas_nao_o_guia(self):
        self.assertEqual(estilos.escolher({}, "hook", padrao_canal="editorial"), "editorial")
        guia = {"estilos": {"hook": "minimal"}}
        self.assertEqual(estilos.escolher(guia, "hook", padrao_canal="editorial"), "minimal")

    def test_tokens_traz_o_dicionario_do_estilo_escolhido(self):
        # 2026-09-12, o dono: "use montserrat no hook visual" — hook e legenda
        # `editorial` sao a mesma voz tipografica, e a serifa Fraunces discordava
        self.assertEqual(estilos.tokens(None, "hook")["fonte"], "'Montserrat',-apple-system,sans-serif")
        t = estilos.tokens({"estilos": {"hook": "vox"}}, "hook")
        self.assertEqual(t["fonte"], "'Archivo Black',Impact,sans-serif")

    def test_validar_aceita_ids_da_galeria(self):
        guia = {"estilos": {"hook": "vox", "legenda": "editorial",
                            "musica": "vox", "sfx": "editorial"}}
        self.assertEqual(estilos.validar(guia), [])

    def test_validar_recusa_id_fora_da_galeria(self):
        erros = estilos.validar({"estilos": {"hook": "punk"}})
        self.assertTrue(any("hook" in e and "punk" in e for e in erros))

    def test_validar_recusa_elemento_que_nao_existe(self):
        erros = estilos.validar({"estilos": {"camera": "vox"}})
        self.assertTrue(any("camera" in e for e in erros))

    def test_musica_vox_tem_ataque_mais_curto_que_editorial(self):
        self.assertLess(estilos.MUSICA["vox"]["sobe_mult"], estilos.MUSICA["editorial"]["sobe_mult"])

    def test_hook_voltou_ao_editorial_e_motion_e_vox(self):
        # pedido do dono em 2026-09-11: "o hook visual prefiro como estava antes
        # do vox, quero vox pra motion"
        self.assertEqual(estilos.PADRAO["hook"], "editorial")
        self.assertEqual(estilos.PADRAO["motion"], "vox")

    def test_todo_estilo_de_motion_tem_origem_tokens_materia_e_acabamento(self):
        for nome, e in estilos.MOTION.items():
            # a origem e um corpus medido em Treinamento/ ou uma referencia/direcao
            # escrita pelo dono, com data — nunca um estilo sem procedencia
            self.assertTrue(e["origem"].startswith("Treinamento/") or "dono" in e["origem"], nome)
            self.assertTrue(e["materia"].strip(), nome)
            for chave in ("FUNDO", "TEXTO", "DESTAQUE", "CARTAO", "FONTE_TITULO"):
                self.assertIn(chave, e["tokens"], f"{nome} sem {chave}")
            for chave in ("vinheta", "halftone_cor", "grao_opacidade"):
                self.assertIn(chave, e["acabamento"], f"{nome} sem {chave}")

    def test_tokens_de_motion_tem_todos_as_mesmas_chaves(self):
        # um estilo sem uma chave deixaria o hf.py com o token do estilo anterior
        chaves = [set(e["tokens"]) for e in estilos.MOTION.values()]
        self.assertTrue(all(k == chaves[0] for k in chaves))

    def test_acabamento_de_estilo_desconhecido_cai_no_padrao(self):
        self.assertEqual(estilos.acabamento("inexistente"),
                         estilos.acabamento(estilos.PADRAO["motion"]))


if __name__ == "__main__":
    unittest.main()
