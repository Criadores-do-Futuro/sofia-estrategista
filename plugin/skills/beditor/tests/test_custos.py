"""`custos.py` lê o registro do Claude Code e diz quanto cada etapa custou — de forma
determinística.

O que pode dar errado, e é o que se tranca aqui: contar o mesmo `requestId` duas
vezes (o registro tem uma linha por bloco da resposta), atribuir a etapa pela
ferramenta errada (a ordem da tabela é a precedência), deixar o almoço do dono
entrar no tempo de parede (o teto por intervalo), e — o pior — a mesma sessão
dar tabelas diferentes em duas execuções.
"""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import custos  # noqa: E402

T0 = "2026-09-15T12:00:"


def _ass(rid, seg, ferramentas=(), agente=False, usage=None, texto=None):
    conteudo = [{"type": "text", "text": texto}] if texto else []
    for i, (nome, entrada) in enumerate(ferramentas):
        conteudo.append({"type": "tool_use", "id": f"{rid}-t{i}", "name": nome, "input": entrada})
    return {"type": "assistant", "requestId": rid, "isSidechain": agente,
            "timestamp": f"{T0}{seg:02d}.000Z", "uuid": f"u-{rid}-{seg}",
            "message": {"model": "claude-x", "role": "assistant", "content": conteudo,
                        "usage": usage or {"input_tokens": 2, "cache_creation_input_tokens": 100,
                                           "cache_read_input_tokens": 1000, "output_tokens": 50,
                                           "output_tokens_details": {"thinking_tokens": 10}}}}


def _pedido(seg, texto):
    return {"type": "user", "isSidechain": False, "promptSource": "typed", "origin": {"kind": "human"},
            "timestamp": f"{T0}{seg:02d}.000Z", "message": {"role": "user", "content": texto}}


def _resultado(rid, i, seg):
    return {"type": "user", "isSidechain": False, "timestamp": f"{T0}{seg:02d}.000Z",
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": f"{rid}-t{i}"}]}}


class TestCustos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        raiz = Path(self.tmp.name)
        self.arq = raiz / "sessao-teste.jsonl"
        linhas = [
            _pedido(0, "transcreva os takes do projeto 16, por favor, com contexto"),
            # r1: duas linhas, MESMO requestId (um bloco de texto e um tool_use) — usage conta UMA vez
            _ass("r1", 1, texto="vou transcrever"),
            _ass("r1", 1, ferramentas=[("Bash", {"command": "python3 transcrever.py edicao/oficina/transcricao a.mov"})]),
            _resultado("r1", 0, 5),
            # r2: Edit em plano.json → provas (precedência: provas vem antes de editar)
            _ass("r2", 6, ferramentas=[("Edit", {"file_path": "/p/edicao/plano.json", "old_string": "a", "new_string": "b"})]),
            _resultado("r2", 0, 7),
            _pedido(10, "agora olha a folha e me diz se o cartão está no lugar"),
            # r3: Read de imagem → olhar
            _ass("r3", 11, ferramentas=[("Read", {"file_path": "/p/edicao/qa.jpg"})]),
            _resultado("r3", 0, 12),
            # r4: sem tool_use → conversa
            _ass("r4", 13, texto="está no lugar."),
            # r5: subagente (sidechain), git
            _ass("r5", 14, agente=True, ferramentas=[("Bash", {"command": "git status"})]),
        ]
        # um resultado tardio do r1: intervalo de 53 s dentro da etapa transcrever (abaixo do teto)
        linhas.append(_resultado("r1", 0, 58))
        with open(self.arq, "w", encoding="utf-8") as fh:
            for l in linhas:
                fh.write(json.dumps(l) + "\n")
            # linha fora do formato: ignorada, não derruba
            fh.write("{isto não é json}\n")
        # subagente em pasta própria também entra
        sub = raiz / "sessao-teste" / "subagents"
        sub.mkdir(parents=True)
        with open(sub / "agent-a1.jsonl", "w", encoding="utf-8") as fh:
            fh.write(json.dumps(_ass("r6", 15, agente=True,
                                     ferramentas=[("Bash", {"command": "python3 render_analise.py /p"})])) + "\n")

    def tearDown(self):
        self.tmp.cleanup()

    def _analise(self, **kw):
        s = custos.ler_sessao(self.arq)
        return s, custos.analisar(s, **kw)

    def test_etapa_herda_do_primeiro_tool_use_com_precedencia(self):
        s, _ = self._analise()
        et = {rid: t["etapa"] for rid, t in s["turnos"].items()}
        self.assertEqual(et["r1"], "transcrever")
        self.assertEqual(et["r2"], "provas", "plano.json casa antes de Edit")
        self.assertEqual(et["r3"], "olhar")
        self.assertEqual(et["r4"], "conversa")
        self.assertEqual(et["r5"], "git")
        self.assertEqual(et["r6"], "renderizar")

    def test_tabela_de_atribuicao_cobre_os_casos_da_docstring(self):
        casos = [
            ("Bash", {"command": "python3 silencio.py edicao/dados.json x.wav"}, "cortar"),
            ("Bash", {"command": "python3 qa_analise.py /p"}, "medir"),
            ("Bash", {"command": "yt-dlp https://x"}, "provas"),
            ("Bash", {"command": "python3 biblioteca.py cama --clima calmo"}, "biblioteca"),
            ("Bash", {"command": "python3 setup.py --pastas"}, "setup"),
            ("mcp__zernio__posts_create", {"x": 1}, "publicar"),
            ("Agent", {"prompt": "faz"}, "delegar"),
            ("Artifact", {"file_path": "a.html"}, "artifact"),
            ("Write", {"file_path": "/x/y.py", "content": ""}, "editar"),
            ("Read", {"file_path": "/x/y.py"}, "investigar"),
            ("mcp__plugin_context-mode_context-mode__ctx_search", {"queries": ["a"]}, "investigar"),
            ("Grep", {"pattern": "x"}, "investigar"),
            ("ToolSearch", {"query": "x"}, "outros"),
        ]
        for nome, entrada, esperado in casos:
            self.assertEqual(custos.etapa_de([(nome, entrada)]), esperado, nome)

    def test_usage_conta_uma_vez_por_requestId(self):
        s, r = self._analise()
        self.assertEqual(len(s["turnos"]), 6)
        tr = next(e for e in r["etapas"] if e["etapa"] == "transcrever")
        self.assertEqual(tr["turnos"], 1)
        self.assertEqual(tr["cacheLida"], 1000, "duas linhas do r1, um usage só")
        self.assertEqual(tr["saida"], 50)
        self.assertEqual(tr["pensamento"], 10)
        self.assertEqual(r["total"]["cacheLida"], 6 * 1000)

    def test_subagentes_ficam_na_coluna_agentes(self):
        _, r = self._analise()
        git = next(e for e in r["etapas"] if e["etapa"] == "git")
        self.assertEqual((git["turnos"], git["agentes"]), (0, 1))
        rend = next(e for e in r["etapas"] if e["etapa"] == "renderizar")
        self.assertEqual((rend["turnos"], rend["agentes"]), (0, 1), "subagents/*.jsonl entra")
        self.assertEqual(r["total"]["agentes"], 2)

    def test_teto_do_intervalo(self):
        # transcrever: eventos em 1, 1, 5, 58 → 0 + 4 + 53 = 57 s, tudo abaixo do teto
        _, r = self._analise()
        tr = next(e for e in r["etapas"] if e["etapa"] == "transcrever")
        self.assertAlmostEqual(tr["paredeS"], 57.0)
        # a função pura: um intervalo de 10 min vira 120 s
        from datetime import datetime, timedelta, timezone
        a = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(custos.parede([a, a + timedelta(minutes=10), a + timedelta(minutes=10, seconds=30)]), 150)

    def test_por_pedido(self):
        _, r = self._analise()
        ped = r["pedidos"]
        self.assertEqual(len(ped), 2)
        self.assertTrue(ped[0]["texto"].startswith("transcreva os takes"))
        self.assertLessEqual(len(ped[0]["texto"]), 60)
        self.assertEqual(ped[0]["turnos"], 2, "r1 e r2 caem no primeiro pedido")
        self.assertEqual(ped[1]["turnos"], 2, "r3 e r4 no segundo")
        self.assertEqual(ped[1]["agentes"], 2)
        self.assertEqual(ped[0]["ateProximoS"], 10.0)

    def test_janela_desde_ate(self):
        from datetime import datetime, timezone
        _, r = self._analise(desde=datetime(2026, 9, 15, 12, 0, 10, tzinfo=timezone.utc))
        self.assertEqual(sorted(e["etapa"] for e in r["etapas"]), ["conversa", "git", "olhar", "renderizar"])
        self.assertEqual(len(r["pedidos"]), 1)

    def test_duas_execucoes_dao_saida_identica(self):
        saidas = []
        for _ in range(2):
            buf = io.StringIO()
            with redirect_stdout(buf):
                custos.main(["--sessao", str(self.arq), "--json", "--por-pedido"])
            d = json.loads(buf.getvalue())
            d.pop("gerado_em")
            saidas.append(json.dumps(d, sort_keys=True))
        self.assertEqual(saidas[0], saidas[1])
        # e o texto também, tirando a linha do cabeçalho que carrega o carimbo
        textos = []
        for _ in range(2):
            buf = io.StringIO()
            with redirect_stdout(buf):
                custos.main(["--sessao", str(self.arq), "--por-pedido"])
            textos.append("\n".join(l for l in buf.getvalue().splitlines() if "gerado em" not in l))
        self.assertEqual(textos[0], textos[1])
        self.assertIn("POR PEDIDO DO DONO", textos[0])
        self.assertIn("TOTAL", textos[0])

    def test_projeto_escreve_custos_json_e_cruza_telemetria(self):
        proj = Path(self.tmp.name) / "proj"
        of = proj / "edicao" / "oficina"
        of.mkdir(parents=True)
        (of / "telemetria.jsonl").write_text(
            json.dumps({"etapa": "transcrever", "script": "transcrever.py", "inicio": "2026-09-15T09:00:00-03:00",
                        "fim": "2026-09-15T09:01:00-03:00", "segundos": 60.0, "rc": 0, "args": {}}) + "\n"
            + json.dumps({"etapa": "transcrever", "script": "transcrever.py", "inicio": "2026-09-15T09:05:00-03:00",
                          "fim": "2026-09-15T09:05:02-03:00", "segundos": 2.5, "rc": 1, "args": {}}) + "\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            custos.main(["--sessao", str(self.arq), "--projeto", str(proj), "--json"])
        d = json.loads((of / "custos.json").read_text())
        self.assertEqual(d["maquina"][0]["etapa"], "transcrever")
        self.assertEqual(d["maquina"][0]["execucoes"], 2)
        self.assertEqual(d["maquina"][0]["falhas"], 1)
        self.assertEqual(d["maquina"][0]["segundosMaquina"], 62.5)
        self.assertEqual(d["maquina"][0]["paredeSessaoS"], 57.0)


if __name__ == "__main__":
    unittest.main()
