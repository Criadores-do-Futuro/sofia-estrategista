"""Cada máquina recebe a escolha mais eficiente para ela — e o Windows não quebra por acento.

O que se tranca:
- Apple Silicon transcreve com mlx-whisper; NVIDIA com faster-whisper em CUDA;
  o resto em CPU int8;
- a prévia usa o codificador de GPU só se ele FUNCIONAR (listado ≠ utilizável),
  e o master nunca sai disto;
- instalar usa brew, winget ou apt conforme o sistema, e o setup no Windows não
  manda `ln -s` nem `export`;
- a notificação vira osascript, PowerShell ou notify-send;
- nenhuma leitura ou escrita de texto sem `encoding` (no Windows o padrão é
  cp1252 e quebra no primeiro acento), e todo ponto de entrada põe o console em
  UTF-8.
"""
import ast
import importlib
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import plataforma  # noqa: E402


def _limpar():
    plataforma.nvidia.cache_clear()
    plataforma._funciona.cache_clear()
    plataforma.codificador_previa.cache_clear()


class TestEscolhas(unittest.TestCase):
    def setUp(self):
        _limpar()

    def tearDown(self):
        _limpar()

    def _em(self, sistema, maquina="x86_64", nvidia=False):
        return [mock.patch.object(plataforma.platform, "system", return_value=sistema),
                mock.patch.object(plataforma.platform, "machine", return_value=maquina),
                mock.patch.object(plataforma, "nvidia", return_value=nvidia)]

    def _com(self, patches, fn):
        for p in patches:
            p.start()
        try:
            return fn()
        finally:
            for p in patches:
                p.stop()

    def test_sistemas(self):
        self.assertEqual(self._com(self._em("Darwin", "arm64"), plataforma.sistema), "mac-arm")
        self.assertEqual(self._com(self._em("Darwin", "x86_64"), plataforma.sistema), "mac-intel")
        self.assertEqual(self._com(self._em("Windows"), plataforma.sistema), "windows")
        self.assertEqual(self._com(self._em("Linux"), plataforma.sistema), "linux")

    def test_transcricao_por_maquina(self):
        self.assertEqual(self._com(self._em("Darwin", "arm64"), plataforma.transcricao)["motor"], "mlx-whisper")
        w_gpu = self._com(self._em("Windows", nvidia=True), plataforma.transcricao)
        self.assertEqual((w_gpu["motor"], w_gpu["device"], w_gpu["compute"]), ("faster-whisper", "cuda", "float16"))
        w_cpu = self._com(self._em("Windows"), plataforma.transcricao)
        self.assertEqual((w_cpu["device"], w_cpu["compute"]), ("cpu", "int8"))
        self.assertEqual(self._com(self._em("Darwin", "x86_64"), plataforma.transcricao)["motor"], "faster-whisper")

    def test_previa_so_usa_gpu_que_funciona(self):
        def rodar():
            _limpar()
            return plataforma.codificador_previa()[0]
        # Windows com NVIDIA listada mas quebrada cai para o próximo que funciona
        with mock.patch.object(plataforma, "_funciona", side_effect=lambda c: c == "h264_qsv"):
            self.assertEqual(self._com(self._em("Windows", nvidia=True), rodar), "h264_qsv")
        with mock.patch.object(plataforma, "_funciona", return_value=False):
            self.assertEqual(self._com(self._em("Windows", nvidia=True), rodar), "libx264")
        with mock.patch.object(plataforma, "_funciona", return_value=True):
            self.assertEqual(self._com(self._em("Darwin", "arm64"), rodar), "h264_videotoolbox")
            self.assertEqual(self._com(self._em("Windows", nvidia=True), rodar), "h264_nvenc")

    def test_instalar_por_sistema(self):
        itens = ["ffmpeg", "yt-dlp"]
        self.assertTrue(self._com(self._em("Darwin", "arm64"), lambda: plataforma.instalar_sistema(itens)).startswith("brew install"))
        w = self._com(self._em("Windows"), lambda: plataforma.instalar_sistema(itens))
        self.assertIn("winget install -e --id Gyan.FFmpeg", w)
        self.assertIn("apt install", self._com(self._em("Linux"), lambda: plataforma.instalar_sistema(itens)))

    def test_notificacao_por_sistema(self):
        mac = self._com(self._em("Darwin", "arm64"), lambda: plataforma.comando_notificacao("t", "s", "x"))
        self.assertEqual(mac[0], "osascript")
        with mock.patch.object(plataforma.shutil, "which", side_effect=lambda n: "C:/ps.exe" if n == "powershell" else None):
            win = self._com(self._em("Windows"), lambda: plataforma.comando_notificacao("pronto", "16", "it's ok"))
        self.assertEqual(win[0], "C:/ps.exe")
        self.assertIn("ToastNotification", win[-1])
        self.assertIn("'it''s ok'", win[-1].replace("16 · ", ""))   # aspas escapadas no PowerShell

    def test_setup_no_windows_nao_manda_comando_de_unix(self):
        def carregar():
            import setup
            return importlib.reload(setup)
        s = self._com(self._em("Windows"), carregar)
        try:
            self.assertIn("winget", s.BREW)
            self.assertNotIn("ln -s", s.RENDER)
            self.assertNotIn("export", s.ENV)
        finally:
            import setup
            importlib.reload(setup)      # devolve o módulo da máquina real para os outros testes


class TestWindowsNaoQuebraPorAcento(unittest.TestCase):
    PASTAS = ("skills/beditor/scripts", "painel", "skills/motion-vox")

    def test_todo_io_de_texto_declara_utf8(self):
        raiz = SCRIPTS.parents[2]
        culpados = []
        for d in self.PASTAS:
            for p in (raiz / d).rglob("*.py"):
                if "tests" in p.parts:
                    continue
                for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                    if not isinstance(n, ast.Call):
                        continue
                    kws = {k.arg for k in n.keywords}
                    if None in kws:
                        continue
                    nome = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
                    ruim = nome in ("read_text", "write_text") and "encoding" not in kws
                    if nome == "open" and isinstance(n.func, ast.Name) and "encoding" not in kws:
                        modo = (n.args[1].value if len(n.args) > 1 and isinstance(n.args[1], ast.Constant)
                                else "r")
                        ruim = "b" not in str(modo)
                    if (nome in ("run", "check_output", "Popen") and "encoding" not in kws
                            and kws & {"text", "universal_newlines"}):
                        ruim = True
                    if ruim:
                        culpados.append(f"{p.relative_to(raiz)}:{n.lineno} {nome}")
        self.assertEqual(culpados, [], "texto sem encoding (quebra no Windows):\n" + "\n".join(culpados))

    def test_todo_ponto_de_entrada_poe_o_console_em_utf8(self):
        faltam = []
        for p in sorted(SCRIPTS.glob("*.py")):
            fonte = p.read_text(encoding="utf-8")
            if p.name == "plataforma.py" or "__main__" not in fonte:
                continue
            if "import plataforma" not in fonte:
                faltam.append(p.name)
        self.assertEqual(faltam, [], "script sem `import plataforma` no ponto de entrada:\n" + "\n".join(faltam))


if __name__ == "__main__":
    unittest.main()
