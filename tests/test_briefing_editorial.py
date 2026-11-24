"""Testes de scripts/briefing_editorial.py. Só biblioteca padrão.

Rodar a partir da raiz do projeto:
    python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "plugin"
sys.path.insert(0, str(RAIZ / "scripts"))

import briefing_editorial as be  # noqa: E402
from briefing_editorial import BriefingInvalido  # noqa: E402

BRIEFING_VALIDO = {
    "titulo": "Por que a memória não é um arquivo",
    "formato_sofia": "Análise",
    "estrutura_roteiro": "Gancho, prova, virada, fechamento",
    "editor": "capcut",
    "objetivo": "Explicar a memória sem jargão",
}


class _ComPasta(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.pasta = Path(temp.name)

    def caminho(self, nome):
        return self.pasta / nome


class SalvarECarregar(_ComPasta):
    def test_round_trip_sem_estilo(self):
        destino = be.salvar_briefing(BRIEFING_VALIDO, self.caminho("b.json"))
        self.assertEqual(be.carregar_briefing(destino), BRIEFING_VALIDO)

    def test_preserva_acentos_sem_escape_unicode(self):
        destino = be.salvar_briefing(BRIEFING_VALIDO, self.caminho("b.json"))
        texto = destino.read_text(encoding="utf-8")
        self.assertIn("não", texto)
        self.assertIn("Análise", texto)
        self.assertNotIn("\\u", texto)
        self.assertEqual(json.loads(texto), BRIEFING_VALIDO)

    def test_estilo_opcional_e_gravado_quando_informado(self):
        dados = dict(BRIEFING_VALIDO, estilo="Documentário sóbrio")
        destino = be.salvar_briefing(dados, self.caminho("b.json"))
        self.assertEqual(be.carregar_briefing(destino)["estilo"], "Documentário sóbrio")

    def test_estilo_null_nao_aparece_no_arquivo(self):
        destino = be.salvar_briefing(dict(BRIEFING_VALIDO, estilo=None), self.caminho("b.json"))
        self.assertNotIn("estilo", json.loads(destino.read_text(encoding="utf-8")))

    def test_editor_davinci(self):
        destino = be.salvar_briefing(dict(BRIEFING_VALIDO, editor="davinci"), self.caminho("b.json"))
        self.assertEqual(be.carregar_briefing(destino)["editor"], "davinci")

    def test_normaliza_acento_decomposto_para_nfc(self):
        # "não" com o til como caractere combinante (NFD) vira a forma composta (NFC).
        dados = dict(BRIEFING_VALIDO, titulo="n" + "ã" + "o")
        destino = be.salvar_briefing(dados, self.caminho("b.json"))
        self.assertEqual(be.carregar_briefing(destino)["titulo"], "não")

    def test_cria_pasta_pai(self):
        destino = be.salvar_briefing(BRIEFING_VALIDO, self.caminho("sub/dir/b.json"))
        self.assertTrue(destino.exists())

    def test_nao_sobrescreve(self):
        destino = be.salvar_briefing(BRIEFING_VALIDO, self.caminho("b.json"))
        antes = destino.read_bytes()
        with self.assertRaises(FileExistsError):
            be.salvar_briefing(dict(BRIEFING_VALIDO, titulo="Outro título"), destino)
        self.assertEqual(destino.read_bytes(), antes)

    def test_nao_cria_arquivo_quando_invalido(self):
        destino = self.caminho("b.json")
        with self.assertRaises(BriefingInvalido):
            be.salvar_briefing({"titulo": "Só título"}, destino)
        self.assertFalse(destino.exists())


class Validacao(unittest.TestCase):
    def test_rejeita_campo_obrigatorio_ausente(self):
        for campo in ("titulo", "formato_sofia", "estrutura_roteiro", "editor", "objetivo"):
            with self.subTest(campo=campo):
                dados = dict(BRIEFING_VALIDO)
                del dados[campo]
                with self.assertRaises(BriefingInvalido) as cm:
                    be.validar_briefing(dados)
                self.assertIn(campo, str(cm.exception))

    def test_rejeita_campo_obrigatorio_nulo(self):
        for campo in ("titulo", "formato_sofia", "estrutura_roteiro", "editor", "objetivo"):
            with self.subTest(campo=campo):
                with self.assertRaises(BriefingInvalido) as cm:
                    be.validar_briefing(dict(BRIEFING_VALIDO, **{campo: None}))
                self.assertIn(campo, str(cm.exception))

    def test_rejeita_texto_vazio_ou_so_espacos(self):
        for campo in ("titulo", "formato_sofia", "estrutura_roteiro", "objetivo", "estilo"):
            with self.subTest(campo=campo):
                with self.assertRaises(BriefingInvalido) as cm:
                    be.validar_briefing(dict(BRIEFING_VALIDO, **{campo: "   "}))
                self.assertIn("não pode ser vazio", str(cm.exception))

    def test_rejeita_editor_invalido(self):
        with self.assertRaises(BriefingInvalido) as cm:
            be.validar_briefing(dict(BRIEFING_VALIDO, editor="premiere"))
        self.assertIn("capcut", str(cm.exception))
        self.assertIn("davinci", str(cm.exception))

    def test_editor_aceita_maiusculas_e_normaliza(self):
        dados = be.validar_briefing(dict(BRIEFING_VALIDO, editor="CapCut"))
        self.assertEqual(dados["editor"], "capcut")

    def test_rejeita_campo_desconhecido(self):
        dados = dict(BRIEFING_VALIDO)
        dados["formato"] = dados.pop("formato_sofia")
        with self.assertRaises(BriefingInvalido) as cm:
            be.validar_briefing(dados)
        self.assertIn("formato", str(cm.exception))

    def test_rejeita_tipo_errado(self):
        with self.assertRaises(BriefingInvalido):
            be.validar_briefing(dict(BRIEFING_VALIDO, titulo=123))

    def test_rejeita_que_nao_e_objeto(self):
        with self.assertRaises(BriefingInvalido):
            be.validar_briefing(["titulo", "formato_sofia"])

    def test_rejeita_json_invalido_no_arquivo(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        arquivo = Path(pasta.name) / "quebrado.json"
        arquivo.write_text("{não é json", encoding="utf-8")
        with self.assertRaises(BriefingInvalido):
            be.carregar_briefing(arquivo)


class Alterar(_ComPasta):
    def setUp(self):
        super().setUp()
        self.origem = be.salvar_briefing(BRIEFING_VALIDO, self.caminho("origem.json"))

    def test_grava_em_arquivo_novo_e_nao_mexe_no_original(self):
        antes = self.origem.read_bytes()
        destino = self.caminho("v2.json")
        resultado = be.alterar_briefing(
            self.origem, destino, {"editor": "davinci", "titulo": "Título revisado"}
        )
        self.assertEqual(self.origem.read_bytes(), antes)
        esperado = dict(BRIEFING_VALIDO, editor="davinci", titulo="Título revisado")
        self.assertEqual(be.carregar_briefing(destino), esperado)
        self.assertEqual(resultado, esperado)

    def test_recusa_destino_existente(self):
        outro = be.salvar_briefing(dict(BRIEFING_VALIDO, titulo="Outro"), self.caminho("outro.json"))
        antes = outro.read_bytes()
        with self.assertRaises(FileExistsError):
            be.alterar_briefing(self.origem, outro, {"editor": "davinci"})
        self.assertEqual(outro.read_bytes(), antes)

    def test_recusa_gravar_sobre_a_propria_origem(self):
        antes = self.origem.read_bytes()
        with self.assertRaises(FileExistsError):
            be.alterar_briefing(self.origem, self.origem, {"editor": "davinci"})
        self.assertEqual(self.origem.read_bytes(), antes)

    def test_alteracao_invalida_nao_cria_arquivo(self):
        destino = self.caminho("v2.json")
        with self.assertRaises(BriefingInvalido):
            be.alterar_briefing(self.origem, destino, {"editor": "premiere"})
        self.assertFalse(destino.exists())

    def test_campo_obrigatorio_nao_pode_ser_removido(self):
        destino = self.caminho("v2.json")
        with self.assertRaises(BriefingInvalido) as cm:
            be.alterar_briefing(self.origem, destino, {"objetivo": None})
        self.assertIn("objetivo", str(cm.exception))
        self.assertFalse(destino.exists())

    def test_remove_estilo_com_null(self):
        origem = be.salvar_briefing(
            dict(BRIEFING_VALIDO, estilo="Cinematográfico"), self.caminho("com-estilo.json")
        )
        destino = self.caminho("sem-estilo.json")
        be.alterar_briefing(origem, destino, {"estilo": None})
        self.assertNotIn("estilo", be.carregar_briefing(destino))

    def test_sem_alteracoes_e_rejeitado(self):
        with self.assertRaises(BriefingInvalido):
            be.alterar_briefing(self.origem, self.caminho("v2.json"), {})


class LinhaDeComando(_ComPasta):
    def rodar(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            codigo = be.main(argv)
        return codigo, out.getvalue(), err.getvalue()

    def argv_criar(self, saida, *, sem=None):
        pares = [
            ("--titulo", BRIEFING_VALIDO["titulo"]),
            ("--formato-sofia", BRIEFING_VALIDO["formato_sofia"]),
            ("--estrutura-roteiro", BRIEFING_VALIDO["estrutura_roteiro"]),
            ("--editor", BRIEFING_VALIDO["editor"]),
            ("--objetivo", BRIEFING_VALIDO["objetivo"]),
        ]
        argv = ["criar"]
        for flag, valor in pares:
            if flag != sem:
                argv += [flag, valor]
        return argv + ["--saida", str(saida)]

    def test_criar_com_campos_validos(self):
        destino = self.caminho("b.json")
        codigo, out, _ = self.rodar(self.argv_criar(destino))
        self.assertEqual(codigo, 0)
        self.assertIn("criado", out)
        self.assertEqual(be.carregar_briefing(destino), BRIEFING_VALIDO)

    def test_criar_sem_campo_obrigatorio_falha_e_nao_cria(self):
        destino = self.caminho("b.json")
        codigo, _, err = self.rodar(self.argv_criar(destino, sem="--objetivo"))
        self.assertEqual(codigo, 1)
        self.assertIn("objetivo", err)
        self.assertFalse(destino.exists())

    def test_criar_nao_sobrescreve(self):
        destino = self.caminho("b.json")
        self.rodar(self.argv_criar(destino))
        antes = destino.read_bytes()
        codigo, _, err = self.rodar(self.argv_criar(destino))
        self.assertEqual(codigo, 1)
        self.assertIn("já existe", err)
        self.assertEqual(destino.read_bytes(), antes)

    def test_validar(self):
        destino = self.caminho("b.json")
        self.rodar(self.argv_criar(destino))
        codigo, out, _ = self.rodar(["validar", str(destino)])
        self.assertEqual(codigo, 0)
        self.assertIn("válido", out)

    def test_alterar_cli_grava_novo_arquivo(self):
        origem = self.caminho("origem.json")
        self.rodar(self.argv_criar(origem))
        antes = origem.read_bytes()
        destino = self.caminho("v2.json")
        codigo, _, _ = self.rodar(["alterar", str(origem), "--editor", "davinci", "--saida", str(destino)])
        self.assertEqual(codigo, 0)
        self.assertEqual(origem.read_bytes(), antes)
        self.assertEqual(be.carregar_briefing(destino)["editor"], "davinci")

    def test_alterar_cli_editor_invalido_falha(self):
        origem = self.caminho("origem.json")
        self.rodar(self.argv_criar(origem))
        destino = self.caminho("v2.json")
        codigo, _, err = self.rodar(["alterar", str(origem), "--editor", "premiere", "--saida", str(destino)])
        self.assertEqual(codigo, 1)
        self.assertIn("editor", err)
        self.assertFalse(destino.exists())

    def test_alterar_cli_sem_estilo(self):
        com_estilo = be.salvar_briefing(dict(BRIEFING_VALIDO, estilo="Sóbrio"), self.caminho("com.json"))
        destino = self.caminho("sem.json")
        codigo, _, _ = self.rodar(["alterar", str(com_estilo), "--sem-estilo", "--saida", str(destino)])
        self.assertEqual(codigo, 0)
        self.assertNotIn("estilo", be.carregar_briefing(destino))

    def test_sem_estilo_nao_combina_com_estilo(self):
        origem = self.caminho("origem.json")
        self.rodar(self.argv_criar(origem))
        with self.assertRaises(SystemExit):
            self.rodar(["alterar", str(origem), "--sem-estilo", "--estilo", "X", "--saida", str(self.caminho("v2.json"))])


if __name__ == "__main__":
    unittest.main()
