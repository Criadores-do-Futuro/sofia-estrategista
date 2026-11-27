#!/usr/bin/env python3
"""Confere o pacote de envio da Sofia ao diretório de plugins da OpenAI, regra por regra.

Uso:
  python3 scripts/validar_pacote_openai.py dist/sofia-estrategista-openai.zip
  python3 scripts/validar_pacote_openai.py PASTA_DO_PACOTE
  opções: --webapp PASTA   confere os casos de revisão contra as ferramentas do servidor (PASTA/src)
                           e as anotações readOnlyHint, openWorldHint e destructiveHint de cada uma;
          --links          abre os quatro links da ficha e confere que abrem sem login e citam o publicador.

Fontes, conferidas em 27/11/2026:
  developers.openai.com/plugins/deploy/submission-errors  (os códigos de erro usados abaixo)
  developers.openai.com/plugins/deploy/submission         (ficha, casos de revisão, publicação e traduções)
  developers.openai.com/plugins/build/plugins              (formato Agent Plugins, mcp.json e autenticação)
  developers.openai.com/plugins/plugin-guidelines          (anotações das ferramentas)
  plugin-creator 0.1.28 da OpenAI: prepare-plugin-submission (listing.md, review-materials.md) e
  create-plugin (zip-requirements.md, plugin-packages.md)

Três níveis: erro (o portal recusa; sai com código 1), aviso (o portal avisa ou ignora) e pendente (o ZIP
pode subir assim, mas o envio para revisão exige: vídeo de demonstração, países e o que só o portal faz).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import stat
import sys
import tempfile
import unicodedata
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

try:
    import yaml
except ImportError:  # pragma: no cover - o PyYAML vem com o requirements-motion.txt
    yaml = None

SCHEMA_PLUGIN = 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
SCHEMA_MCP = 'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json'
CAMPOS_DO_MANIFESTO = {'$schema', 'name', 'version', 'description', 'author', 'homepage', 'repository', 'license',
                       'keywords', 'extensions'}
CAMPOS_DO_OPENAI = {'interface', 'review', 'publication', 'onboardingSkill', 'requires_local_executor', 'id', 'apps',
                    'hooks', 'publicationPolicy'}
CATEGORIAS = {'Business & Operations', 'Communication', 'Creativity', 'Data & Analytics', 'Developer Tools',
              'Education & Research', 'Entertainment', 'Finance', 'Healthcare', 'Other', 'Productivity',
              'Scientific Research', 'Security', 'Travel'}
URLS_DA_FICHA = {'websiteURL': 'plugin_website_url', 'supportURL': 'plugin_support_url',
                 'privacyPolicyURL': 'plugin_privacy_policy_url', 'termsOfServiceURL': 'plugin_terms_of_service_url'}
IMAGENS_DA_FICHA = ('logo', 'composerIcon', 'logoDark', 'composerIconDark')
SEMVER = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
                    r'(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?'
                    r'(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$')
NOME_NO_PORTAL = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]*$')
NOME_AGENT_PLUGINS = re.compile(r'^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$')
COR = re.compile(r'^#[0-9A-Fa-f]{6}$')
SEGREDOS = re.compile(
    r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}|\bghp_[A-Za-z0-9]{36}\b'
    r'|\bgithub_pat_[A-Za-z0-9_]{40,}|\bAKIA[0-9A-Z]{16}\b|\bxox[abprs]-[A-Za-z0-9-]{10,}|\bsk_live_[A-Za-z0-9]{20,}')
MIB = 1024 * 1024


class Relatorio:
    def __init__(self):
        self.erros: list[tuple[str, str]] = []
        self.avisos: list[tuple[str, str]] = []
        self.pendentes: list[tuple[str, str]] = []
        self.infos: list[str] = []
        self.conferencias = 0
        self.regras: set[str] = set()

    def conferir(self, condicao: bool, codigo: str, mensagem: str, nivel: str = 'erro') -> bool:
        self.conferencias += 1
        self.regras.add(codigo)
        if not condicao:
            {'erro': self.erros, 'aviso': self.avisos, 'pendente': self.pendentes}[nivel].append((codigo, mensagem))
        return condicao

    def codigos(self) -> set[str]:
        return {c for c, _ in self.erros}


# --- Texto aceito ---------------------------------------------------------------------------------------------

def texto_aceito(texto: str, multilinha: bool = False) -> bool:
    """Sem caractere de controle, separador de linha ou parágrafo Unicode nem formatação invisível."""
    for ch in texto:
        if ch == '\n' and multilinha:
            continue
        if unicodedata.category(ch) in ('Cc', 'Cf', 'Zl', 'Zp', 'Cs', 'Co', 'Cn'):
            return False
    return True


def uma_linha(texto: str) -> bool:
    return '\n' not in texto and '\r' not in texto


def conferir_texto(r: Relatorio, valor, campo: str, codigo: str, limite: int, multilinha: bool = False,
                   obrigatorio: bool = True):
    if valor is None:
        if obrigatorio:
            r.conferir(False, f'{codigo}_required', f'{campo} é obrigatório.')
        return
    if not r.conferir(isinstance(valor, str), f'{codigo}_wrong_type', f'{campo} precisa ser texto.'):
        return
    r.conferir(bool(valor.strip()), f'{codigo}_empty', f'{campo} não pode ficar vazio.')
    r.conferir(len(valor) <= limite, f'{codigo}_too_long', f'{campo} tem {len(valor)} caracteres; o limite é {limite}.')
    r.conferir(multilinha or uma_linha(valor), f'{codigo}_character_unsupported', f'{campo} precisa caber numa linha.')
    r.conferir(texto_aceito(valor, multilinha), f'{codigo}_character_unsupported',
               f'{campo} tem caractere de controle ou invisível.')


def url_https(valor) -> bool:
    if not isinstance(valor, str) or valor != valor.strip():
        return False
    m = re.match(r'^https://([^/?#]+)', valor)
    if not m or '@' in m.group(1) or not texto_aceito(valor) or ' ' in valor:
        return False
    host = m.group(1).split(':')[0]
    return bool(host) and '.' in host


def conferir_url(r: Relatorio, valor, campo: str, codigo: str, limite: int, obrigatorio: bool = False):
    if valor is None:
        if obrigatorio:
            r.conferir(False, f'{codigo}_required', f'{campo} é obrigatório no envio com MCP remoto.')
        return
    if not r.conferir(isinstance(valor, str), f'{codigo}_wrong_type', f'{campo} precisa ser texto.'):
        return
    r.conferir(bool(valor.strip()), f'{codigo}_empty', f'{campo} não pode ficar vazio.')
    r.conferir(url_https(valor), f'{codigo}_format', f'{campo} precisa ser um endereço https, sem login embutido: {valor}')
    r.conferir(len(valor) <= limite, f'{codigo}_too_long', f'{campo} passa de {limite} caracteres.')


# --- Imagens --------------------------------------------------------------------------------------------------

def formato_e_tamanho(dados: bytes):
    """Lê formato e dimensões do cabeçalho de PNG, JPEG e WebP, sem biblioteca de imagem."""
    if dados[:8] == b'\x89PNG\r\n\x1a\n' and dados[12:16] == b'IHDR':
        return 'png', int.from_bytes(dados[16:20], 'big'), int.from_bytes(dados[20:24], 'big')
    if dados[:2] == b'\xff\xd8':
        i = 2
        while i + 9 < len(dados):
            if dados[i] != 0xFF:
                i += 1
                continue
            marca = dados[i + 1]
            if marca in (0xD8, 0x01) or 0xD0 <= marca <= 0xD7:
                i += 2
                continue
            tamanho = int.from_bytes(dados[i + 2:i + 4], 'big')
            if 0xC0 <= marca <= 0xCF and marca not in (0xC4, 0xC8, 0xCC):
                return 'jpeg', int.from_bytes(dados[i + 7:i + 9], 'big'), int.from_bytes(dados[i + 5:i + 7], 'big')
            i += 2 + tamanho
        return 'jpeg', None, None
    if dados[:4] == b'RIFF' and dados[8:12] == b'WEBP':
        bloco = dados[12:16]
        if bloco == b'VP8X':
            return 'webp', 1 + int.from_bytes(dados[24:27], 'little'), 1 + int.from_bytes(dados[27:30], 'little')
        if bloco == b'VP8L':
            b = dados[21:25]
            return 'webp', 1 + (((b[1] & 0x3F) << 8) | b[0]), 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | (b[1] >> 6))
        if bloco == b'VP8 ':
            return ('webp', int.from_bytes(dados[26:28], 'little') & 0x3FFF,
                    int.from_bytes(dados[28:30], 'little') & 0x3FFF)
        return 'webp', None, None
    return None, None, None


def numero_svg(valor):
    if valor is None or not re.fullmatch(r'\s*[0-9]*\.?[0-9]+\s*', valor):
        return None
    return float(valor)


def conferir_imagem(r: Relatorio, raiz: Path, campo: str, caminho, minimo: int):
    if not r.conferir(isinstance(caminho, str), 'declared_asset_path_wrong_type', f'{campo} precisa ser um caminho.'):
        return
    r.conferir(bool(caminho), 'declared_asset_path_empty', f'{campo} não pode ficar vazio.')
    r.conferir(caminho == caminho.strip(), 'declared_asset_path_has_outer_whitespace', f'{campo} tem espaço nas pontas.')
    r.conferir(not any(ord(c) < 32 or ord(c) == 127 for c in caminho), 'declared_asset_path_has_control_character',
               f'{campo} tem caractere de controle.')
    r.conferir(caminho.startswith('./'), 'branding_asset_path_missing_root_prefix', f'{campo} precisa começar com ./')
    partes = PurePosixPath(caminho).parts
    seguro = not caminho.startswith('/') and not re.match(r'^[A-Za-z]:', caminho) and '..' not in partes
    if not r.conferir(seguro, 'declared_asset_path_unsafe', f'{campo} sai do pacote: {caminho}'):
        return
    arquivo = (raiz / caminho).resolve()
    if not r.conferir(str(arquivo).startswith(str(raiz.resolve()) + os.sep), 'declared_asset_path_outside_package',
                      f'{campo} aponta para fora do pacote.'):
        return
    if not r.conferir(arquivo.exists(), 'declared_asset_file_missing', f'{campo}: {caminho} não existe.'):
        return
    if not r.conferir(arquivo.is_file() and not (raiz / caminho).is_symlink(), 'declared_asset_not_regular_file',
                      f'{campo} precisa ser um arquivo comum.'):
        return
    ext = arquivo.suffix.lower()
    if not r.conferir(ext in ('.png', '.jpg', '.jpeg', '.webp', '.svg'), 'image_file_format_unsupported',
                      f'{campo}: use png, jpg, jpeg, webp ou svg.'):
        return
    r.conferir(arquivo.stat().st_size <= 5 * MIB, 'image_file_too_large', f'{campo} passa de 5 MiB.')
    dados = arquivo.read_bytes()
    if ext == '.svg':
        try:
            svg = ElementTree.fromstring(dados.decode('utf-8'))
        except (UnicodeDecodeError, ElementTree.ParseError):
            r.conferir(False, 'svg_xml_malformed', f'{campo}: SVG inválido.')
            return
        if not r.conferir(svg.tag.split('}')[-1] == 'svg', 'svg_root_element_invalid', f'{campo}: a raiz não é <svg>.'):
            return
        caixa = (svg.get('viewBox') or '').replace(',', ' ').split()
        if len(caixa) == 4:
            largura, altura = numero_svg(caixa[2]), numero_svg(caixa[3])
        else:
            largura, altura = numero_svg(svg.get('width')), numero_svg(svg.get('height'))
        if not r.conferir(largura is not None and altura is not None, 'svg_dimensions_missing',
                          f'{campo}: SVG sem viewBox nem largura e altura numéricas.'):
            return
        r.conferir(largura > 0 and altura > 0, 'svg_dimensions_not_positive', f'{campo}: dimensões não positivas.')
        r.conferir(largura == altura, 'svg_dimensions_not_square', f'{campo}: SVG não é quadrado.')
        r.conferir(min(largura, altura) >= minimo, 'svg_dimensions_too_small', f'{campo}: menor que {minimo}.')
        return
    formato, largura, altura = formato_e_tamanho(dados)
    if not r.conferir(formato is not None and largura is not None, 'raster_image_decode_failed',
                      f'{campo}: não consegui ler a imagem.'):
        return
    esperado = {'.png': 'png', '.jpg': 'jpeg', '.jpeg': 'jpeg', '.webp': 'webp'}[ext]
    r.conferir(formato == esperado, 'raster_image_extension_content_mismatch', f'{campo}: extensão {ext}, conteúdo {formato}.')
    r.conferir(largura == altura, 'raster_image_not_square', f'{campo}: {largura} × {altura} não é quadrado.')
    r.conferir(min(largura, altura) >= 48, 'raster_image_dimensions_too_small', f'{campo}: menor que 48 × 48.')
    r.conferir(max(largura, altura) <= 4096, 'raster_image_dimensions_too_large', f'{campo}: maior que 4096 × 4096.')
    # listing.md: o logo da ficha tem pelo menos 256 × 256; o ícone do compositor, 48 × 48.
    r.conferir(min(largura, altura) >= minimo, 'listing_icon_too_small', f'{campo}: a ficha pede pelo menos {minimo} × {minimo}.')
    r.infos.append(f'{campo}: {caminho}, {formato.upper()} {largura} × {altura}, {len(dados)} bytes')


def luminancia(cor: str) -> float:
    canais = []
    for i in (1, 3, 5):
        c = int(cor[i:i + 2], 16) / 255
        canais.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]


def contraste(a: str, b: str) -> float:
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# --- Arquivo ZIP ----------------------------------------------------------------------------------------------

def conferir_zip(r: Relatorio, caminho: Path, destino: Path) -> Path | None:
    """As regras de ZIP do portal; extrai em destino e devolve a raiz do plugin."""
    if not r.conferir(caminho.stat().st_size > 0, 'archive_empty', 'O ZIP está vazio.'):
        return None
    r.conferir(caminho.stat().st_size <= 100 * 1000 * 1000, 'archive_too_large', 'O ZIP passa de 100 MB.')
    if not r.conferir(zipfile.is_zipfile(caminho), 'archive_format_not_zip', 'Não é um ZIP válido.'):
        return None
    with zipfile.ZipFile(caminho) as z:
        entradas = z.infolist()
        r.conferir(len(entradas) > 0, 'archive_empty', 'O ZIP não tem entradas.')
        r.conferir(len(entradas) <= 5000, 'archive_too_many_entries', f'{len(entradas)} entradas; o limite é 5.000.')
        r.conferir(sum(e.file_size for e in entradas) <= 512 * MIB, 'archive_uncompressed_too_large',
                   'Descompactado passa de 512 MiB.')
        vistos, normalizados, arquivos, pastas = set(), {}, set(), set()
        for e in entradas:
            nome = e.filename
            if not r.conferir(bool(nome), 'archive_member_path_empty', 'Entrada sem caminho.'):
                continue
            r.conferir(nome == nome.strip(), 'archive_member_path_has_outer_whitespace', f'{nome!r} tem espaço nas pontas.')
            r.conferir('\\' not in nome, 'archive_member_path_has_backslash', f'{nome} usa barra invertida.')
            r.conferir(not nome.startswith('/') and not re.match(r'^[A-Za-z]:', nome), 'archive_member_path_absolute',
                       f'{nome} é caminho absoluto.')
            segmentos = nome.rstrip('/').split('/')
            r.conferir(all(segmentos), 'archive_member_path_has_empty_segment', f'{nome} tem segmento vazio.')
            r.conferir('..' not in segmentos, 'archive_member_path_has_parent_segment', f'{nome} tem "..".')
            r.conferir(len(segmentos) <= 20, 'archive_member_path_too_deep', f'{nome} tem mais de 20 níveis.')
            # O portal não publica o limite de comprimento; 1.024 no caminho e 255 por nome é o limite comum.
            r.conferir(len(nome.encode()) <= 1024 and all(len(s.encode()) <= 255 for s in segmentos),
                       'archive_member_path_too_long', f'{nome} é longo demais.')
            r.conferir(nome not in vistos, 'archive_member_path_duplicate', f'{nome} repetido.')
            vistos.add(nome)
            chave = unicodedata.normalize('NFC', nome.rstrip('/')).casefold()
            r.conferir(normalizados.get(chave, nome) == nome, 'archive_member_path_normalization_collision',
                       f'{nome} colide com {normalizados.get(chave)} ao ignorar maiúsculas e acentos.')
            normalizados.setdefault(chave, nome)
            modo = (e.external_attr >> 16) & 0o170000
            r.conferir(modo in (0, stat.S_IFREG, stat.S_IFDIR), 'archive_member_type_unsupported',
                       f'{nome} não é arquivo nem pasta (link simbólico?).')
            r.conferir(e.file_size <= 100 * MIB, 'archive_member_too_large', f'{nome} passa de 100 MiB.')
            r.conferir(not e.flag_bits & 0x1 and e.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
                       'archive_member_unreadable', f'{nome} está cifrado ou usa compressão não aceita.')
            (pastas if nome.endswith('/') else arquivos).add(nome.rstrip('/'))
            for i in range(1, len(segmentos)):
                pastas.add('/'.join(segmentos[:i]))
        conflito = arquivos & pastas
        r.conferir(not conflito, 'archive_member_path_type_conflict', f'Arquivo que também é pasta: {sorted(conflito)[:3]}')
        if r.erros:
            return None
        topo = {n.split('/')[0] for n in vistos}
        if 'plugin.json' in topo:
            raiz_no_zip = ''
        else:
            com_manifesto = [t for t in topo if f'{t}/plugin.json' in arquivos]
            if not r.conferir(len(com_manifesto) == 1, 'plugin_root_ambiguous',
                              'O ZIP precisa de uma raiz de plugin só: na raiz ou numa pasta do topo.'):
                return None
            raiz_no_zip = com_manifesto[0]
            r.conferir(topo == {raiz_no_zip}, 'plugin_root_has_siblings',
                       f'Ao lado da pasta {raiz_no_zip}/ há {sorted(topo - {raiz_no_zip})}.')
        for e in entradas:
            z.extract(e, destino)
        r.infos.append(f'ZIP: {len(entradas)} entradas, {caminho.stat().st_size / MIB:.1f} MiB compactado, '
                       f'{sum(e.file_size for e in entradas) / MIB:.1f} MiB descompactado, raiz {raiz_no_zip or "(topo)"}/')
    return destino / raiz_no_zip if raiz_no_zip else destino


# --- Pacote ---------------------------------------------------------------------------------------------------

def ler_json(r: Relatorio, arquivo: Path, prefixo: str):
    if not r.conferir(arquivo.is_file() and not arquivo.is_symlink(), f'{prefixo}_not_file',
                      f'{arquivo.name} precisa ser um arquivo JSON comum.'):
        return None
    try:
        texto = arquivo.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        r.conferir(False, f'{prefixo}_unreadable', f'{arquivo.name} não é UTF-8.')
        return None
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as erro:
        r.conferir(False, f'{prefixo}_json_malformed', f'{arquivo.name}, linha {erro.lineno}: {erro.msg}')
        return None
    r.conferir(isinstance(dados, dict), f'{prefixo}_root_not_object', f'{arquivo.name} precisa ser um objeto JSON.')
    return dados if isinstance(dados, dict) else None


def procurar_chaves(dados, proibidas: set[str], caminho='') -> list[str]:
    achadas = []
    if isinstance(dados, dict):
        for k, v in dados.items():
            if k in proibidas:
                achadas.append(f'{caminho}.{k}'.lstrip('.'))
            achadas += procurar_chaves(v, proibidas, f'{caminho}.{k}')
    elif isinstance(dados, list):
        for i, v in enumerate(dados):
            achadas += procurar_chaves(v, proibidas, f'{caminho}[{i}]')
    return achadas


def conferir_arquivos(r: Relatorio, raiz: Path):
    links, lixo, segredos = [], [], []
    for pasta, subpastas, nomes in os.walk(raiz):
        for nome in subpastas + nomes:
            p = Path(pasta) / nome
            rel = p.relative_to(raiz).as_posix()
            if p.is_symlink():
                links.append(rel)
            if nome in ('.DS_Store', '__pycache__', 'node_modules') or nome.endswith('.pyc'):
                lixo.append(rel)
        for nome in nomes:
            p = Path(pasta) / nome
            if p.is_symlink() or p.stat().st_size > 2 * MIB:
                continue
            try:
                texto = p.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            if SEGREDOS.search(texto):
                segredos.append(p.relative_to(raiz).as_posix())
    r.conferir(not links, 'package_symlink', f'Links simbólicos no pacote: {links[:5]}')
    r.conferir(not lixo, 'package_junk', f'Arquivos de máquina no pacote: {lixo[:5]}', 'aviso')
    r.conferir(not segredos, 'package_secret', f'Parece haver segredo em: {segredos[:5]}')
    r.conferir(not (raiz / 'hooks').exists(), 'lifecycle_hooks_excluded',
               'O pacote leva hooks/: plugin com hooks não entra no diretório.')
    r.conferir(not (raiz / '.app.json').exists(), 'app_configuration_excluded', 'O ZIP não pode levar .app.json.')
    r.conferir(not (raiz / '.mcp.json').exists(), 'undeclared_mcp_manifest_ignored',
               '.mcp.json na raiz é ignorado: o pacote portátil usa mcp.json.', 'aviso')
    r.conferir(not (raiz / '.claude-plugin' / 'plugin.json').exists(), 'claude_format_normalized',
               '.claude-plugin/plugin.json vai ser convertido pelo portal.', 'aviso')
    r.conferir(not (raiz / '.codex-plugin' / 'plugin.json').exists(), 'codex_overlay_ignored',
               '.codex-plugin/plugin.json é ignorado quando plugin.json tem extensions.com.openai.', 'aviso')
    catalogos = [p.relative_to(raiz).as_posix() for p in raiz.rglob('marketplace.json')]
    r.conferir(not catalogos, 'archive_marketplace_excluded', f'Catálogo de marketplace no pacote: {catalogos}')


def conferir_manifesto(r: Relatorio, raiz: Path):
    arquivo = raiz / 'plugin.json'
    if not r.conferir(arquivo.exists(), 'plugin_manifest_missing', 'Falta plugin.json na raiz do plugin.'):
        return None
    m = ler_json(r, arquivo, 'plugin_manifest')
    if m is None:
        return None
    r.conferir(m.get('$schema') == SCHEMA_PLUGIN, 'plugin_manifest_missing',
               f'plugin.json sem "$schema": "{SCHEMA_PLUGIN}" não é reconhecido como Agent Plugins.')
    fora = sorted(set(m) - CAMPOS_DO_MANIFESTO)
    r.conferir(not fora, 'plugin_manifest_field_unsupported',
               f'Campos fora do Agent Plugins 1.0.0 no topo do plugin.json: {fora} (skills, mcpServers, apps e '
               'interface não vão no topo).')
    nome = m.get('name')
    if r.conferir(nome is not None, 'plugin_name_missing', 'name é obrigatório.') and \
            r.conferir(isinstance(nome, str), 'plugin_name_wrong_type', 'name precisa ser texto.'):
        r.conferir(bool(nome), 'plugin_name_empty', 'name vazio.')
        r.conferir(len(nome) <= 64, 'plugin_name_too_long', 'name passa de 64 caracteres.')
        r.conferir(bool(NOME_NO_PORTAL.match(nome)) and bool(NOME_AGENT_PLUGINS.match(nome)), 'plugin_name_format',
                   f'name "{nome}": letras minúsculas, números e hífen simples, começando e terminando em letra ou número.')
    versao = m.get('version')
    if r.conferir(versao is not None, 'plugin_version_missing', 'version é obrigatório no envio.') and \
            r.conferir(isinstance(versao, str), 'plugin_version_wrong_type', 'version precisa ser texto.'):
        r.conferir(bool(versao), 'plugin_version_empty', 'version vazio.')
        r.conferir(bool(SEMVER.match(versao)), 'plugin_version_not_semver', f'version "{versao}" não é SemVer.')
        r.conferir(len(versao) <= 64, 'plugin_version_too_long', 'version passa de 64 caracteres.')
    descricao = m.get('description')
    if r.conferir(descricao is not None, 'plugin_description_missing', 'description é obrigatório.'):
        conferir_texto(r, descricao, 'description', 'plugin_description', 1024, multilinha=True)
    autor = m.get('author')
    if r.conferir(isinstance(autor, dict), 'plugin_author_wrong_type', 'author precisa ser um objeto com name.'):
        r.conferir(not set(autor) - {'name', 'email', 'url'}, 'plugin_author_wrong_type',
                   'author aceita só name, email e url.')
        if r.conferir('name' in autor, 'plugin_developer_missing', 'author.name é obrigatório.'):
            conferir_texto(r, autor['name'], 'author.name', 'plugin_author_name', 120)
        if 'email' in autor:
            conferir_texto(r, autor['email'], 'author.email', 'plugin_author_email', 320)
        if 'url' in autor:
            conferir_url(r, autor['url'], 'author.url', 'plugin_author_url', 2048)
    if 'homepage' in m:
        conferir_url(r, m['homepage'], 'homepage', 'plugin_homepage', 2048)
    for campo in ('repository', 'license'):
        if campo in m:
            r.conferir(isinstance(m[campo], str) and bool(m[campo].strip()), 'plugin_manifest_field_wrong_type',
                       f'{campo} precisa ser texto.')
    if 'keywords' in m:
        palavras = m['keywords']
        r.conferir(isinstance(palavras, list) and all(isinstance(p, str) and p.strip() for p in palavras),
                   'plugin_keywords_wrong_type', 'keywords precisa ser uma lista de textos.')
        r.conferir(isinstance(palavras, list) and len(palavras) <= 25, 'plugin_keywords_too_many',
                   'No envio público, até 25 palavras-chave.')
    return m


def conferir_interface(r: Relatorio, raiz: Path, interface):
    if not r.conferir(isinstance(interface, dict), 'plugin_interface_wrong_type',
                      'extensions.com.openai.interface precisa ser um objeto.'):
        return
    conferir_texto(r, interface.get('displayName'), 'displayName', 'submission_display_name', 30)
    conferir_texto(r, interface.get('shortDescription'), 'shortDescription', 'submission_subtitle', 30)
    conferir_texto(r, interface.get('longDescription'), 'longDescription', 'submission_description', 4000, multilinha=True)
    conferir_texto(r, interface.get('developerName'), 'developerName', 'submission_developer_name', 80)
    categoria = interface.get('category')
    r.conferir(categoria in CATEGORIAS, 'plugin_category_unknown',
               f'category "{categoria}" não é um dos títulos aceitos: {sorted(CATEGORIAS)}')
    capacidades = interface.get('capabilities', [])
    if r.conferir(isinstance(capacidades, list), 'plugin_capabilities_wrong_type', 'capabilities precisa ser uma lista.'):
        r.conferir(len(capacidades) <= 20, 'plugin_capabilities_too_many', 'capabilities passa de 20.')
        for i, c in enumerate(capacidades):
            r.conferir(isinstance(c, str) and bool(c.strip()) and len(c) <= 120 and uma_linha(c) and texto_aceito(c),
                       'plugin_capability_invalid', f'capabilities[{i}] precisa ter de 1 a 120 caracteres numa linha.')
    for campo, codigo in URLS_DA_FICHA.items():
        conferir_url(r, interface.get(campo), campo, codigo, 1024, obrigatorio=True)
    pedidos = interface.get('defaultPrompt')
    if pedidos is not None:
        if r.conferir(isinstance(pedidos, (str, list)), 'plugin_default_prompt_wrong_type',
                      'defaultPrompt precisa ser texto ou lista de textos.'):
            lista = [pedidos] if isinstance(pedidos, str) else pedidos
            r.conferir(len(lista) <= 3, 'plugin_default_prompt_too_many', 'defaultPrompt passa de 3 pedidos.')
            normalizados = []
            for i, p in enumerate(lista):
                if not r.conferir(isinstance(p, str), 'plugin_default_prompt_entry_wrong_type', f'defaultPrompt[{i}] não é texto.'):
                    continue
                r.conferir(bool(p.strip()), 'plugin_default_prompt_empty', f'defaultPrompt[{i}] vazio.')
                r.conferir(len(p) <= 128, 'plugin_default_prompt_too_long', f'defaultPrompt[{i}] passa de 128 caracteres.')
                r.conferir(uma_linha(p) and texto_aceito(p), 'plugin_default_prompt_character_unsupported',
                           f'defaultPrompt[{i}] precisa caber numa linha.')
                r.conferir(not re.search(r'(^|\s)@\w', p), 'plugin_default_prompt_mention',
                           f'defaultPrompt[{i}] cita um servidor com @.')
                normalizados.append(' '.join(unicodedata.normalize('NFKC', p).split()).casefold())
            r.conferir(len(set(normalizados)) == len(normalizados), 'plugin_default_prompt_duplicate',
                       'defaultPrompt tem pedidos repetidos.')
    for campo, fundo, codigo in (('brandColor', '#FFFFFF', 'plugin_brand_color'),
                                 ('brandColorDark', '#212121', 'plugin_brand_color_dark')):
        if campo in interface:
            cor = interface[campo]
            if r.conferir(isinstance(cor, str) and bool(COR.match(cor)), f'{codigo}_format', f'{campo} precisa ser #RRGGBB.'):
                r.conferir(contraste(cor, fundo) >= 2, f'{codigo}_contrast', f'{campo} tem contraste menor que 2:1 com {fundo}.')
    r.conferir('logo' in interface, 'plugin_logo_path_missing', 'interface.logo é obrigatório.')
    r.conferir('composerIcon' in interface, 'plugin_composer_icon_path_missing', 'interface.composerIcon é obrigatório.')
    for campo in IMAGENS_DA_FICHA:
        if campo in interface:
            conferir_imagem(r, raiz, campo, interface[campo], 256 if campo.startswith('logo') else 48)


def conferir_casos(r: Relatorio, casos, ferramentas: set[str] | None):
    if not r.conferir(isinstance(casos, dict), 'review_test_cases_wrong_type', 'test_cases precisa ser um objeto.'):
        return
    positivos, negativos = casos.get('positive'), casos.get('negative')
    r.conferir(set(casos) <= {'positive', 'negative'}, 'review_test_cases_field_unsupported',
               'test_cases aceita só positive e negative.')
    if not r.conferir(isinstance(positivos, list) and isinstance(negativos, list), 'review_test_cases_wrong_type',
                      'test_cases precisa das duas listas, positive e negative.'):
        return
    r.conferir(len(positivos) == 5, 'review_test_cases_count', f'{len(positivos)} casos positivos; o envio exige 5.')
    r.conferir(len(negativos) == 3, 'review_test_cases_count', f'{len(negativos)} casos negativos; o envio exige 3.')
    permitidos = {'description', 'prompt', 'tools_triggered', 'expected_behavior', 'file_attachment_urls',
                  'expected_output_url'}
    for tipo, lista in (('positive', positivos), ('negative', negativos)):
        for i, caso in enumerate(lista):
            onde = f'test_cases.{tipo}[{i}]'
            if not r.conferir(isinstance(caso, dict), 'review_test_case_wrong_type', f'{onde} precisa ser um objeto.'):
                continue
            r.conferir(not set(caso) - permitidos, 'review_test_case_field_unsupported',
                       f'{onde}: campos fora da lista ({sorted(set(caso) - permitidos)}).')
            obrigatorios = ['description', 'prompt'] + (['tools_triggered', 'expected_behavior'] if tipo == 'positive' else [])
            for campo in obrigatorios:
                valor = caso.get(campo)
                r.conferir(isinstance(valor, str) and bool(valor.strip()), 'review_test_case_field_required',
                           f'{onde}.{campo} precisa ser texto (não lista).')
            r.conferir(len(caso.get('description') or '') <= 4000, 'review_test_case_description_too_long',
                       f'{onde}.description passa de 4.000 caracteres.')
            for url in caso.get('file_attachment_urls', []) or []:
                r.conferir(url_https(url), 'review_test_case_url_format', f'{onde}: anexo fora de https.')
            if 'expected_output_url' in caso:
                r.conferir(url_https(caso['expected_output_url']), 'review_test_case_url_format', f'{onde}: resultado fora de https.')
            if tipo == 'positive' and ferramentas is not None and isinstance(caso.get('tools_triggered'), str):
                citadas = [t.strip() for t in caso['tools_triggered'].split(',') if t.strip()]
                faltam = [t for t in citadas if t not in ferramentas]
                r.conferir(not faltam, 'review_test_case_tool_unknown', f'{onde}: o servidor não tem {faltam}.')


def conferir_extensao_openai(r: Relatorio, raiz: Path, m: dict, servidores: dict, ferramentas):
    extensoes = m.get('extensions')
    if not r.conferir(isinstance(extensoes, dict) and isinstance(extensoes.get('com.openai'), dict),
                      'plugin_openai_extension_missing', 'Falta extensions.com.openai no plugin.json.'):
        return
    for ns, valor in extensoes.items():
        r.conferir(isinstance(valor, dict), 'plugin_extension_wrong_type', f'extensions.{ns} precisa ser um objeto.')
    o = extensoes['com.openai']
    desconhecidos = sorted(set(o) - CAMPOS_DO_OPENAI)
    r.conferir(not desconhecidos, 'plugin_openai_field_unknown', f'Campos desconhecidos em extensions.com.openai: {desconhecidos}',
               'aviso')
    r.conferir(o.get('apps') is None, 'app_configuration_excluded', 'O envio público não aceita apps nem .app.json.')
    r.conferir('hooks' not in o, 'lifecycle_hooks_excluded', 'O envio público não aceita hooks.')
    if 'requires_local_executor' in o:
        r.conferir(isinstance(o['requires_local_executor'], bool), 'plugin_requires_local_executor_wrong_type',
                   'requires_local_executor precisa ser true ou false.')
        if o['requires_local_executor'] is True:
            r.infos.append('requires_local_executor: true (o diretório marca "Desktop only"; se o portal recusar o campo, '
                           'a OpenAI libera a organização)')
    if 'onboardingSkill' in o:
        caminho = o['onboardingSkill']
        r.conferir(isinstance(caminho, str) and caminho.startswith('./skills/') and caminho.endswith('/SKILL.md')
                   and (raiz / caminho).is_file(), 'plugin_onboarding_skill_missing',
                   'onboardingSkill precisa apontar para ./skills/<nome>/SKILL.md que existe.')
    conferir_interface(r, raiz, o.get('interface'))
    proibidas = procurar_chaves(m, {'test_credentials', 'reviewer_instructions', 'clientSecret', 'client_secret'})
    r.conferir(not proibidas, 'review_credentials_in_package',
               f'Credencial ou instrução de revisor no pacote ({proibidas}): use o formulário do portal.')
    revisao = o.get('review', {})
    if r.conferir(isinstance(revisao, dict), 'review_wrong_type', 'review precisa ser um objeto.'):
        casos = revisao.get('test_cases')
        por_servidor = [n for n, s in servidores.items()
                        if isinstance(s, dict) and isinstance(s.get('extensions', {}).get('com.openai', {}), dict)
                        and 'review' in s.get('extensions', {}).get('com.openai', {})]
        if casos is not None:
            r.conferir(len(servidores) == 1, 'review_test_cases_server_count',
                       'Casos no plugin.json só valem com exatamente um servidor MCP.')
            r.conferir(not por_servidor, 'review_test_cases_combined',
                       'Casos no plugin.json e no mcp.json ao mesmo tempo não são aceitos.')
            conferir_casos(r, casos, ferramentas)
        elif servidores and not por_servidor:
            r.conferir(False, 'review_test_cases_missing', 'Sem casos de revisão: o envio com MCP exige 5 positivos e 3 negativos.',
                       'pendente')
        demo = revisao.get('demo_recording_url')
        if demo is None:
            r.conferir(not servidores, 'review_demo_recording_missing',
                       'Falta review.demo_recording_url: o vídeo de demonstração é exigido no envio para revisão.',
                       'pendente')
        else:
            r.conferir(url_https(demo), 'review_demo_recording_url_format', 'demo_recording_url precisa ser https.')
        if 'commerce' in revisao:
            r.conferir(isinstance(revisao['commerce'], bool), 'review_commerce_wrong_type', 'commerce precisa ser booleano.')
        if 'commerce_description' in revisao:
            conferir_texto(r, revisao['commerce_description'], 'commerce_description', 'review_commerce_description',
                           4000, multilinha=True)
        if 'prompts' in revisao:
            pedidos = revisao['prompts']
            r.conferir(isinstance(pedidos, list) and len(pedidos) <= 20 and all(
                isinstance(p, str) and p.strip() and len(p) <= 4000 for p in pedidos), 'review_prompts_invalid',
                'review.prompts: até 20 textos não vazios de até 4.000 caracteres.')
    publicacao = o.get('publication', {})
    if r.conferir(isinstance(publicacao, dict), 'publication_wrong_type', 'publication precisa ser um objeto.'):
        r.conferir(not ({'commerce', 'commerce_description'} & set(publicacao)), 'publication_commerce_misplaced',
                   'commerce fica em review, não em publication.')
        notas = publicacao.get('release_notes')
        if notas is None:
            r.conferir(False, 'publication_release_notes_missing', 'Faltam as notas da versão (release_notes).', 'pendente')
        else:
            conferir_texto(r, notas, 'release_notes', 'publication_release_notes', 4000, multilinha=True)
        if 'countries' in publicacao:
            paises = publicacao['countries']
            r.conferir(isinstance(paises, list) and all(isinstance(p, str) and re.fullmatch(r'[A-Z]{2}', p) for p in paises),
                       'publication_countries_invalid', 'countries: lista de códigos de país em maiúsculas, como BR e US.')
        else:
            r.conferir(False, 'publication_countries_missing',
                       'Sem publication.countries: os países ficam para escolher no portal (o dono decide).', 'pendente')
        traducoes = publicacao.get('translations')
        if traducoes is not None and r.conferir(isinstance(traducoes, dict), 'publication_translations_wrong_type',
                                                'translations precisa ser um mapa de idioma para textos.'):
            for idioma, t in traducoes.items():
                r.conferir(bool(str(idioma).strip()), 'publication_translation_locale_empty', 'Idioma vazio em translations.')
                r.conferir(idioma != 'en-US', 'publication_translation_en_us',
                           'translations não precisa de en-US: o inglês fica nos campos da ficha.', 'aviso')
                if not r.conferir(isinstance(t, dict) and set(t) <= {'subtitle', 'description'},
                                  'publication_translation_wrong_type', f'translations.{idioma}: só subtitle e description.'):
                    continue
                if t.get('subtitle') is not None:
                    conferir_texto(r, t['subtitle'], f'translations.{idioma}.subtitle', 'publication_translation_subtitle', 30)
                if t.get('description') is not None:
                    conferir_texto(r, t['description'], f'translations.{idioma}.description',
                                   'publication_translation_description', 4000, multilinha=True)


def conferir_mcp(r: Relatorio, raiz: Path) -> dict:
    arquivo = raiz / 'mcp.json'
    if not arquivo.exists():
        r.infos.append('Sem mcp.json: pacote só de skills.')
        return {}
    dados = ler_json(r, arquivo, 'mcp_manifest')
    if dados is None:
        return {}
    r.conferir(dados.get('$schema') == SCHEMA_MCP, 'mcp_manifest_schema', f'mcp.json precisa de "$schema": "{SCHEMA_MCP}".')
    r.conferir(set(dados) <= {'$schema', 'mcpServers'}, 'mcp_manifest_field_unsupported', 'mcp.json aceita só $schema e mcpServers.')
    segredos = procurar_chaves(dados, {'clientSecret', 'client_secret', 'test_credentials', 'apiKey', 'token'})
    r.conferir(not segredos, 'mcp_auth_secret_in_package', f'Segredo no mcp.json ({segredos}): o portal pede no formulário.')
    servidores = dados.get('mcpServers')
    if not r.conferir(servidores is not None, 'mcp_servers_missing', 'Falta mcpServers no mcp.json.') or \
            not r.conferir(isinstance(servidores, dict), 'mcp_servers_wrong_type', 'mcpServers precisa ser um objeto.'):
        return {}
    for nome, s in servidores.items():
        r.conferir(bool(nome.strip()), 'mcp_server_name_empty', 'Servidor MCP sem nome.')
        if not r.conferir(isinstance(s, dict), 'mcp_server_wrong_type', f'mcpServers.{nome} precisa ser um objeto.'):
            continue
        r.conferir(set(s) <= {'type', 'url', 'headers', 'extensions'}, 'mcp_server_field_unsupported',
                   f'mcpServers.{nome}: campos fora do formato portátil ({sorted(set(s) - {"type", "url", "headers", "extensions"})}); '
                   'auth vai em extensions.com.openai.auth e server_url não existe.')
        tipo = s.get('type')
        if tipo == 'stdio' or 'command' in s:
            r.conferir(False, 'mcp_configuration_excluded',
                       f'mcpServers.{nome} é local (stdio): só organização liberada pela OpenAI envia MCP local.')
            continue
        r.conferir(tipo in ('streamable-http', 'sse'), 'mcp_server_type',
                   f'mcpServers.{nome}: type "streamable-http" (o "http" antigo vira "streamable-http").')
        r.conferir(url_https(s.get('url')), 'mcp_server_url_format', f'mcpServers.{nome}: url precisa ser https pública.')
        r.conferir(not s.get('headers'), 'mcp_server_headers_rejected',
                   f'mcpServers.{nome}: o envio público recusa headers com valor (nada de token no pacote).')
        extensoes = s.get('extensions', {})
        if 'extensions' in s:
            r.avisos.append(('mcp_server_extensions_outside_schema',
                             f'mcpServers.{nome}.extensions: a OpenAI lê a autenticação daqui, mas o mcp.schema.json do '
                             'Agent Plugins 1.0.0 não lista o campo; outro cliente Agent Plugins pode ignorar o servidor.'))
        if not r.conferir(isinstance(extensoes, dict), 'mcp_server_extensions_wrong_type', 'extensions precisa ser um objeto.'):
            continue
        openai = extensoes.get('com.openai', {})
        if not r.conferir(isinstance(openai, dict), 'mcp_server_extensions_wrong_type', 'extensions.com.openai precisa ser um objeto.'):
            continue
        conferir_auth(r, nome, openai)
    return servidores


def conferir_auth(r: Relatorio, nome: str, openai: dict):
    if 'tunnelId' in openai:
        r.conferir(isinstance(openai['tunnelId'], str) and bool(re.fullmatch(r'tunnel_[a-z0-9]{32}', openai['tunnelId'])),
                   'mcp_tunnel_id_format', f'{nome}: tunnelId inválido.')
    if 'urlTemplates' in openai:
        modelos = openai['urlTemplates']
        r.conferir(isinstance(modelos, list) and modelos and len(set(modelos)) == len(modelos)
                   and all(isinstance(t, str) and t.startswith('https://') and re.search(r'\{[A-Za-z][A-Za-z0-9_]*\}', t)
                           for t in modelos), 'mcp_url_templates_invalid', f'{nome}: urlTemplates inválido.')
    auth = openai.get('auth')
    if auth is None:
        r.infos.append(f'{nome}: sem auth no mcp.json; o portal descobre pelo servidor.')
        return
    if not r.conferir(isinstance(auth, dict), 'mcp_auth_wrong_type', f'{nome}: auth precisa ser um objeto.'):
        return
    tipo = auth.get('type')
    r.conferir(tipo in ('none', 'oauth', 'mixed', 'api_key'), 'mcp_auth_type', f'{nome}: auth.type "{tipo}" não existe.')
    r.conferir(tipo != 'api_key', 'mcp_auth_api_key_unsupported',
               f'{nome}: o portal não tem fluxo de chave de API; a conexão não fecha.', 'aviso')
    if tipo in ('oauth', 'mixed') and 'client' in auth:
        cliente = auth['client']
        if r.conferir(isinstance(cliente, dict) and cliente.get('mode') in ('provided', 'dcr', 'cimd'), 'mcp_auth_client_mode',
                      f'{nome}: auth.client.mode precisa ser provided, dcr ou cimd.'):
            if cliente['mode'] in ('dcr', 'cimd'):
                r.conferir(set(cliente) == {'mode'}, 'mcp_auth_client_fields', f'{nome}: dcr e cimd aceitam só mode.')
            else:
                r.conferir(isinstance(cliente.get('clientId'), str) and bool(cliente['clientId'].strip()),
                           'mcp_auth_client_id_required', f'{nome}: provided precisa de clientId.')
                metodo = cliente.get('tokenEndpointAuthMethod')
                r.conferir(metodo in (None, 'none', 'client_secret_post', 'client_secret_basic', 'private_key_jwt'),
                           'mcp_auth_token_method', f'{nome}: tokenEndpointAuthMethod inválido.')
    r.conferir('useCimd' not in auth and 'clientId' not in auth, 'mcp_auth_client_fields',
               f'{nome}: use auth.client.mode; nada de useCimd ou clientId direto em auth.')
    for campo in ('baseScopes', 'defaultScopes', 'oidcScopesSupported'):
        if campo in auth:
            r.conferir(isinstance(auth[campo], list) and all(isinstance(s, str) and s.strip() for s in auth[campo]),
                       'mcp_auth_scopes', f'{nome}: {campo} precisa ser uma lista de textos.')
    if 'oidcEnabled' in auth:
        r.conferir(isinstance(auth['oidcEnabled'], bool), 'mcp_auth_oidc', f'{nome}: oidcEnabled precisa ser booleano.')
    for campo in ('authorizationUrl', 'tokenUrl', 'registrationUrl', 'authorizationServerBase', 'resource',
                  'oidcConfigurationUrl', 'oidcUserinfoEndpoint'):
        if campo in auth:
            valor = auth[campo]
            r.conferir(isinstance(valor, str) and re.match(r'^https?://[^/@#]+', valor) is not None and '#' not in valor,
                       'mcp_auth_endpoint', f'{nome}: {campo} precisa ser http(s) absoluto, sem login nem fragmento.')
    if tipo == 'api_key' or 'headerScheme' in auth:
        esquema = auth.get('headerScheme')
        r.conferir(esquema in ('bearer', 'basic', 'custom_header'), 'mcp_auth_header_scheme', f'{nome}: headerScheme inválido.')
        r.conferir(('headerName' in auth) == (esquema == 'custom_header'), 'mcp_auth_header_name',
                   f'{nome}: headerName só com custom_header.')


def cabecalho_yaml(texto: str):
    if not texto.startswith('---\n') and not texto.startswith('---\r\n'):
        return None, 'skill_frontmatter_missing'
    fim = re.search(r'\r?\n---[ \t]*(\r?\n|$)', texto[3:])
    if not fim:
        return None, 'skill_frontmatter_unclosed'
    bruto = texto[3:3 + fim.start()]
    corpo = texto[3 + fim.end():]
    try:
        dados = yaml.safe_load(bruto)
    except yaml.YAMLError:
        return None, 'skill_frontmatter_yaml_malformed'
    if not isinstance(dados, dict):
        return None, 'skill_frontmatter_wrong_type'
    return (dados, corpo), None


def conferir_skills(r: Relatorio, raiz: Path, nome_do_plugin: str):
    pasta = raiz / 'skills'
    if not pasta.is_dir():
        r.infos.append('Sem skills/.')
        return 0
    if yaml is None:
        r.avisos.append(('yaml_missing', 'PyYAML não instalado: os cabeçalhos das skills não foram conferidos.'))
        return 0
    validas, nomes = 0, {}
    for item in sorted(pasta.iterdir()):
        rel = item.relative_to(raiz).as_posix()
        if item.is_symlink():
            r.avisos.append(('skill_symlink_ignored', f'{rel} é link simbólico e não vira skill.'))
            continue
        if item.is_file():
            if item.name != '.DS_Store':
                r.avisos.append(('skill_file_ignored', f'{rel} está solto em skills/ e não vira skill.'))
            continue
        if not r.conferir(not item.name.startswith('.'), 'skill_directory_hidden', f'{rel}: pasta de skill começa com ponto.'):
            continue
        manifesto = item / 'SKILL.md'
        if not manifesto.exists():
            aninhados = [p.relative_to(raiz).as_posix() for p in item.rglob('SKILL.md')]
            r.conferir(not aninhados, 'skill_manifest_nested', f'{rel}: SKILL.md fora do primeiro nível ({aninhados[:2]}).')
            r.conferir(False, 'skill_manifest_missing', f'{rel}: falta SKILL.md.')
            continue
        if not r.conferir(manifesto.is_file() and not manifesto.is_symlink(), 'skill_manifest_not_regular_file',
                          f'{rel}/SKILL.md precisa ser um arquivo comum.'):
            continue
        r.conferir(manifesto.stat().st_size <= MIB, 'skill_manifest_too_large', f'{rel}/SKILL.md passa de 1 MiB.')
        try:
            texto = manifesto.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            r.conferir(False, 'skill_manifest_invalid_utf8', f'{rel}/SKILL.md não é UTF-8.')
            continue
        lido, erro = cabecalho_yaml(texto)
        if not r.conferir(erro is None, erro or 'skill_frontmatter', f'{rel}/SKILL.md: cabeçalho YAML inválido ({erro}).'):
            continue
        dados, corpo = lido
        nome, descricao = dados.get('name'), dados.get('description')
        if r.conferir(isinstance(nome, str) and bool(nome.strip()), 'skill_name_missing', f'{rel}: name vazio ou ausente.'):
            r.conferir(texto_aceito(nome) and uma_linha(nome), 'skill_name_character_unsupported', f'{rel}: name com caractere não aceito.')
            r.conferir(nome == item.name, 'skill_name_directory_mismatch', f'{rel}: name "{nome}" diferente da pasta.')
            r.conferir(len(f'{nome_do_plugin}:{nome}') <= 64, 'skill_identity_too_long',
                       f'{nome_do_plugin}:{nome} passa de 64 caracteres.')
            r.conferir(nome not in nomes, 'skill_identity_duplicate', f'{rel}: name repetido com {nomes.get(nome)}.')
            nomes[nome] = rel
        if r.conferir(isinstance(descricao, str) and bool(descricao.strip()), 'skill_description_missing',
                      f'{rel}: description vazio ou ausente.'):
            r.conferir(len(descricao) <= 1024, 'skill_description_too_long', f'{rel}: description com {len(descricao)} caracteres.')
            r.conferir(texto_aceito(descricao, multilinha=True), 'skill_description_character_unsupported',
                       f'{rel}: description com caractere não aceito.')
        r.conferir(bool(corpo.strip()), 'skill_body_empty', f'{rel}: SKILL.md sem instruções.')
        r.conferir('metadata' not in dados, 'skill_metadata_ignored',
                   f'{rel}: metadata no SKILL.md não configura a interface (só agents/openai.yaml).', 'aviso')
        conferir_agente_da_skill(r, item)
        validas += 1
    r.conferir(validas > 0, 'plugin_runtime_surface_missing', 'O ZIP precisa de pelo menos uma skill válida.')
    r.infos.append(f'Skills válidas: {validas} ({", ".join(sorted(nomes))})')
    return validas


def conferir_agente_da_skill(r: Relatorio, pasta: Path):
    arquivo = pasta / 'agents' / 'openai.yaml'
    rel = arquivo.relative_to(pasta.parent.parent).as_posix()
    if not arquivo.exists():
        return
    if not r.conferir(arquivo.is_file() and not arquivo.is_symlink(), 'skill_agent_not_regular_file', f'{rel} precisa ser arquivo comum.'):
        return
    try:
        dados = yaml.safe_load(arquivo.read_text(encoding='utf-8'))
    except UnicodeDecodeError:
        r.conferir(False, 'skill_agent_invalid_utf8', f'{rel} não é UTF-8.')
        return
    except yaml.YAMLError:
        r.conferir(False, 'skill_agent_yaml_malformed', f'{rel}: YAML inválido.')
        return
    if not r.conferir(isinstance(dados, dict), 'skill_agent_top_level_wrong_type', f'{rel} precisa ser um mapa.'):
        return
    interface = dados.get('interface')
    if r.conferir(interface is not None, 'skill_agent_interface_missing', f'{rel}: falta interface.') and \
            r.conferir(isinstance(interface, dict), 'skill_agent_interface_wrong_type', f'{rel}: interface precisa ser um mapa.'):
        for campo in ('display_name', 'short_description'):
            valor = interface.get(campo)
            r.conferir(isinstance(valor, str) and bool(valor.strip()), f'skill_agent_{campo}_missing', f'{rel}: falta {campo}.')
        for campo in ('icon_small', 'icon_large'):
            if campo in interface:
                valor = interface[campo]
                r.conferir(isinstance(valor, str) and bool(valor.strip()) and not valor.startswith('/') and
                           (pasta / valor).is_file(), f'skill_agent_{campo}_wrong_type', f'{rel}: {campo} aponta para arquivo inexistente.')
        if 'brand_color' in interface:
            r.conferir(isinstance(interface['brand_color'], str) and bool(COR.match(interface['brand_color'])),
                       'skill_agent_brand_color_format', f'{rel}: brand_color precisa ser #RRGGBB.')
        if 'default_prompt' in interface:
            valor = interface['default_prompt']
            r.conferir(isinstance(valor, str) and bool(valor.strip()), 'skill_agent_default_prompt_wrong_type',
                       f'{rel}: default_prompt precisa ser um texto.')
    politica = dados.get('policy')
    if politica is not None and r.conferir(isinstance(politica, dict), 'skill_agent_policy_wrong_type',
                                           f'{rel}: policy precisa ser um mapa.'):
        produtos = politica.get('products')
        implicita = politica.get('allow_implicit_invocation')
        r.conferir(set(politica) <= {'products', 'allow_implicit_invocation'}
                   and (produtos is None or (isinstance(produtos, list) and set(produtos) <= {'CHAT', 'CODEX', 'HERMES'}))
                   and (implicita is None or isinstance(implicita, bool)),
                   'skill_agent_allow_implicit_invocation_wrong_type', f'{rel}: policy só com products e allow_implicit_invocation.')
    dependencias = dados.get('dependencies')
    if dependencias is not None and r.conferir(isinstance(dependencias, dict), 'skill_agent_dependencies_wrong_type',
                                               f'{rel}: dependencies precisa ser um mapa.'):
        r.conferir(set(dependencias) <= {'tools'}, 'skill_agent_dependency_unsupported', f'{rel}: só dependencies.tools.')
        externos = [d.get('url') for d in dependencias.get('tools', []) or [] if isinstance(d, dict) and d.get('type') == 'mcp']
        externos = [u for u in externos if u and 'criadorestrategista.com.br' not in u]
        if externos:
            r.avisos.append(('skill_external_mcp_dependency',
                             f'{rel} depende de MCP de terceiros ({", ".join(externos)}); a revisão pode perguntar.'))


def tamanho_dos_pacotes_de_skill(raiz: Path) -> list[str]:
    saida = []
    for item in sorted((raiz / 'skills').iterdir()) if (raiz / 'skills').is_dir() else []:
        if not item.is_dir() or item.name.startswith('.'):
            continue
        memoria = io.BytesIO()
        with zipfile.ZipFile(memoria, 'w', zipfile.ZIP_DEFLATED) as z:
            for arquivo in sorted(item.rglob('*')):
                if arquivo.is_file():
                    z.write(arquivo, arquivo.relative_to(raiz / 'skills').as_posix())
        saida.append(f'{item.name} {memoria.tell() / MIB:.1f} MiB')
    return saida


# --- Servidor (opcional) --------------------------------------------------------------------------------------

def ferramentas_do_servidor(webapp: Path, r: Relatorio) -> set[str]:
    """Nomes registrados com registerTool em webapp/src, e as três anotações de cada um."""
    textos = {f: f.read_text(encoding='utf-8') for f in (webapp / 'src').rglob('*.ts*')}
    constantes = {}
    for texto in textos.values():
        for nome, corpo in re.findall(r'const ([A-Z_]+) = (\{[^}]*\})', texto):
            constantes.setdefault(nome, corpo)

    def resolver(corpo: str, profundidade=0) -> str:
        if profundidade > 5:
            return corpo
        for base in re.findall(r'\.\.\.([A-Z_]+)', corpo):
            corpo += resolver(constantes.get(base, ''), profundidade + 1)
        return corpo

    nomes, sem_anotacao = set(), []
    for texto in textos.values():
        achados = list(re.finditer(r'registerTool\(\s*["\'`]([a-z][a-z0-9_]*)["\'`]', texto))
        for i, m in enumerate(achados):
            nomes.add(m.group(1))
            trecho = texto[m.end():achados[i + 1].start() if i + 1 < len(achados) else len(texto)]
            a = re.search(r'annotations:\s*([A-Z_]+|\{[^}]*\})', trecho)
            corpo = '' if not a else resolver(constantes.get(a.group(1), '') if a.group(1)[0] != '{' else a.group(1))
            if not all(re.search(rf'{dica}:\s*(true|false)', corpo) for dica in ('readOnlyHint', 'openWorldHint', 'destructiveHint')):
                sem_anotacao.append(m.group(1))
    r.conferir(bool(nomes), 'webapp_tools_missing', f'Nenhuma ferramenta achada em {webapp}/src.')
    r.conferir(not sem_anotacao, 'annotations_required',
               f'Ferramentas sem readOnlyHint, openWorldHint e destructiveHint explícitos: {sorted(sem_anotacao)}')
    r.infos.append(f'Servidor: {len(nomes)} ferramentas, {len(nomes) - len(sem_anotacao)} com as três anotações.')
    return nomes


def conferir_links(r: Relatorio, m: dict):
    interface = m.get('extensions', {}).get('com.openai', {}).get('interface', {})
    publicador = ('Criadores do Futuro', 'Action Criação Digital')
    for campo in URLS_DA_FICHA:
        url = interface.get(campo)
        if not url:
            continue
        try:
            pedido = urllib.request.Request(url, headers={'User-Agent': 'validar-pacote/1.0'})
            with urllib.request.urlopen(pedido, timeout=25) as resposta:
                final, status = resposta.geturl(), resposta.status
                pagina = resposta.read(600_000).decode('utf-8', 'ignore')
        except Exception as erro:  # noqa: BLE001 - qualquer falha de rede vira o mesmo aviso
            r.conferir(False, 'listing_url_unreachable', f'{campo}: {url} não abriu ({erro}).')
            continue
        r.conferir(status == 200, 'listing_url_status', f'{campo}: {url} respondeu {status}.')
        r.conferir('/entrar' not in final and '/login' not in final, 'listing_url_requires_login',
                   f'{campo}: {url} manda para o login ({final}).')
        r.conferir(any(p in pagina for p in publicador), 'listing_url_publisher',
                   f'{campo}: {url} não cita o publicador ({" ou ".join(publicador)}).')
        r.infos.append(f'{campo}: {url} abriu ({status}) e cita o publicador.')


# --- Principal ------------------------------------------------------------------------------------------------

def conferir(caminho: Path, webapp: Path | None = None, links: bool = False) -> Relatorio:
    r = Relatorio()
    with tempfile.TemporaryDirectory() as temporario:
        if caminho.is_file():
            raiz = conferir_zip(r, caminho, Path(temporario))
            if raiz is None:
                return r
        else:
            raiz = caminho
        if not r.conferir(raiz.is_dir(), 'plugin_root_missing', f'{raiz} não é uma pasta.'):
            return r
        conferir_arquivos(r, raiz)
        m = conferir_manifesto(r, raiz)
        servidores = conferir_mcp(r, raiz)
        ferramentas = ferramentas_do_servidor(webapp, r) if webapp else None
        if m is not None:
            conferir_extensao_openai(r, raiz, m, servidores, ferramentas)
            conferir_skills(r, raiz, m.get('name') or '')
            if links:
                conferir_links(r, m)
        r.infos.append('Pacote de cada skill compactado: ' + ', '.join(tamanho_dos_pacotes_de_skill(raiz)))
    return r


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('caminho', type=Path, help='o .zip de envio ou a pasta do pacote')
    p.add_argument('--webapp', type=Path, help='pasta do site (com src/) para conferir ferramentas e anotações')
    p.add_argument('--links', action='store_true', help='abre os quatro links da ficha')
    a = p.parse_args(argv)
    r = conferir(a.caminho, a.webapp, a.links)
    for linha in r.infos:
        print(f'  info      {linha}')
    for codigo, msg in r.pendentes:
        print(f'  pendente  {codigo}: {msg}')
    for codigo, msg in r.avisos:
        print(f'  aviso     {codigo}: {msg}')
    for codigo, msg in r.erros:
        print(f'  ERRO      {codigo}: {msg}')
    print(f'Resultado: {len(r.regras)} regras em {r.conferencias} conferências, {len(r.erros)} erros, '
          f'{len(r.avisos)} avisos, {len(r.pendentes)} pendentes.')
    return 1 if r.erros else 0


if __name__ == '__main__':
    sys.exit(main())
