"""O setup tem de funcionar numa máquina crua e nunca mexer na configuração real.

Estes testes trancam quatro coisas: `verificar()` descreve uma máquina sem nada
(com `which` e `find_spec` simulados) na estrutura que o manual lê; `--pastas`
grava e MESCLA num config apontado por `BEDITOR_CONFIG` (rodar de novo com uma
pasta só não apaga as outras); `--manual` troca o marcador pelo JSON e o marcador
não sobra; e o template, com `{}` no lugar do JSON, ainda é um HTML íntegro.
"""
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import oficina  # noqa: E402
import setup  # noqa: E402


class _Ambiente(unittest.TestCase):
    """um HOME e um BEDITOR_CONFIG descartáveis, para nada tocar a máquina real"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        self.config = self.raiz / "config.json"
        self._env = {k: os.environ.get(k) for k in ("BEDITOR_CONFIG", "GEMINI_API_KEY")}
        os.environ["BEDITOR_CONFIG"] = str(self.config)
        os.environ.pop("GEMINI_API_KEY", None)

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()


class TestVerificar(_Ambiente):
    def test_maquina_crua_devolve_a_estrutura_que_o_manual_le(self):
        v = setup.verificar(which=lambda b: None, tem_modulo=lambda m: False,
                            home=self.raiz, conferir_dataless=False)
        self.assertEqual(set(v), {"quando", "sistema", "itens", "pastas", "resumo", "config"})
        por_id = {i["id"]: i for i in v["itens"]}
        for i in v["itens"]:
            self.assertIn(i["estado"], ("ok", "falta", "opcional"))
            self.assertEqual(set(i), {"id", "nome", "estado", "detalhe", "instalar", "grupo"})
        # o que é obrigatório falta; o que é opcional é dito como opcional
        self.assertEqual(por_id["ffmpeg"]["estado"], "falta")
        self.assertIn("brew install", por_id["ffmpeg"]["instalar"])
        self.assertEqual(por_id["node"]["estado"], "opcional")
        self.assertEqual(por_id["py-PIL"]["estado"], "falta")
        self.assertIn("pip3 install", por_id["py-PIL"]["instalar"])
        self.assertEqual(por_id["py-whisper"]["estado"], "falta")
        self.assertEqual(por_id["render"]["estado"], "falta")
        # a chave nunca aparece: só presente/ausente
        self.assertEqual(por_id["gemini"]["estado"], "opcional")
        self.assertNotIn("=", por_id["gemini"]["detalhe"])
        # pastas: as oito, nenhuma configurada
        self.assertEqual([p["nome"] for p in v["pastas"]], list(oficina.PASTAS))
        self.assertFalse(any(p["configurada"] for p in v["pastas"]))
        self.assertEqual(v["resumo"]["pastas_configuradas"], 0)
        self.assertEqual(v["resumo"]["falta"], sum(1 for i in v["itens"] if i["estado"] == "falta"))

    def test_maquina_completa_fica_ok_e_ve_a_chave_sem_mostrar(self):
        (self.raiz / ".beditor" / "bin").mkdir(parents=True)
        for b in ("recorte", "rastrear-rosto"):
            p = self.raiz / ".beditor" / "bin" / b
            p.write_text("#!/bin/sh\n")
            p.chmod(0o755)
        (self.raiz / ".beditor" / "render").mkdir()
        env = self.raiz / ".config" / "beditor" / "env"
        env.parent.mkdir(parents=True)
        env.write_text("export GEMINI_API_KEY=segredo-que-nao-pode-sair\n")
        v = setup.verificar(which=lambda b: f"/opt/bin/{b}", tem_modulo=lambda m: True,
                            home=self.raiz, conferir_dataless=False)
        por_id = {i["id"]: i for i in v["itens"]}
        for id_ in ("ffmpeg", "ffprobe", "yt-dlp", "node", "py-PIL", "py-cv2", "py-whisper",
                    "render", "gemini", "bin-recorte", "fontes"):
            self.assertEqual(por_id[id_]["estado"], "ok", id_)
        self.assertIn("mlx-whisper", por_id["py-whisper"]["detalhe"])
        self.assertNotIn("segredo", json.dumps(v))

    def _registrar_plugin(self, chave, versao):
        p = self.raiz / ".claude" / "plugins"
        p.mkdir(parents=True, exist_ok=True)
        (p / "installed_plugins.json").write_text(json.dumps(
            {"version": 2, "plugins": {chave: [{"version": versao}]}}), encoding="utf-8")

    def test_context_mode_ausente_vira_falta_com_o_comando_de_instalar(self):
        v = setup.verificar(which=lambda b: None, tem_modulo=lambda m: False,
                            home=self.raiz, conferir_dataless=False)
        i = {x["id"]: x for x in v["itens"]}["context-mode"]
        self.assertEqual(i["estado"], "falta")
        self.assertIn("claude plugin install context-mode@context-mode", i["instalar"])
        self.assertIn(i["instalar"], setup.comandos_instalacao(v))

    def test_context_mode_instalado_aparece_com_a_versao(self):
        self._registrar_plugin("context-mode@context-mode", "1.0.169")
        v = setup.verificar(which=lambda b: None, tem_modulo=lambda m: False,
                            home=self.raiz, conferir_dataless=False)
        i = {x["id"]: x for x in v["itens"]}["context-mode"]
        self.assertEqual(i["estado"], "ok")
        self.assertIn("1.0.169", i["detalhe"])
        self.assertEqual(i["instalar"], "")

    def test_registro_de_plugins_quebrado_nao_derruba_o_setup(self):
        p = self.raiz / ".claude" / "plugins"
        p.mkdir(parents=True)
        (p / "installed_plugins.json").write_text("{isto não é json")
        self.assertIsNone(setup._plugin_claude("context-mode", self.raiz))

    def test_atualizar_so_imprime_sem_sim(self):
        (self.raiz / ".git").mkdir()
        cmds = setup.atualizar(executar=False, raiz=self.raiz)
        self.assertTrue(any("pull --ff-only" in c for c in cmds))
        self.assertTrue(any("plugin update context-mode" in c for c in cmds))

    def test_clone_do_repositorio_com_o_plugin_em_subpasta_atualiza_pelo_git(self):
        # No repositório da Sofia o plugin mora em plugin/; o .git fica na pasta de cima.
        (self.raiz / ".git").mkdir()
        (self.raiz / "plugin").mkdir()
        cmds = setup.atualizar(executar=False, raiz=self.raiz / "plugin", home=self.raiz)
        self.assertEqual(cmds[0], f"git -C '{self.raiz}' pull --ff-only")

    def test_instalado_pelo_marketplace_atualiza_pelo_claude_e_nao_pelo_git(self):
        cmds = setup.atualizar(executar=False, raiz=self.raiz, home=self.raiz)   # sem .git
        # O catálogo antes do plugin: sem ele, o update não vê a versão nova.
        self.assertEqual(cmds[:2], ["claude plugin marketplace update criadores-do-futuro",
                                    "claude plugin update sofia-estrategista@criadores-do-futuro"])
        self.assertFalse(any("git" in c for c in cmds))

    def _instalado_por(self, marketplace, nome="sofia-estrategista"):
        p = self.raiz / ".claude" / "plugins"
        p.mkdir(parents=True)
        (p / "installed_plugins.json").write_text(json.dumps(
            {"plugins": {f"{nome}@{marketplace}": [{"version": "0.3.0"}]}}))

    def _atualizar_e_ler_o_aviso(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            cmds = setup.atualizar(executar=False, raiz=self.raiz, home=self.raiz)
        return cmds, saida.getvalue()

    def test_marketplace_criadores_do_futuro_atualiza_por_ele_mesmo(self):
        self._instalado_por("criadores-do-futuro")
        cmds, aviso = self._atualizar_e_ler_o_aviso()
        self.assertEqual(cmds[:2], ["claude plugin marketplace update criadores-do-futuro",
                                    "claude plugin update sofia-estrategista@criadores-do-futuro"])
        self.assertNotIn("aviso:", aviso)

    def test_outro_marketplace_avisa_com_o_prompt_de_migracao_e_nao_tenta_atualizar_a_sofia(self):
        self._instalado_por("sofia-plugins")
        cmds, aviso = self._atualizar_e_ler_o_aviso()
        self.assertFalse(any("sofia-estrategista" in c for c in cmds))
        self.assertIn("plugin update context-mode", cmds[-1])
        self.assertIn("prompt de migração", aviso)
        self.assertEqual(setup._plugin_claude("sofia-estrategista", self.raiz), "0.3.0")

    def test_sofia_de_nome_antigo_avisa_com_o_prompt_de_migracao(self):
        self._instalado_por("sofia-editora", nome="sofia-estrategista-editora")
        cmds, aviso = self._atualizar_e_ler_o_aviso()
        self.assertIn("sofia-estrategista-editora", aviso)
        self.assertIn("prompt de migração", aviso)
        self.assertFalse(any("sofia-estrategista-editora" in c for c in cmds))
        self.assertIn("plugin update context-mode", cmds[-1])

    def test_chave_vazia_ou_placeholder_conta_como_ausente(self):
        env = self.raiz / "env"
        env.write_text("export GEMINI_API_KEY=\n")
        self.assertFalse(setup._chave_gemini_presente(env)[0])
        env.write_text("export GEMINI_API_KEY=<sua chave>\n")
        self.assertFalse(setup._chave_gemini_presente(env)[0])
        env.write_text("GEMINI_API_KEY='abc'\n")
        self.assertTrue(setup._chave_gemini_presente(env)[0])

    def test_render_com_acento_e_apontado(self):
        (self.raiz / ".beditor").mkdir()
        alvo = self.raiz / "Criação"
        alvo.mkdir()
        (self.raiz / ".beditor" / "render").symlink_to(alvo)
        v = setup.verificar(which=lambda b: None, tem_modulo=lambda m: False,
                            home=self.raiz, conferir_dataless=False)
        render = next(i for i in v["itens"] if i["id"] == "render")
        self.assertEqual(render["estado"], "falta")
        self.assertIn("acento", render["detalhe"])

    def test_pasta_configurada_e_medida(self):
        proj = self.raiz / "Projetos"
        proj.mkdir()
        self.config.write_text(json.dumps({"versao": 1, "pastas": {"projetos": str(proj)}}))
        v = setup.verificar(which=lambda b: None, tem_modulo=lambda m: False,
                            home=self.raiz, conferir_dataless=False)
        p = next(x for x in v["pastas"] if x["nome"] == "projetos")
        self.assertTrue(p["configurada"] and p["existe"])
        self.assertIsInstance(p["livre_gb"], float)
        self.assertEqual(v["resumo"]["pastas_existem"], 1)

    def test_comandos_de_instalacao_nao_repetem(self):
        v = setup.verificar(which=lambda b: None, tem_modulo=lambda m: False,
                            home=self.raiz, conferir_dataless=False)
        cmds = setup.comandos_instalacao(v)
        self.assertEqual(len(cmds), len(set(cmds)))
        self.assertTrue(any("brew install" in c for c in cmds))
        self.assertTrue(any("pip3 install" in c for c in cmds))


class TestPastas(_Ambiente):
    def test_grava_e_mescla_sem_apagar_o_que_ja_estava(self):
        a, b = self.raiz / "Projetos", self.raiz / "Entregas"
        setup.gravar_pastas([f"projetos={a}", f"entregas={b}"], criar=True)
        self.assertTrue(a.is_dir() and b.is_dir())
        setup.gravar_pastas([f"musicas={self.raiz / 'Musicas'}"], criar=True,
                            canal=["nome=Canal Teste", "arroba=@teste"])
        cfg = json.loads(self.config.read_text())
        self.assertEqual(cfg["versao"], 1)
        self.assertEqual(cfg["pastas"]["projetos"], str(a))
        self.assertEqual(cfg["pastas"]["entregas"], str(b))
        self.assertEqual(cfg["pastas"]["musicas"], str(self.raiz / "Musicas"))
        self.assertEqual(cfg["canal"], {"nome": "Canal Teste", "arroba": "@teste"})
        self.assertNotIn("_arquivo", cfg)
        # e o oficina lê o mesmo arquivo
        self.assertEqual(oficina.pasta("projetos"), a)

    def test_guarda_o_til_como_o_usuario_digitou(self):
        setup.gravar_pastas(["render=~/.beditor/render"])
        cfg = json.loads(self.config.read_text())
        self.assertEqual(cfg["pastas"]["render"], "~/.beditor/render")

    def test_nome_desconhecido_para(self):
        with self.assertRaises(SystemExit):
            setup.gravar_pastas(["fotos=/tmp"])
        with self.assertRaises(SystemExit):
            setup.gravar_pastas(["projetos="])
        self.assertFalse(self.config.exists())

    def test_pela_linha_de_comando(self):
        setup.main(["--pastas", f"sfx={self.raiz / 'SFX'}", "--criar"])
        self.assertEqual(json.loads(self.config.read_text())["pastas"]["sfx"], str(self.raiz / "SFX"))


class TestManual(_Ambiente):
    def test_template_tem_o_marcador_uma_vez_e_o_esqueleto_de_artifact(self):
        html = setup.TEMPLATE_MANUAL.read_text(encoding="utf-8")
        self.assertEqual(html.count(setup.MARCADOR), 1)
        self.assertTrue(html.startswith("<title>Manual do bEditor</title>"))
        for tag in ("<!doctype", "<!DOCTYPE", "<html", "<head>", "<body"):
            self.assertNotIn(tag, html)
        # todas as abas existem e apenas a primeira está visível ao carregar
        abas = re.findall(r'data-aba="([a-z]+)"', html)
        self.assertEqual(abas, ["comecar", "saude", "fluxos", "comandos", "pastas", "referencias", "glossario"])
        for a in abas:
            self.assertIn(f'id="aba-{a}"', html)
        self.assertEqual(len(re.findall(r'role="tabpanel" id="aba-[a-z]+" hidden', html)), 6)

    def test_gera_o_manual_com_o_json_e_sem_o_marcador(self):
        v = setup.verificar(which=lambda b: None, tem_modulo=lambda m: False,
                            home=self.raiz, conferir_dataless=False)
        dados = setup.dados_do_manual(verificacao=v)
        # o JSON contém algo que, cru, fecharia o <script>
        dados["comandos"].append({"nome": "x", "descricao": "fecha </script> por engano", "argumentos": ""})
        destino = setup.gerar_manual(self.raiz / "manual.html", dados)
        html = destino.read_text(encoding="utf-8")
        self.assertNotIn(setup.MARCADOR, html)
        self.assertNotIn("</script> por engano", html)
        m = re.search(r"var DADOS = (\{.*?\});\n", html, re.S)
        self.assertIsNotNone(m)
        lido = json.loads(m.group(1).replace("<\\/", "</"))
        self.assertEqual(lido["verificacao"]["resumo"], v["resumo"])
        self.assertEqual([c["nome"] for c in lido["comandos"]][:1], [setup.comandos_do_plugin()[0]["nome"]])
        self.assertIn("setup", [c["nome"] for c in lido["comandos"]])
        self.assertTrue(all(r["titulo"] for r in lido["referencias"]))
        self.assertNotIn("_arquivo", lido["config"])

    def test_comandos_e_referencias_saem_do_repo(self):
        cmds = {c["nome"]: c for c in setup.comandos_do_plugin()}
        self.assertIn("editar-analise", cmds)
        self.assertTrue(cmds["editar-analise"]["descricao"].startswith("Edita um vídeo do formato"))
        self.assertEqual(cmds["cortar"]["argumentos"], "<take.mov>")
        refs = {r["arquivo"]: r["titulo"] for r in setup.referencias_do_plugin()}
        self.assertIn("formato-analise.md", refs)
        self.assertTrue(refs["eficiencia.md"].startswith("Eficiência"))

    def test_template_renderiza_com_json_vazio(self):
        """`{}` no lugar do JSON: o JS tem de tratar cada bloco como ausente. Sem
        navegador aqui, o teste confere que cada leitura de DADOS tem `|| {}` ou
        `|| []` e que a dica de preencher existe."""
        html = setup.TEMPLATE_MANUAL.read_text(encoding="utf-8")
        js = html[html.index("<script>"):]
        for acesso in re.findall(r"= DADOS\.(\w+)", js):
            self.assertRegex(js, r"DADOS\.%s \|\| (\{\}|\[\])" % acesso,
                             f"DADOS.{acesso} lido sem valor padrão")
        self.assertIn("setup.py --manual", js)
        # com navegador, a prova de verdade: abrir com `{}` e com dados, sem erro de JS
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright ausente")
        v = setup.verificar(which=lambda b: None, tem_modulo=lambda m: False,
                            home=self.raiz, conferir_dataless=False)
        cheio = setup.gerar_manual(self.raiz / "cheio.html", setup.dados_do_manual(verificacao=v))
        vazio = self.raiz / "vazio.html"
        vazio.write_text(html, encoding="utf-8")
        # Subir o navegador é dependência do ambiente (chromium não baixado, node
        # com NODE_OPTIONS de outra ferramenta): falha aí é `skip`, não erro do
        # manual. O que se afirma fica fora do try, para nunca ser engolido.
        try:
            pw = sync_playwright().start()
            nav = pw.chromium.launch()
        except Exception as e:  # noqa: BLE001
            self.skipTest(f"playwright sem navegador aqui: {str(e).splitlines()[0][:100]}")
        try:
            for arq, esperado in ((vazio, "rode"), (cheio, "ffmpeg")):
                erros = []
                pg = nav.new_page()
                pg.on("pageerror", lambda e: erros.append(str(e)))
                pg.goto(arq.as_uri() + "#saude")
                self.assertEqual(erros, [], arq.name)
                self.assertFalse(pg.eval_on_selector("#aba-saude", "e => e.hidden"))
                self.assertTrue(pg.eval_on_selector("#aba-comecar", "e => e.hidden"))
                self.assertIn(esperado, pg.inner_text("#saude-tabela"))
                pg.close()
        finally:
            nav.close()
            pw.stop()


if __name__ == "__main__":
    unittest.main()
