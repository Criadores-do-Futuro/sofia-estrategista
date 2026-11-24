"""A midiateca guarda cada mídia UMA vez e o projeto só aponta para ela.

O que se tranca:
- o mesmo conteúdo com dois nomes vira um item só (chave por conteúdo);
- migrar sem --sim não mexe em nada; com --sim move, troca o caminho nos JSON
  do projeto por `midia:` e apaga a pasta `acervo/` vazia;
- a busca acha pelo título e pela fala transcrita;
- `resolver` leva `midia:` para a pasta configurada e deixa o resto como está.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import midiateca  # noqa: E402


class TestMidiateca(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.midia = base / "Midia"
        self.midia.mkdir()
        cfg = base / "config.json"
        cfg.write_text(json.dumps({"versao": 1, "pastas": {"midia": str(self.midia)}}))
        self._env = os.environ.get("BEDITOR_CONFIG")
        os.environ["BEDITOR_CONFIG"] = str(cfg)
        self.proj = base / "16 - Teste"
        self.acervo = self.proj / "edicao" / "acervo"
        self.acervo.mkdir(parents=True)

    def tearDown(self):
        if self._env is None:
            os.environ.pop("BEDITOR_CONFIG", None)
        else:
            os.environ["BEDITOR_CONFIG"] = self._env
        self.tmp.cleanup()

    def _projeto(self):
        (self.acervo / "manchete.png").write_bytes(b"\x89PNG-conteudo-a")
        (self.acervo / "copia.png").write_bytes(b"\x89PNG-conteudo-a")      # mesmo conteúdo, outro nome
        (self.acervo / "cama.m4a").write_bytes(b"audio-b")
        plano = {"fontes": {"manchete": {"arq": "edicao/acervo/manchete.png", "url": "https://ex.com/a",
                                         "titulo": "Manchete do vinco", "autor": "9to5Mac", "tipo": "prova social"}},
                 "musicas": {"cama": {"arq": "edicao/acervo/cama.m4a"}}}
        (self.proj / "edicao" / "plano.json").write_text(json.dumps(plano))

    def test_simulacao_nao_mexe(self):
        self._projeto()
        rel = midiateca.migrar(self.proj, sim=False)
        self.assertEqual(len(rel), 3)
        self.assertTrue((self.acervo / "manchete.png").exists())
        self.assertFalse((self.midia / "catalogo.json").exists())

    def test_migrar_deduplica_e_troca_caminho(self):
        self._projeto()
        midiateca.migrar(self.proj, sim=True)
        cat = midiateca.carregar(self.midia)
        self.assertEqual(len(cat["itens"]), 2)                    # as duas PNG iguais viraram uma
        self.assertFalse(self.acervo.exists())
        plano = json.loads((self.proj / "edicao" / "plano.json").read_text())
        ref = plano["fontes"]["manchete"]["arq"]
        self.assertTrue(ref.startswith("midia:imagens/"))
        self.assertTrue(midiateca.resolver(ref).exists())
        self.assertTrue(plano["musicas"]["cama"]["arq"].startswith("midia:audios/"))
        item = next(it for it in cat["itens"].values() if it["tipo"] == "imagens")
        self.assertEqual(item["autor"], "9to5Mac")
        self.assertIn("16 - Teste", item["projetos"])

    def test_busca_pela_fala(self):
        self._projeto()
        midiateca.migrar(self.proj, sim=True)
        cat = midiateca.carregar(self.midia)
        k = next(k for k, it in cat["itens"].items() if it["tipo"] == "audios")
        (self.midia / "transcricoes").mkdir(exist_ok=True)
        (self.midia / "transcricoes" / f"{k}.whisper.json").write_text(
            json.dumps({"segments": [{"start": 12.0, "text": "a dobradiça junta poeira"}]}))
        cat["itens"][k]["transcricao"] = f"transcricoes/{k}.whisper.json"
        midiateca.salvar(self.midia, cat)
        achados = midiateca.buscar("dobradica poeira")
        self.assertEqual(len(achados), 1)
        self.assertEqual(achados[0]["trechos"][0][0], 12.0)
        self.assertEqual(len(midiateca.buscar("vinco manchete")), 1)

    def test_resolver_deixa_caminho_comum(self):
        self.assertEqual(midiateca.resolver("edicao/x.mp4"), Path("edicao/x.mp4"))


if __name__ == "__main__":
    unittest.main()
