"""O plugin não pode carregar o disco de quem o escreveu.

Estes testes trancam o que quebra quando o bEditor vai para outro computador:

- nenhum caminho absoluto de máquina (`/Volumes/...`, `/Users/...`) no código
  que roda — documentação pode citar o disco do autor como exemplo, código não;
- `entregar.py` sem pasta configurada **para e manda configurar**, em vez de
  cair num caminho que só existe na máquina de origem;
- o binário que o formato `analise` exige aparece como FALTA no setup, não como
  «opcional» — marcá-lo opcional fazia a máquina nova passar no setup e morrer
  no meio do primeiro render.
"""
import os
import platform
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "skills" / "beditor" / "scripts"))
import setup  # noqa: E402

# `~/.beditor` e `~/.config/beditor` são a casa do plugin em QUALQUER máquina —
# expandem por usuário e não são endereço de ninguém.
ABSOLUTO = re.compile(r"(?:/Volumes/|/Users/)")


class TestSemCaminhoDeMaquina(unittest.TestCase):
    def test_nenhum_script_tem_caminho_absoluto_de_maquina(self):
        alvos = [p for d in ("skills/beditor/scripts", "painel")
                 for p in (RAIZ / d).rglob("*.py")
                 if "tests" not in p.parts]
        self.assertGreater(len(alvos), 20, "não achei os scripts — caminho errado?")
        culpados = []
        for p in alvos:
            for n, linha in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if ABSOLUTO.search(linha) and not linha.lstrip().startswith("#"):
                    culpados.append(f"{p.relative_to(RAIZ)}:{n}: {linha.strip()[:90]}")
        self.assertEqual(culpados, [], "caminho de máquina em código que roda:\n" + "\n".join(culpados))


class TestEntregarSemConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._antes = {k: os.environ.get(k) for k in ("BEDITOR_CONFIG", "BEDITOR_ENTREGAS")}
        os.environ["BEDITOR_CONFIG"] = str(Path(self.tmp.name) / "config.json")
        os.environ.pop("BEDITOR_ENTREGAS", None)

    def tearDown(self):
        for k, v in self._antes.items():
            os.environ[k] = v if v is not None else os.environ.pop(k, "") and ""
            if v is None:
                os.environ.pop(k, None)
        self.tmp.cleanup()

    def test_para_e_manda_configurar(self):
        import importlib
        import entregar
        entregar = importlib.reload(entregar)
        with self.assertRaises(SystemExit) as e:
            entregar.raiz()
        msg = str(e.exception)
        self.assertIn("entregas", msg)
        self.assertIn("setup", msg)


class TestBinarioDoAnalise(unittest.TestCase):
    def test_rastreador_ausente_conta_como_falta_no_mac(self):
        if platform.system() != "Darwin":
            self.skipTest("os binários Swift só existem em macOS")
        with tempfile.TemporaryDirectory() as tmp:
            v = setup.verificar(which=lambda b: f"/opt/bin/{b}", tem_modulo=lambda m: True,
                                home=tmp, conferir_dataless=False)
        i = {x["id"]: x for x in v["itens"]}["bin-rastrear-rosto"]
        self.assertEqual(i["estado"], "falta")
        self.assertIn("analise", i["detalhe"])
        self.assertIn("instalar_bin.sh", i["instalar"])


class TestScriptsAbremSemDependencia(unittest.TestCase):
    """`--help` de cada script tem que responder — pega import quebrado e
    dependência que ninguém declarou, que é o erro que aparece na máquina do
    outro e nunca na nossa."""

    def test_todos_os_scripts_respondem_help(self):
        pasta = RAIZ / "skills" / "beditor" / "scripts"
        quebrados = []
        for p in sorted(pasta.glob("*.py")):
            if p.name.startswith("_"):
                continue
            r = subprocess.run([sys.executable, str(p), "--help"],
                               capture_output=True, text=True, timeout=120)
            # Script sem argparse pode sair != 0; o que não pode é estourar import.
            if "Traceback" in r.stderr and "ModuleNotFoundError" in r.stderr:
                quebrados.append(f"{p.name}: {r.stderr.strip().splitlines()[-1][:100]}")
        self.assertEqual(quebrados, [], "dependência faltando:\n" + "\n".join(quebrados))


if __name__ == "__main__":
    unittest.main()
