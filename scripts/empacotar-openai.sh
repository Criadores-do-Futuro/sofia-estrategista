#!/usr/bin/env bash
# Monta o pacote de envio da Sofia Estrategista ao diretório público de plugins da OpenAI (ChatGPT e Codex):
#   dist/sofia-estrategista-openai.zip   uma pasta só, sofia-estrategista/, no formato Agent Plugins:
#                                         plugin.json na raiz (a ficha, os casos de revisão, as notas da versão e
#                                         a tradução em extensions.com.openai), mcp.json com o conector e o OAuth,
#                                         as skills e os arquivos que elas usam.
#
# O plugin.json e o mcp.json moram em openai/ (fora de plugin/, como os catálogos). O resto vem de plugin/, com
# as mesmas pastas e exclusões do empacotar.sh, menos os manifestos do Claude e do Codex (.claude-plugin,
# .codex-plugin e .mcp.json): o portal converte ou ignora esses arquivos quando o plugin.json da raiz existe.
# Este script não mexe em plugin/ nem no pacote do Claude e não envia nada: o envio é feito no portal
# (docs/envio-openai.md). O empacotar.sh apaga a pasta dist/ inteira; rode este depois dele.
#
# Antes de fechar, o pacote passa pelo scripts/validar_pacote_openai.py. Com erro, o .zip não fica em dist/.
# DIST_OPENAI troca a pasta de saída (os testes usam uma pasta temporária).
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$RAIZ/plugin"
FONTE="$RAIZ/openai"
DIST="${DIST_OPENAI:-$RAIZ/dist}"
PASTA="sofia-estrategista"
ZIP="$DIST/sofia-estrategista-openai.zip"

ITENS=(
  assets
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
  '*.DS_Store'
  '*/__pycache__/*' '*.pyc' '*/node_modules/*'
  'skills/*/tests/*' 'painel/index.html' 'painel/estado.json' 'painel/telemetria.json'
  'painel/revisao.json' 'painel/revisao/*' 'painel/previa/*' 'docs/superpowers/*'
  'treinamento/*/videos/*' 'treinamento/*/folhas/*' 'treinamento/*/raw_frames/*'
  'treinamento/*/frames-por-categoria/*' 'treinamento/*/metadata/*'
)

for arquivo in plugin.json mcp.json; do
  [ -f "$FONTE/$arquivo" ] || { echo "Falta openai/$arquivo." >&2; exit 1; }
done
cd "$PLUGIN"
for item in "${ITENS[@]}"; do
  [ -e "$item" ] || { echo "Falta em plugin/: $item" >&2; exit 1; }
done

# 1. O manifesto da OpenAI tem o mesmo nome, versão, licença e repositório dos manifestos do Claude e do Codex.
python3 - "$FONTE/plugin.json" "$PLUGIN/.claude-plugin/plugin.json" "$PLUGIN/.codex-plugin/plugin.json" <<'PY'
import json, sys
openai, *outros = (json.load(open(c, encoding='utf-8')) for c in sys.argv[1:])
erros = [f'{campo}: openai/plugin.json tem {openai.get(campo)!r}, {nome} tem {m.get(campo)!r}'
         for nome, m in zip(('.claude-plugin', '.codex-plugin'), outros)
         for campo in ('name', 'version', 'license', 'repository') if openai.get(campo) != m.get(campo)]
if erros:
    sys.exit('Suba a versão nos três manifestos juntos:\n  ' + '\n  '.join(erros))
PY

MONTAGEM="$(mktemp -d "${TMPDIR:-/tmp}/empacotar-openai.XXXXXX")"
trap 'rm -rf "$MONTAGEM"' EXIT

# 2. Copia só o que entra, com as mesmas exclusões do empacotar.sh, e põe o plugin.json e o mcp.json na raiz.
zip -q -r -X "$MONTAGEM/conteudo.zip" "${ITENS[@]}" -x "${FORA[@]}"
mkdir "$MONTAGEM/$PASTA"
unzip -q "$MONTAGEM/conteudo.zip" -d "$MONTAGEM/$PASTA"
cp "$FONTE/plugin.json" "$FONTE/mcp.json" "$MONTAGEM/$PASTA/"

# 3. O que o portal recusa e que dá para ver antes do .zip: hooks, .app.json e caminho com caractere especial.
if [ -e "$MONTAGEM/$PASTA/hooks" ] || [ -e "$MONTAGEM/$PASTA/.app.json" ]; then
  echo "O pacote não pode levar hooks/ nem .app.json: o diretório da OpenAI recusa os dois." >&2
  exit 1
fi
INVALIDOS="$(cd "$MONTAGEM" && find "$PASTA" | LC_ALL=C grep -v -E '^[A-Za-z0-9._/-]+$' || true)"
if [ -n "$INVALIDOS" ]; then
  echo "Caminhos com caractere fora de A-Z, a-z, 0-9, ponto, hífen e sublinhado:" >&2
  echo "$INVALIDOS" >&2
  exit 1
fi

# 4. Fecha o .zip com a pasta como única entrada do topo e confere o arquivo pronto, como o portal vai recebê-lo.
mkdir -p "$DIST"
rm -f "$ZIP"
(cd "$MONTAGEM" && zip -q -r -X "$ZIP" "$PASTA")
if ! python3 "$RAIZ/scripts/validar_pacote_openai.py" "$ZIP" "$@"; then
  rm -f "$ZIP"
  echo "O pacote não passou na conferência; nada ficou em dist/." >&2
  exit 1
fi

echo "Pronto: $(unzip -Z1 "$ZIP" | grep -vc '/$') arquivos em $ZIP"
