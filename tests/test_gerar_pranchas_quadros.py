"""Testes de scripts/gerar_pranchas_quadros.py com vídeos sintéticos (ffmpeg lavfi).

Funcionam com ``python3 -m unittest`` e com ``pytest``. Os testes que precisam de
ffmpeg/ffprobe são pulados quando as ferramentas não estão no PATH. Não usam
rede nem git.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import math
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "plugin"
CAMINHO_SCRIPT = RAIZ / "scripts" / "gerar_pranchas_quadros.py"

_spec = importlib.util.spec_from_file_location("gerar_pranchas_quadros", CAMINHO_SCRIPT)
pranchas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pranchas)

TEM_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
LARGURA_TESTE = 64


def criar_video(destino, quadros, fps=10, tamanho="160x120"):
    """Cria um vídeo sintético com exatamente ``quadros`` quadros (testsrc)."""
    comando = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-f", "lavfi", "-i", f"testsrc=size={tamanho}:rate={fps}",
        "-frames:v", str(quadros),
        "-c:v", "mpeg4", "-pix_fmt", "yuv420p",
        str(destino),
    ]
    subprocess.run(comando, check=True, stdin=subprocess.DEVNULL)
    return destino


def executar_main(argumentos):
    """Roda main() capturando stdout/stderr; devolve (código, stdout, stderr)."""
    saida, erro = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
        codigo = pranchas.main([str(a) for a in argumentos])
    return codigo, saida.getvalue(), erro.getvalue()


class TestFuncoesPuras(unittest.TestCase):
    def test_caixa_mantem_proporcao_e_usa_tamanhos_pares(self):
        info = {"largura": 160, "altura": 120, "rotacao_graus": 0}
        self.assertEqual(pranchas.calcular_caixa(info, 64), (64, 48))

    def test_caixa_troca_eixos_quando_ha_rotacao_de_90_graus(self):
        info = {"largura": 160, "altura": 120, "rotacao_graus": 90}
        # 64 * 160 / 120 = 85,33 -> 85 -> arredondado para o par 86
        self.assertEqual(pranchas.calcular_caixa(info, 64), (64, 86))

    def test_caixa_respeita_largura_minima(self):
        info = {"largura": 100, "altura": 100, "rotacao_graus": 0}
        largura, _ = pranchas.calcular_caixa(info, 2)
        self.assertEqual(largura, pranchas.LARGURA_MINIMA)

    def test_comando_usa_grade_5x5_passthrough_e_nao_sobrescreve(self):
        comando = pranchas.construir_comando_ffmpeg(
            "entrada.mp4", "destino", 0, (64, 48)
        )
        filtro = comando[comando.index("-vf") + 1]
        self.assertIn("tile=5x5", filtro)
        self.assertLess(filtro.index("showinfo"), filtro.index("tile="))
        self.assertIn("-n", comando)
        self.assertEqual(comando[comando.index("-fps_mode") + 1], "passthrough")
        self.assertTrue(comando[-1].endswith("prancha_%04d.png"))

    def test_comando_aceita_opcao_vsync_para_ffmpeg_antigo(self):
        comando = pranchas.construir_comando_ffmpeg(
            "entrada.mp4", "destino", 0, (64, 48), opcao_sincronia="vsync"
        )
        self.assertEqual(comando[comando.index("-vsync") + 1], "passthrough")
        self.assertNotIn("-fps_mode", comando)

    def test_inteiro_positivo_trata_na_e_zero_como_indisponivel(self):
        for valor in ("N/A", None, "", "0", "-3", "abc"):
            self.assertIsNone(pranchas._inteiro_positivo(valor), valor)
        self.assertEqual(pranchas._inteiro_positivo("60"), 60)

    def test_aviso_diz_que_nao_ha_garantia_de_analise_semantica(self):
        self.assertIn("não garantem análise semântica", pranchas.AVISO_SEMANTICA)


class TestErrosDeUso(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_video_inexistente_retorna_2_e_nao_cria_pasta(self):
        destino = self.tmp / "saida"
        codigo, _, erro = executar_main([self.tmp / "nao_existe.mp4", "--saida", destino])
        self.assertEqual(codigo, pranchas.EXIT_USO)
        self.assertIn("vídeo não encontrado", erro)
        self.assertFalse(destino.exists())

    def test_pasta_existente_e_recusada_sem_tocar_no_conteudo(self):
        video = self.tmp / "video.mp4"
        video.write_bytes(b"conteudo qualquer")  # a checagem do destino vem antes da sondagem
        destino = self.tmp / "ja_existe"
        destino.mkdir()
        sentinela = destino / "sentinela.txt"
        sentinela.write_text("intacto", encoding="utf-8")

        codigo, _, erro = executar_main([video, "--saida", destino])

        self.assertEqual(codigo, pranchas.EXIT_USO)
        self.assertIn("não será sobrescrita", erro)
        self.assertEqual(sentinela.read_text(encoding="utf-8"), "intacto")
        self.assertEqual([p.name for p in destino.iterdir()], ["sentinela.txt"])

    def test_ferramenta_ausente_retorna_erro_claro(self):
        video = self.tmp / "video.mp4"
        video.write_bytes(b"x")
        destino = self.tmp / "saida"
        codigo, _, erro = executar_main(
            [video, "--saida", destino, "--ffmpeg", "ffmpeg-que-nao-existe"]
        )
        self.assertEqual(codigo, pranchas.EXIT_ERRO)
        self.assertIn("ferramenta não encontrada", erro)
        self.assertFalse(destino.exists())

    def test_largura_abaixo_do_minimo_retorna_2(self):
        video = self.tmp / "video.mp4"
        video.write_bytes(b"x")
        codigo, _, erro = executar_main([video, "--saida", self.tmp / "s", "--largura", "4"])
        self.assertEqual(codigo, pranchas.EXIT_USO)
        self.assertIn("--largura", erro)


@unittest.skipUnless(TEM_FFMPEG, "ffmpeg/ffprobe não estão disponíveis no PATH")
class TestComVideoSintetico(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def gerar(self, quadros, nome="video.mp4", **extra):
        video = criar_video(self.tmp / nome, quadros)
        destino = self.tmp / f"pranchas_{nome}"
        manifesto = pranchas.gerar_pranchas(video, destino, largura=LARGURA_TESTE, **extra)
        return video, destino, manifesto

    def test_60_quadros_geram_3_pranchas_sem_pular_nenhum(self):
        _, destino, manifesto = self.gerar(60)

        self.assertEqual(manifesto["status"], "ok")
        self.assertEqual(manifesto["quadros"]["processados"], 60)
        self.assertEqual(manifesto["quadros"]["esperados"], 60)
        self.assertEqual(manifesto["quadros"]["conferencia"], "confere")

        arquivos = sorted(p.name for p in destino.glob("prancha_*.png"))
        self.assertEqual(arquivos, ["prancha_0001.png", "prancha_0002.png", "prancha_0003.png"])

        intervalos = [
            (p["quadro_inicial"], p["quadro_final"], p["quadros_na_prancha"])
            for p in manifesto["pranchas"]
        ]
        self.assertEqual(intervalos, [(0, 24, 25), (25, 49, 25), (50, 59, 10)])
        # Os intervalos cobrem todos os quadros, sem buracos nem sobreposição.
        self.assertEqual(sum(i[2] for i in intervalos), 60)

    def test_limites_da_prancha_25_e_26_quadros(self):
        for quadros, esperadas in ((25, 1), (26, 2)):
            with self.subTest(quadros=quadros):
                _, destino, manifesto = self.gerar(quadros, nome=f"v{quadros}.mp4")
                self.assertEqual(manifesto["quadros"]["processados"], quadros)
                self.assertEqual(len(list(destino.glob("prancha_*.png"))), esperadas)
                self.assertEqual(len(manifesto["pranchas"]), math.ceil(quadros / 25))
                self.assertEqual(manifesto["pranchas"][-1]["quadro_final"], quadros - 1)

    def test_prancha_tem_resolucao_reduzida_de_grade_5x5(self):
        _, destino, manifesto = self.gerar(25)
        info = pranchas.sondar_video(destino / "prancha_0001.png")
        celula = (manifesto["configuracao"]["largura_celula"], manifesto["configuracao"]["altura_celula"])
        self.assertEqual(celula, (LARGURA_TESTE, 48))
        # A grade tem 5 colunas/linhas de células, mais espaçamento e margem.
        self.assertGreaterEqual(info["largura"], 5 * celula[0])
        self.assertLess(info["largura"], 5 * celula[0] + 40)
        self.assertGreaterEqual(info["altura"], 5 * celula[1])
        self.assertLess(info["altura"], 5 * celula[1] + 40)
        self.assertLess(info["largura"], 5 * 160)  # menor que o vídeo original em grade

    def test_manifesto_e_gravado_com_aviso_e_campos_principais(self):
        _, destino, manifesto = self.gerar(30)
        em_disco = json.loads((destino / "manifesto.json").read_text(encoding="utf-8"))
        self.assertEqual(em_disco["quadros"], manifesto["quadros"])
        self.assertIn("não garantem análise semântica", em_disco["aviso"])
        self.assertEqual(em_disco["configuracao"]["quadros_por_prancha"], 25)
        self.assertEqual(em_disco["video"]["nome"], "video.mp4")
        self.assertIn("passthrough", em_disco["configuracao"]["modo_quadros"])

    def test_pasta_nova_nao_sobrescreve_execucao_anterior(self):
        video, destino, _ = self.gerar(30)
        antes = {p.name: p.stat().st_mtime_ns for p in destino.iterdir()}
        codigo, _, erro = executar_main([video, "--saida", destino, "--largura", LARGURA_TESTE])
        self.assertEqual(codigo, pranchas.EXIT_USO)
        self.assertIn("não será sobrescrita", erro)
        depois = {p.name: p.stat().st_mtime_ns for p in destino.iterdir()}
        self.assertEqual(antes, depois)

    def test_sem_total_declarado_conferencia_e_sem_referencia_ou_confere(self):
        # Em Matroska o ffprobe normalmente não informa nb_frames.
        video = self.tmp / "video.mkv"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-f", "lavfi", "-i", "testsrc=size=160x120:rate=10",
                "-frames:v", "30", "-c:v", "mpeg4", "-pix_fmt", "yuv420p", str(video),
            ],
            check=True,
            stdin=subprocess.DEVNULL,
        )
        manifesto = pranchas.gerar_pranchas(
            video, self.tmp / "saida_mkv", largura=LARGURA_TESTE
        )
        self.assertEqual(manifesto["quadros"]["processados"], 30)
        self.assertIn(manifesto["quadros"]["esperados"], (None, 30))
        if manifesto["quadros"]["esperados"] is None:
            self.assertEqual(manifesto["quadros"]["conferencia"], "sem_referencia")
            self.assertIsNone(manifesto["quadros"]["fonte_esperados"])
        else:
            self.assertEqual(manifesto["quadros"]["conferencia"], "confere")

    def test_contar_quadros_fornece_contagem_independente(self):
        _, _, manifesto = self.gerar(60, contar_quadros=True)
        self.assertEqual(manifesto["quadros"]["contados_ffprobe"], 60)
        self.assertEqual(manifesto["quadros"]["processados"], 60)
        self.assertEqual(manifesto["quadros"]["esperados"], 60)

    def test_cli_retorna_0_e_imprime_aviso(self):
        video = criar_video(self.tmp / "cli.mp4", 40)
        destino = self.tmp / "saida_cli"
        codigo, saida, _ = executar_main([video, "--saida", destino, "--largura", LARGURA_TESTE])
        self.assertEqual(codigo, pranchas.EXIT_OK)
        self.assertIn("Quadros esperados: 40", saida)
        self.assertIn("processados: 40", saida)
        self.assertIn("análise semântica", saida)
        self.assertEqual(len(list(destino.glob("prancha_*.png"))), 2)

    def test_arquivo_que_nao_e_video_retorna_erro_sem_travar(self):
        falso = self.tmp / "falso.mp4"
        falso.write_text("isto não é um vídeo", encoding="utf-8")
        destino = self.tmp / "saida_falso"
        codigo, _, erro = executar_main([falso, "--saida", destino])
        self.assertEqual(codigo, pranchas.EXIT_ERRO)
        self.assertIn("ffprobe", erro)
        self.assertFalse(destino.exists())  # falhou antes de criar a pasta


if __name__ == "__main__":
    unittest.main()
