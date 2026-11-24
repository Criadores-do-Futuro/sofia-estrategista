"""Regras de estrutura que o envio do plugin no Claude (Personalizar › Plugins) e no Codex cobram.

Fontes: claude.com/docs/plugins/build, claude.com/docs/plugins/platform-support,
code.claude.com/docs/en/skills (campos aceitos fora do Claude Code),
developers.openai.com/plugins/deploy/submission (limites do manifesto do Codex).
"""
import json
import re
import struct
import subprocess
import unittest
from pathlib import Path

# Os testes ficam na raiz do repositório, fora do pacote; o plugin é a pasta plugin/.
REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / 'plugin'

try:
    import yaml
except ImportError:  # pragma: no cover - o PyYAML vem com o requirements-motion.txt
    yaml = None

# No envio pelo claude.ai, campo fora desta lista no SKILL.md é erro e o envio falha.
# No chat, cada comando vira uma skill, então os comandos seguem a mesma lista.
CAMPOS_DE_SKILL = {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}
NOME_DE_SKILL = re.compile(r'[a-z0-9]+(-[a-z0-9]+)*')
# Campos que o Claude Code lê no agente de plugin (code.claude.com/docs/en/sub-agents, conferido em 17/11).
# permissionMode, hooks, mcpServers e initialPrompt são ignorados em agente de plugin e não entram.
CAMPOS_DE_AGENTE = {'name', 'description', 'model', 'effort', 'maxTurns', 'autoCompactWindow', 'tools',
                    'disallowedTools', 'skills', 'memory', 'background', 'omitClaudeMd', 'isolation', 'color',
                    'experimental'}
# Os agentes da equipe da Sofia herdam as ferramentas (sem `tools`), porque o nome do conector muda conforme
# ele veio do plugin ou do claude.ai (decisão D11, caminho A); a lista de proibidas tira o que grava.
AGENTES_DA_SOFIA = {'estrategista-de-ideias', 'especialista-em-bolha', 'pesquisador', 'redator-de-hook', 'roteirista',
                    'revisor-o-que-nao-fazer', 'revisor-de-hook', 'revisor-de-voz', 'revisor-de-estrutura',
                    'revisor-de-fatos', 'critico'}
ESCRITORES = {'redator-de-hook', 'roteirista'}
PROIBIDAS_AOS_AGENTES = {'Write', 'Edit', 'NotebookEdit', 'Bash', 'PowerShell', 'Agent'}
# Teste da loja: expressões recusadas em descrição de plugin, skill, comando e agente.
LOJA = re.compile(
    r'você é a sofia|comece por|prefira|pergunte ao aluno|diga ao aluno|não mostre|hotmart|checkout|\bcompre\b'
    r'|zernio|metricool|apify|mcp__|—|mediana', re.I)
# Descrições do bEditor que já tinham travessão (e, no publicar, o nome dos serviços de agendamento) antes da
# versão 0.6.0. Ficam fora até a revisão delas; arquivo novo nunca entra nesta lista.
DESCRICOES_DO_BEDITOR_A_REVER = {
    'agents/analista-de-estilo.md', 'agents/diretor.md', 'agents/enriquecedor.md', 'commands/branding.md',
    'commands/cortar.md', 'commands/dirigir.md', 'commands/editar-analise.md', 'commands/finalizar.md',
    'commands/montar.md', 'commands/motion-graficos.md', 'commands/motion.md', 'commands/plano.md',
    'commands/publicar.md', 'commands/setup.md',
}


def cabecalho(arquivo):
    texto = arquivo.read_text(encoding='utf-8')
    if not texto.startswith('---\n'):
        raise AssertionError(f'{arquivo.relative_to(ROOT)}: sem cabeçalho YAML')
    fim = texto.find('\n---', 4)
    dados = yaml.safe_load(texto[4:fim])
    if not isinstance(dados, dict):
        raise AssertionError(f'{arquivo.relative_to(ROOT)}: cabeçalho não é um mapa')
    return dados


def tamanho_do_png(arquivo):
    dados = arquivo.read_bytes()[:24]
    assert dados[:8] == b'\x89PNG\r\n\x1a\n', f'{arquivo} não é PNG'
    return struct.unpack('>II', dados[16:24])


@unittest.skipIf(yaml is None, 'PyYAML não instalado')
class CabecalhosTest(unittest.TestCase):
    def test_skills_seguem_o_padrao_aceito_no_envio(self):
        skills = sorted((ROOT / 'skills').glob('*/SKILL.md'))
        self.assertTrue(skills)
        for arquivo in skills:
            with self.subTest(arquivo=arquivo.parent.name):
                dados = cabecalho(arquivo)
                self.assertLessEqual(set(dados), CAMPOS_DE_SKILL)
                self.assertEqual(dados['name'], arquivo.parent.name)
                self.assertRegex(dados['name'], NOME_DE_SKILL)
                self.assertLessEqual(len(dados['name']), 64)
                self.assertIsInstance(dados['description'], str)
                self.assertTrue(0 < len(dados['description']) <= 1024)
                if 'compatibility' in dados:
                    self.assertLessEqual(len(str(dados['compatibility'])), 500)
                if 'metadata' in dados:
                    self.assertTrue(all(isinstance(v, str) for v in dados['metadata'].values()))

    def test_comandos_viram_skill_no_chat_sem_campo_recusado(self):
        for arquivo in sorted((ROOT / 'commands').glob('*.md')):
            with self.subTest(arquivo=arquivo.name):
                dados = cabecalho(arquivo)
                self.assertLessEqual(set(dados), CAMPOS_DE_SKILL)
                self.assertIsInstance(dados['description'], str)
                self.assertTrue(0 < len(dados['description']) <= 1024)
                self.assertRegex(arquivo.stem, NOME_DE_SKILL)

    def test_agentes_tem_cabecalho_valido(self):
        for arquivo in sorted((ROOT / 'agents').glob('*.md')):
            with self.subTest(arquivo=arquivo.name):
                dados = cabecalho(arquivo)
                self.assertEqual(dados['name'], arquivo.stem)
                self.assertIsInstance(dados['description'], str)
                self.assertLessEqual(set(dados), CAMPOS_DE_AGENTE)

    def test_agentes_da_sofia_herdam_o_conector_e_nao_gravam(self):
        for nome in sorted(AGENTES_DA_SOFIA):
            with self.subTest(agente=nome):
                dados = cabecalho(ROOT / 'agents' / f'{nome}.md')
                self.assertNotIn('tools', dados)
                proibidas = {t.strip() for t in dados['disallowedTools'].split(',')}
                self.assertLessEqual(PROIBIDAS_AOS_AGENTES, proibidas)
                self.assertIs(dados['omitClaudeMd'], True)
                self.assertEqual(dados['model'], 'inherit')
                self.assertEqual(dados['effort'], 'high' if nome in ESCRITORES else 'medium')
                self.assertIsInstance(dados['maxTurns'], int)

    def test_descricoes_passam_no_teste_da_loja(self):
        arquivos = [*(ROOT / 'skills').glob('*/SKILL.md'), *(ROOT / 'commands').glob('*.md'), *(ROOT / 'agents').glob('*.md')]
        for arquivo in sorted(arquivos):
            if arquivo.relative_to(ROOT).as_posix() in DESCRICOES_DO_BEDITOR_A_REVER:
                continue
            with self.subTest(arquivo=arquivo.relative_to(ROOT).as_posix()):
                self.assertEqual(LOJA.findall(cabecalho(arquivo)['description']), [])


class TextoDoPacoteTest(unittest.TestCase):
    def test_nenhum_markdown_cita_o_prefixo_interno_das_ferramentas(self):
        # O prefixo muda conforme o conector veio do plugin ou do claude.ai; o plugin cita só o nome curto. A
        # exceção é a linha disallowedTools dos agentes, gerada pelo webapp com os dois prefixos (a trava).
        fora = {'node_modules', 'tests', '.git'}
        achados = []
        for arquivo in ROOT.rglob('*.md'):
            if fora & set(arquivo.relative_to(ROOT).parts):
                continue
            texto = arquivo.read_text(encoding='utf-8', errors='ignore')
            if arquivo.parent.name == 'agents':
                texto = re.sub(r'^disallowedTools:.*$', '', texto, flags=re.M)
            if 'mcp__' in texto:
                achados.append(arquivo.relative_to(ROOT).as_posix())
        self.assertEqual(achados, [])


class ManifestosTest(unittest.TestCase):
    def setUp(self):
        self.claude = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())
        self.codex = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())

    def test_pasta_claude_plugin_so_tem_manifestos(self):
        # O pacote leva só o plugin.json e o ícone; o marketplace.json fica na raiz do repositório,
        # fora do plugin, para instalar pelo GitHub.
        nomes = {p.name for p in (ROOT / '.claude-plugin').iterdir() if p.name != 'types'}
        self.assertEqual(nomes, {'plugin.json', 'icon.png'})
        self.assertTrue((REPO / '.claude-plugin/marketplace.json').is_file())

    def test_icone_existe_e_e_quadrado(self):
        caminhos = {self.claude['icon'], self.codex['interface']['composerIcon'], self.codex['interface']['logo']}
        for caminho in caminhos:
            with self.subTest(caminho=caminho):
                self.assertTrue(caminho.startswith('./assets/'))
                largura, altura = tamanho_do_png(ROOT / caminho)
                self.assertEqual(largura, altura)
                self.assertTrue(48 <= largura <= 4096)

    def test_ficha_do_codex_cabe_nos_limites(self):
        ficha = self.codex['interface']
        self.assertLessEqual(len(ficha['displayName']), 30)
        self.assertLessEqual(len(ficha['shortDescription']), 30)
        self.assertLessEqual(len(ficha['longDescription']), 4000)
        self.assertLessEqual(len(ficha['developerName']), 80)
        self.assertLessEqual(len(ficha['defaultPrompt']), 3)
        self.assertTrue(all(len(p) <= 128 for p in ficha['defaultPrompt']))
        self.assertLessEqual(len(ficha['capabilities']), 20)
        self.assertTrue(all(len(c) <= 120 for c in ficha['capabilities']))
        for campo in ('websiteURL', 'supportURL', 'privacyPolicyURL', 'termsOfServiceURL'):
            self.assertTrue(ficha[campo].startswith('https://'), campo)
        self.assertLessEqual(len(self.codex['description']), 4000)

    def test_links_do_manifesto_do_claude_sao_https(self):
        for campo in ('homepage', 'supportUrl', 'privacyPolicyUrl', 'termsOfServiceUrl'):
            self.assertTrue(self.claude[campo].startswith('https://'), campo)
        self.assertTrue(self.claude['author']['url'].startswith('https://'))

    def test_caminhos_do_pacote_so_tem_caracteres_aceitos_no_envio(self):
        # O envio de plugin do Claude recusa o .zip inteiro ("Zip file contains path with
        # invalid characters") se um único caminho tiver colchete, vírgula, espaço ou acento.
        script = (REPO / 'scripts/empacotar.sh').read_text()
        itens = re.search(r'ITENS=\(\n(.*?)\n\)', script, re.S).group(1).split()
        saida = subprocess.run(['git', 'ls-files', '-z', '--', *itens], cwd=ROOT,
                               capture_output=True, check=True).stdout
        caminhos = [c.decode('utf-8') for c in saida.split(b'\0') if c]
        self.assertTrue(caminhos)
        aceito = re.compile(r'[A-Za-z0-9._/-]+')
        recusados = [c for c in caminhos if not aceito.fullmatch(c)]
        self.assertEqual(recusados, [])

    def test_conector_no_dominio_proprio(self):
        mcp = json.loads((ROOT / '.mcp.json').read_text())
        servidor = mcp['mcpServers']['sofia-estrategista']
        self.assertEqual(servidor['type'], 'http')
        self.assertEqual(servidor['url'], 'https://plataforma.criadorestrategista.com.br/api/mcp')


if __name__ == '__main__':
    unittest.main()
