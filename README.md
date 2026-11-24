# Sofia Estrategista (plugin)

Código do plugin Sofia Estrategista, a estrategista de vídeo curto do curso Criador Estrategista. O plugin junta a skill com o método do curso, atalhos, a equipe de agentes (quem escreve e quem confere cada etapa) e o conector do planejamento do site. O que o plugin faz, para quem usa, está em [plugin/README.md](plugin/README.md).

## Pastas

| Pasta | O que tem |
|---|---|
| `plugin/` | O plugin em si: `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json` (o manifesto do Codex), `.mcp.json`, `assets/icon.png`, `skills/`, `commands/`, `agents/`, README e LICENSE |
| `.claude-plugin/marketplace.json` | O catálogo, para instalar pelo Claude Code direto deste repositório |
| `scripts/empacotar.sh` | Monta `dist/sofia-estrategista.plugin` (o plugin, um .zip por dentro) e `dist/sofia-estrategista.skill` (só a skill) |
| `scripts/conferir-ferramentas.mjs` | Confere se toda ferramenta citada no plugin existe no conector |
| `tests/test_equipe.py` | Confere a equipe: espelho do método sem edição à mão, um agente por papel, ferramentas citadas e as regras de texto. Fica fora do pacote |
| `docs/desenho.md` | Por que o plugin é assim: regras, escolhas e o que fica para depois |

## Antes de cada versão

1. `claude plugin validate plugin` e `claude plugin validate .` sem erro.
2. `node scripts/conferir-ferramentas.mjs <pasta-do-webapp>` sem ferramenta faltando, com a pasta do webapp na `main` (é a `main` que está no ar). O script não confere os campos de cada ferramenta: confira à mão os que o plugin cita, como `nasceuDe`, `pediuCorte` e `escolhidoPeloAluno`.
3. `python3 -m unittest discover -s tests` sem falha. Com `SOFIA_WEBAPP=<pasta-do-webapp>`, a lista de ferramentas do teste também é comparada com o servidor.
4. Suba a versão em `plugin/.claude-plugin/plugin.json`, em `plugin/.codex-plugin/plugin.json` (com as notas da versão) e na seção "Versão e atualização" da skill.
5. `bash scripts/empacotar.sh` e copie os dois arquivos de `dist/` para `public/kit/` do webapp.

As referências marcadas como "Cópia da peça" e o `cartas.md` (em `plugin/skills/sofia-estrategista/references/`) não se editam aqui: mude a peça no webapp e rode, nele, `npx tsx scripts/exportar-referencias.mts CAMINHO_DESTE_REPOSITORIO/plugin`. O mesmo comando reescreve a linha `disallowedTools` de cada agente da equipe com as ferramentas do conector que gravam (a trava). O `tests/test_equipe.py` acusa arquivo do espelho mudado à mão e agente sem a trava completa.

## Instalar pelo Claude Code

```bash
claude plugin marketplace add bento-dev-ia/sofia-estrategista
claude plugin install sofia-estrategista
```

Depois, `/mcp` para entrar no conector com o e-mail do curso.
