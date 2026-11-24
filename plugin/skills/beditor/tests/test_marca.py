"""Marca é de quem edita — uma por canal ou cliente — e o painel é de cada conta.

O que se tranca:
- a marca vale nesta ordem: BEDITOR_MARCA, a do projeto, a padrão da máquina;
  nenhuma → estilo da casa, sem inventar identidade;
- dois projetos na mesma máquina podem usar marcas diferentes (clientes);
- marca pedida e inexistente para dizendo quais existem;
- cores e estilos da marca chegam em quem desenha, e sem marca vale a casa;
- o endereço da mesa e do painel mora no config da máquina, não no plugin;
- nada de marca pessoal nem endereço de artifact dentro do que se distribui.
"""
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "skills" / "beditor" / "scripts"))
import marca  # noqa: E402
import setup  # noqa: E402


class _Maquina(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        self._env = {k: os.environ.get(k) for k in ("BEDITOR_CONFIG", "BEDITOR_MARCA")}
        os.environ["BEDITOR_CONFIG"] = str(self.r / "config.json")
        os.environ.pop("BEDITOR_MARCA", None)
        (self.r / "config.json").write_text(json.dumps(
            {"versao": 1, "pastas": {"marcas": str(self.r / "marcas")}}), encoding="utf-8")

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()


class TestResolucao(_Maquina):
    def test_sem_marca_vale_a_casa(self):
        self.assertIsNone(marca.resolver())

    def test_clientes_diferentes_em_projetos_diferentes(self):
        marca.nova("Cliente A")
        marca.nova("Cliente B", padrao=True)
        pa, pb = self.r / "proj-a", self.r / "proj-b"
        pa.mkdir(); pb.mkdir()
        marca.usar("cliente-a", projeto=pa)
        self.assertEqual(marca.resolver(projeto=pa).nome, "cliente-a")
        self.assertEqual(marca.resolver(projeto=pb).nome, "cliente-b")      # cai na padrão
        os.environ["BEDITOR_MARCA"] = "cliente-b"
        self.assertEqual(marca.resolver(projeto=pa).nome, "cliente-b")      # a variável manda

    def test_marca_inexistente_para_listando_as_que_existem(self):
        marca.nova("Canal")
        with self.assertRaises(SystemExit) as e:
            marca.resolver(nome="outra")
        self.assertIn("canal", str(e.exception))

    def test_cor_e_estilo_da_marca(self):
        pasta = marca.nova("Loja")
        dados = json.loads((pasta / "marca.json").read_text(encoding="utf-8"))
        dados["cores"]["destaque"] = "#F0B95B"
        dados["estilos"] = {"hook": "editorial"}
        (pasta / "marca.json").write_text(json.dumps(dados), encoding="utf-8")
        mc = marca.resolver(nome="loja")
        self.assertEqual(mc.cor("destaque", (0, 0, 0)), (240, 185, 91))
        self.assertEqual(mc.cor("texto", (1, 2, 3)), (1, 2, 3))              # vazio → padrão
        import estilos
        self.assertEqual(estilos.escolher({"marca": "loja"}, "hook"), "editorial")
        self.assertEqual(estilos.escolher({"marca": "loja", "estilos": {"hook": "vox"}}, "hook"), "vox")
        self.assertEqual(estilos.escolher(None, "hook"), estilos.PADRAO["hook"])


class TestArtefatoPorConta(_Maquina):
    def test_grava_e_le_por_maquina(self):
        self.assertEqual(setup.artefato("mesa"), "")
        setup.artefato("mesa=https://claude.ai/code/artifact/abc")
        self.assertEqual(setup.artefato("mesa"), "https://claude.ai/code/artifact/abc")
        with self.assertRaises(SystemExit):
            setup.artefato("mesa=nao-e-url")
        with self.assertRaises(SystemExit):
            setup.artefato("outro=https://x")


class TestNadaPessoalNoPlugin(unittest.TestCase):
    ALVOS = ("skills", "commands", "agents", "painel", "README.md", ".claude-plugin")
    GERADOS = {"painel/index.html", "painel/estado.json", "painel/revisao.json", "painel/telemetria.json"}

    def _textos(self):
        for alvo in self.ALVOS:
            p = RAIZ / alvo
            arquivos = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
            for f in arquivos:
                rel = f.relative_to(RAIZ).as_posix()
                if (f.suffix not in (".md", ".py", ".json", ".yaml", ".html", ".sh")
                        or "/tests/" in rel or rel in self.GERADOS):
                    continue
                yield rel, f.read_text(encoding="utf-8", errors="replace")

    def test_sem_marca_pessoal(self):
        achados = [rel for rel, t in self._textos()
                   if re.search(r"mechamedebento|branding-bento|branding-usuario", t)]
        self.assertEqual(achados, [], "marca pessoal viajando com o plugin:\n" + "\n".join(achados))

    def test_sem_endereco_fixo_de_artifact(self):
        achados = [rel for rel, t in self._textos()
                   if re.search(r"claude\.ai/code/artifact/[0-9a-f]{8}-", t)]
        self.assertEqual(achados, [], "endereço de artifact de uma conta dentro do plugin:\n" + "\n".join(achados))


if __name__ == "__main__":
    unittest.main()
