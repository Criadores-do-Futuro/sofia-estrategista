#!/usr/bin/env bash
# Monta os dois arquivos que vão para a página Kit do site:
#   dist/sofia-estrategista.zip    o plugin inteiro, para o Claude (Personalizar › Plugins › Enviar plugin)
#   dist/sofia-estrategista.skill  só a skill, numa pasta sofia-estrategista/, para o ChatGPT e para quem
#                                  prefere instalar só a skill
# Os dois saem do mesmo plugin/, então não há duas fontes para manter.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$RAIZ/dist"
PLUGIN="$RAIZ/plugin"

rm -rf "$DIST"
mkdir -p "$DIST"

# Plugin: o conteúdo de plugin/ na raiz do zip (.claude-plugin/, skills/, commands/, agents/, .mcp.json).
(
  cd "$PLUGIN"
  find . -name .DS_Store -delete
  zip -q -r -X "$DIST/sofia-estrategista.zip" . -x '*.DS_Store'
)

# Skill solta: a pasta sofia-estrategista/ com SKILL.md dentro.
(
  cd "$PLUGIN/skills"
  zip -q -r -X "$DIST/sofia-estrategista.skill" sofia-estrategista -x '*.DS_Store'
)

echo "Pronto:"
ls -l "$DIST"
