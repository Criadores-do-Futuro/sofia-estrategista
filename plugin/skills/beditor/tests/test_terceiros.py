"""O plugin leva o que foi aprendido, nunca o material de quem ensinou.

O que se tranca:
- nenhuma imagem ou vídeo dentro de `treinamento/` (só ESTILO.md e medicoes.json);
- nenhum link de post ou perfil de rede social no que se distribui;
- nenhum @perfil de criador (os exemplos de formulário usam nomes fictícios);
- nenhum caminho de disco de máquina nos textos distribuídos;
- a licença existe e o plugin.json aponta para ela.
"""
import json
import re
import subprocess
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
TEXTO = {".md", ".py", ".json", ".yaml", ".yml", ".html", ".sh", ".tsx", ".ts", ".css", ".txt"}
# link de post ou perfil: o domínio seguido de caminho. Citar o domínio (`tiktok.com`) é permitido.
REDE = re.compile(r"(youtube\.com|youtu\.be|tiktok\.com|instagram\.com|twitter\.com|x\.com|facebook\.com)/[^\s`'\")]", re.I)
# @perfil: começa em fronteira, não é decorador de código nem pacote npm/brew
PERFIL = re.compile(r"(?<![\w.@/])@([a-z][a-z0-9_.]{3,})\b")
PERMITIDOS = {
    "perfil_analisado", "meucanal", "arroba", "teste", "canal1", "canal2", "criador",
    # decoradores, at-rules e pacotes que aparecem no código
    "property", "staticmethod", "classmethod", "dataclass", "font-face", "media", "keyframes",
    "import", "supports", "layer", "container", "charset", "page", "functools", "unittest",
    "latest", "version", "types", "remotion", "beditor", "context-mode", "mock", "wraps",
    "abstractmethod", "contextmanager", "cache", "font", "keyframe", "grupocriadores",
}
MAQUINA = re.compile(r"/Volumes/(?!SSD/|<)|/Users/")


def distribuidos():
    saida = subprocess.run(["git", "-C", str(RAIZ), "ls-files", "-z"], capture_output=True, check=True)
    for rel in saida.stdout.decode("utf-8").split("\0"):
        if rel and (RAIZ / rel).is_file():
            yield rel


class TestNadaDeTerceiros(unittest.TestCase):
    def _textos(self):
        for rel in distribuidos():
            if Path(rel).suffix in TEXTO and "/tests/" not in rel:
                yield rel, (RAIZ / rel).read_text(encoding="utf-8", errors="replace")

    def test_treinamento_sem_imagem_nem_video(self):
        ruins = [r for r in distribuidos() if r.startswith("treinamento/")
                 and Path(r).name not in ("ESTILO.md", "medicoes.json")]
        self.assertEqual(ruins, [], "material de terceiros em treinamento/:\n" + "\n".join(ruins))

    def test_sem_link_de_rede_social(self):
        achados = [f"{rel}:{n}" for rel, t in self._textos()
                   for n, linha in enumerate(t.splitlines(), 1) if REDE.search(linha)]
        self.assertEqual(achados, [], "link de post ou perfil no plugin:\n" + "\n".join(achados))

    def test_sem_arroba_de_criador(self):
        achados = []
        for rel, t in self._textos():
            if Path(rel).suffix not in (".md", ".json", ".yaml", ".html"):
                continue
            for n, linha in enumerate(t.splitlines(), 1):
                for m in PERFIL.finditer(linha):
                    nome = m.group(1).lower()
                    if nome not in PERMITIDOS and not nome.split(".")[0] in PERMITIDOS:
                        achados.append(f"{rel}:{n}: @{nome}")
        self.assertEqual(achados, [], "perfil de terceiro no plugin:\n" + "\n".join(achados))

    def test_sem_caminho_de_maquina_nos_textos(self):
        achados = [f"{rel}:{n}" for rel, t in self._textos()
                   for n, linha in enumerate(t.splitlines(), 1) if MAQUINA.search(linha)]
        self.assertEqual(achados, [], "caminho de uma máquina no plugin:\n" + "\n".join(achados))

    def test_licenca_restrita(self):
        self.assertTrue((RAIZ / "LICENSE").is_file())
        self.assertIn("revender", (RAIZ / "LICENSE").read_text(encoding="utf-8"))
        plugin = json.loads((RAIZ / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        licenca = plugin.get("license", "")
        self.assertTrue(licenca.startswith("LicenseRef-") or "LICENSE" in licenca, licenca)


if __name__ == "__main__":
    unittest.main()
