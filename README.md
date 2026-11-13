# Sofia Estrategista (plugin)

Código do plugin Sofia Estrategista, a estrategista de vídeo curto do curso Criador Estrategista. O plugin junta a skill com o método do curso, atalhos, dois ajudantes e o conector do planejamento do site. O que o plugin faz, para quem usa, está em [plugin/README.md](plugin/README.md).

## Pastas

| Pasta | O que tem |
|---|---|
| `plugin/` | O plugin em si: `.claude-plugin/plugin.json`, `.mcp.json`, `skills/`, `commands/`, `agents/`, README e LICENSE |
| `.claude-plugin/marketplace.json` | O catálogo, para instalar pelo Claude Code direto deste repositório |
| `scripts/empacotar.sh` | Monta `dist/sofia-estrategista.plugin` (o plugin, um .zip por dentro) e `dist/sofia-estrategista.skill` (só a skill) |
| `scripts/conferir-ferramentas.mjs` | Confere se toda ferramenta citada no plugin existe no conector |
| `docs/desenho.md` | Por que o plugin é assim: regras, escolhas e o que fica para depois |

## Antes de cada versão

1. `claude plugin validate plugin` e `claude plugin validate .` sem erro.
2. `node scripts/conferir-ferramentas.mjs <pasta-do-webapp>` sem ferramenta faltando, com a pasta do webapp na `main` (é a `main` que está no ar). O script não confere os campos de cada ferramenta: confira à mão os que o plugin cita, como `nasceuDe`, `pediuCorte` e `escolhidoPeloAluno`.
3. Suba a versão em `plugin/.claude-plugin/plugin.json`.
4. `bash scripts/empacotar.sh` e copie os dois arquivos de `dist/` para `public/kit/` do webapp.

## Instalar pelo Claude Code

```bash
claude plugin marketplace add bento-dev-ia/sofia-estrategista
claude plugin install sofia-estrategista
```

Depois, `/mcp` para entrar no conector com o e-mail do curso.
