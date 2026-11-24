#!/usr/bin/env bash
# Monta os arquivos da Sofia Estrategista para o kit do site, a partir da pasta plugin/:
#   dist/sofia-estrategista.zip     o plugin inteiro dentro de uma pasta só (sofia-estrategista/), no formato
#                                   que o Claude aceita em Personalizar › Plugins › Adicionar › Enviar plugin e
#                                   que o Codex instala como plugin local (a pasta traz o próprio catálogo,
#                                   marketplace sofia-estrategista-local);
#   dist/sofia-estrategista.plugin  o mesmo .zip com outra extensão, para o navegador não descompactar sozinho
#                                   ao baixar (o Safari abre .zip);
#   dist/sofia-estrategista.skill   só a skill sofia-estrategista, numa pasta sofia-estrategista/, para o
#                                   ChatGPT e para quem instala só a skill.
#
# Entram só as pastas e arquivos que o plugin usa; testes, caches, dependências instaladas e dados locais
# ficam de fora. Os catálogos de marketplace moram na raiz do repositório, fora de plugin/, e não entram.
# Antes de fechar o .zip, a pasta montada passa pelo `claude plugin validate`, quando ele está instalado.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$RAIZ/plugin"
DIST="$RAIZ/dist"
PASTA="sofia-estrategista"

ITENS=(
  .claude-plugin
  .codex-plugin
  .mcp.json
  assets
  hooks
  types
  skills
  commands
  agents
  scripts
  beditor
  schemas
  motion
  painel
  treinamento
  docs
  requirements-editorial.txt
  requirements-capcut-desktop.txt
  requirements-motion.txt
  README.md
  LICENSE
)

FORA=(
  '*.DS_Store' '.claude-plugin/types/*'
  '*/__pycache__/*' '*.pyc' '*/node_modules/*'
  'skills/*/tests/*' 'painel/index.html' 'painel/estado.json' 'painel/telemetria.json'
  'painel/revisao.json' 'painel/revisao/*' 'painel/previa/*' 'docs/superpowers/*'
  'treinamento/*/videos/*' 'treinamento/*/folhas/*' 'treinamento/*/raw_frames/*'
  'treinamento/*/frames-por-categoria/*' 'treinamento/*/metadata/*'
)

cd "$PLUGIN"
for item in "${ITENS[@]}"; do
  [ -e "$item" ] || { echo "Falta em plugin/: $item" >&2; exit 1; }
done

MONTAGEM="$(mktemp -d "${TMPDIR:-/tmp}/empacotar.XXXXXX")"
trap 'rm -rf "$MONTAGEM"' EXIT

# 1. Copia só o que entra, com as mesmas regras de exclusão, para uma pasta com o nome do plugin.
zip -q -r -X "$MONTAGEM/conteudo.zip" "${ITENS[@]}" -x "${FORA[@]}"
mkdir "$MONTAGEM/$PASTA"
unzip -q "$MONTAGEM/conteudo.zip" -d "$MONTAGEM/$PASTA"

# O catálogo do Codex para quem instala pelo .zip: a própria pasta vira um marketplace local.
mkdir -p "$MONTAGEM/$PASTA/.agents/plugins"
cat > "$MONTAGEM/$PASTA/.agents/plugins/marketplace.json" <<'JSON'
{
  "name": "sofia-estrategista-local",
  "interface": {"displayName": "Sofia Estrategista"},
  "plugins": [
    {
      "name": "sofia-estrategista",
      "source": {"source": "local", "path": "./"},
      "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
      "category": "Productivity"
    }
  ]
}
JSON

# 2. Confere a pasta exatamente como ela vai dentro do .zip.
# O envio de plugin do Claude recusa o .zip inteiro quando um caminho tem caractere fora de
# letra sem acento, número, ponto, hífen e sublinhado ("Zip file contains path with invalid
# characters"). Fonte variável baixada do Google Fonts vem como Nome[wght].ttf: renomeie antes.
INVALIDOS="$(cd "$MONTAGEM" && find "$PASTA" | LC_ALL=C grep -v -E '^[A-Za-z0-9._/-]+$' || true)"
if [ -n "$INVALIDOS" ]; then
  echo "Caminhos que o envio de plugin recusa (use só A-Z, a-z, 0-9, ponto, hífen e sublinhado):" >&2
  echo "$INVALIDOS" >&2
  exit 1
fi
if command -v claude >/dev/null 2>&1; then
  claude plugin validate "$MONTAGEM/$PASTA"
else
  echo "Claude Code não encontrado; a validação do manifesto ficou de fora." >&2
fi

# 3. Fecha os arquivos: o .zip com a pasta como única entrada do topo, a cópia .plugin e a skill solta.
rm -rf "$DIST"
mkdir -p "$DIST"
(cd "$MONTAGEM" && zip -q -r -X "$DIST/$PASTA.zip" "$PASTA")
cp "$DIST/$PASTA.zip" "$DIST/$PASTA.plugin"
(cd "$MONTAGEM/$PASTA/skills" && zip -q -r -X "$DIST/$PASTA.skill" sofia-estrategista)

echo "Pronto: $(unzip -Z1 "$DIST/$PASTA.zip" | grep -vc '/$') arquivos no plugin."
ls -l "$DIST"
