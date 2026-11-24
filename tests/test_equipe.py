"""A equipe da Sofia: agentes, skill, comandos e o espelho do método batem com o conector.

O método mora no webapp (decisão D1 de 23/11). As referências da skill marcadas como "Cópia da peça" e o
cartas.md são gerados por `npx tsx scripts/exportar-referencias.mts <pasta-do-plugin>`, rodado no webapp; o
.espelho.json guarda o sha256 de cada arquivo gerado. Estes testes acusam edição à mão no espelho, papel sem
agente, agente que a skill não cita, ferramenta citada que o conector não tem e texto novo fora das regras.

Com a variável SOFIA_WEBAPP apontando para um checkout do webapp, a lista de ferramentas abaixo também é
comparada com as que o servidor registra.

Os testes ficam na raiz do repositório, fora do pacote: o plugin é a pasta plugin/. É o mesmo teste do plugin
sofia-estrategista-editora, com o caminho e o nome do plugin trocados. Para rodar: python3 -m unittest discover -s tests
"""
import hashlib
import json
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'plugin'
SKILL = ROOT / 'skills/sofia-estrategista'
REFERENCIAS = SKILL / 'references'

try:
    import yaml
except ImportError:  # pragma: no cover - sem o PyYAML (pip install pyyaml), os testes de cabeçalho são pulados
    yaml = None

# As ferramentas do conector na branch da equipe (registerTool em src/). Ao mudar o conector, atualize a lista
# e rode scripts/conferir-ferramentas.mjs.
FERRAMENTAS_DO_CONECTOR = set('''
buscar_no_curso cerebro_bolha cerebro_buscar cerebro_desfazer cerebro_esquecer cerebro_guardar cerebro_indice
cerebro_ler cerebro_preferencia destravar escrever_abordagem glossario kit marcar_etapa onde_estou
perfil_definir_alvo perfil_desfazer_alvo perfil_evolucao perfil_ler_da_rede perfil_listar perfil_salvar_avaliacao
perfil_salvar_leitura perfil_ver planejamento_consolidar_card planejamento_criar_card planejamento_dividir_card
planejamento_editar_card planejamento_estruturar_card planejamento_gravar planejamento_guardar_card
planejamento_juntar_duplicado planejamento_mover_card planejamento_postado planejamento_quadro
planejamento_reusar_card planejamento_salvar_pesquisa preco_e_contrato preparar_reuniao referencia_apagar
referencia_buscar referencia_editar referencia_listar referencia_salvar referencia_usar referencia_ver sofia_apagar
sofia_briefing sofia_conferir sofia_exportar sofia_grifos sofia_metodo sofia_meus_videos sofia_perfil
sofia_preparar_escrita sofia_salvar sofia_video ver_etapa ver_situacao
'''.split())
FAMILIA = re.compile(r'^(sofia|planejamento|cerebro|referencia|perfil)_[a-z0-9_]+$')

ESCRITORES = {'redator-de-hook', 'roteirista'}
REVISORES = {'revisor-o-que-nao-fazer', 'revisor-de-hook', 'revisor-de-voz', 'revisor-de-estrutura', 'revisor-de-fatos'}
AGENTES_DA_SOFIA = ESCRITORES | REVISORES | {'estrategista-de-ideias', 'especialista-em-bolha', 'pesquisador', 'critico'}
COMANDOS_DA_EQUIPE = {'ideias', 'pesquisa', 'roteiro', 'critica'}

# Arquivos escritos à mão nesta versão: valem as regras de texto do aluno e o teste da loja.
TEXTOS_NOVOS = [
    *(ROOT / 'agents' / f'{n}.md' for n in sorted(AGENTES_DA_SOFIA)),
    *(ROOT / 'commands' / f'{n}.md' for n in sorted(COMANDOS_DA_EQUIPE)),
    REFERENCIAS / 'passadas.md',
    SKILL / 'agents/openai.yaml',
]
LOJA = re.compile(
    r'você é a sofia|comece por|prefira|pergunte ao aluno|diga ao aluno|não mostre|hotmart|checkout|\bcompre\b'
    r'|zernio|metricool|apify|mcp__|—|mediana', re.I)
# A mesma regra do webapp (vicios.ts): advérbio em -mente, com as palavras que só terminam assim.
MENTE = re.compile(r'\b\w+mente\b', re.I)
NAO_SAO_ADVERBIO = {'mente', 'semente', 'sementes', 'comente', 'aumente', 'lamente', 'demente', 'clemente', 'fermente',
                    'experimente', 'alimente', 'documente', 'complemente', 'implemente', 'tormente'}
MOLDE = re.compile(r'\bnão é [^.,;:]{1,40}, é\b', re.I)


def sem_trava(texto):
    """O texto sem a linha disallowedTools do frontmatter: ela é gerada e traz o nome interno das ferramentas."""
    return re.sub(r'^disallowedTools:.*$', '', texto, flags=re.M)


def trava_esperada():
    """A trava gerada pelo webapp: as do terminal e, com os dois prefixos, as ferramentas que gravam."""
    espelho = json.loads((REFERENCIAS / '.espelho.json').read_text(encoding='utf-8'))
    nome = json.loads((ROOT / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))['name']
    prefixos = [f'mcp__plugin_{nome}_sofia-estrategista__', 'mcp__claude_ai_Sofia_Estrategista__']
    return espelho['ferramentasQueGravam'], ['Write', 'Edit', 'NotebookEdit', 'Bash', 'PowerShell', 'Agent'] + [
        p + f for p in prefixos for f in espelho['ferramentasQueGravam']]


def corpo_e_cabecalho(arquivo):
    texto = arquivo.read_text(encoding='utf-8')
    fim = texto.find('\n---', 4)
    return yaml.safe_load(texto[4:fim]), texto[fim + 4:]


def papeis_do_cartas():
    texto = (REFERENCIAS / 'cartas.md').read_text(encoding='utf-8')
    parte = texto.split('## Por papel', 1)[1].split('## As cartas, por peça', 1)[0]
    return dict(re.findall(r'^### .+? \(([a-z-]+)\)\n((?:- .+\n)+)', parte, re.M))


class EspelhoTest(unittest.TestCase):
    def test_arquivos_do_espelho_sem_edicao_a_mao(self):
        espelho = json.loads((REFERENCIAS / '.espelho.json').read_text(encoding='utf-8'))
        self.assertTrue(espelho['arquivos'])
        for relativo, sha in espelho['arquivos'].items():
            with self.subTest(arquivo=relativo):
                dados = (REFERENCIAS / relativo).read_bytes()
                self.assertEqual(hashlib.sha256(dados).hexdigest(), sha,
                                 'arquivo gerado mudou à mão: rode exportar-referencias.mts no webapp')

    def test_pecas_que_cada_papel_le_estao_no_espelho(self):
        nomes = {'sem-slop': 'sem-cara-de-ia'}
        for papel, linhas in papeis_do_cartas().items():
            for pecas in re.findall(r'peças ([^.]+)\.', linhas):
                for peca in (p.strip() for p in pecas.split(',')):
                    if peca.startswith('@'):
                        continue
                    with self.subTest(papel=papel, peca=peca):
                        self.assertTrue((REFERENCIAS / f'{nomes.get(peca, peca)}.md').exists())

    def test_referencias_citadas_pela_skill_e_pelos_agentes_existem(self):
        arquivos = [SKILL / 'SKILL.md', REFERENCIAS / 'passadas.md', *(ROOT / 'agents' / f'{n}.md' for n in AGENTES_DA_SOFIA)]
        for arquivo in arquivos:
            texto = arquivo.read_text(encoding='utf-8')
            citadas = set(re.findall(r'\]\((references/[^)#]+)\)', texto))
            citadas |= {f'references/{c}' for c in re.findall(r'`((?:[a-z-]+/)?[a-z-]+\.md)`', texto)}
            citadas |= set(re.findall(r'`skills/sofia-estrategista/(references/[^`]+)`', texto))
            for citada in citadas:
                with self.subTest(arquivo=arquivo.name, citada=citada):
                    self.assertTrue((SKILL / citada).exists())


@unittest.skipIf(yaml is None, 'PyYAML não instalado')
class EquipeTest(unittest.TestCase):
    def test_todo_papel_tem_agente(self):
        papeis = set(papeis_do_cartas())
        self.assertEqual(papeis, AGENTES_DA_SOFIA)
        for papel in papeis:
            with self.subTest(papel=papel):
                self.assertTrue((ROOT / 'agents' / f'{papel}.md').exists())

    def test_agente_busca_o_proprio_briefing(self):
        for nome in AGENTES_DA_SOFIA:
            with self.subTest(agente=nome):
                _, corpo = corpo_e_cabecalho(ROOT / 'agents' / f'{nome}.md')
                self.assertIn('`sofia_briefing`', corpo)
                self.assertIn(f'papel: "{nome}"', corpo)
                self.assertIn('references/cartas.md', corpo)
                self.assertIn('sem acesso ao conector', corpo)
                if nome in ESCRITORES:
                    self.assertIn('`sofia_conferir`', corpo)

    def test_skill_cita_todo_agente_e_os_caminhos_de_cada_app(self):
        texto = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        for nome in AGENTES_DA_SOFIA:
            with self.subTest(agente=nome):
                self.assertIn(f'`{nome}`', texto)
        for trecho in ('## A equipe e a conferência', 'sofia-estrategista:<papel>', 'entrega: "orquestrar"',
                       '`conferencia`', 'No máximo 2 rodadas', 'passou pela conferência', 'references/passadas.md',
                       'No Codex', 'Espere a equipe inteira voltar'):
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, texto)

    def test_skill_abaixo_de_500_linhas(self):
        linhas = (SKILL / 'SKILL.md').read_text(encoding='utf-8').count('\n')
        self.assertLess(linhas, 500)

    def test_piso_da_skill_igual_ao_da_peca(self):
        def sem_remissao(item):
            # A remissão final muda de nome entre a skill (arquivo) e a peça (nome de peça); a regra não muda.
            return re.sub(r'\s*(As listas estão|Veja) .*$', '', item.strip())

        skill = (SKILL / 'SKILL.md').read_text(encoding='utf-8').split('## Piso', 1)[1].split('\n## ', 1)[0]
        da_skill = [sem_remissao(i) for i in re.findall(r'^\d+\. (.+)$', skill, re.M)]
        peca = (REFERENCIAS / 'piso.md').read_text(encoding='utf-8')
        da_peca = [sem_remissao(i) for i in re.findall(r'^- \*\*P\d+\.\*\* (.+)$', peca, re.M)]
        self.assertEqual(len(da_skill), 7)
        self.assertEqual(da_skill, da_peca)


class FerramentasTest(unittest.TestCase):
    def citadas(self, arquivo):
        return {n for n in re.findall(r'`([a-z][a-z0-9_]*)`', arquivo.read_text(encoding='utf-8')) if FAMILIA.match(n)}

    def test_agentes_comandos_e_skill_so_citam_ferramentas_do_conector(self):
        arquivos = [*(ROOT / 'agents').glob('*.md'), *(ROOT / 'commands').glob('*.md'), SKILL / 'SKILL.md',
                    REFERENCIAS / 'passadas.md', REFERENCIAS / 'conector.md']
        for arquivo in arquivos:
            with self.subTest(arquivo=arquivo.relative_to(ROOT).as_posix()):
                self.assertEqual(self.citadas(arquivo) - FERRAMENTAS_DO_CONECTOR, set())

    @unittest.skipUnless(os.environ.get('SOFIA_WEBAPP'), 'sem SOFIA_WEBAPP')
    def test_lista_bate_com_o_servidor(self):
        registradas = set()
        for arquivo in Path(os.environ['SOFIA_WEBAPP'], 'src').rglob('*.ts*'):
            registradas |= set(re.findall(r'registerTool\(\s*["\'`]([a-z][a-z0-9_]*)', arquivo.read_text(encoding='utf-8')))
        self.assertEqual(FERRAMENTAS_DO_CONECTOR, registradas)


class TravaTest(unittest.TestCase):
    """Nenhum agente da equipe grava no site: só a conversa principal, com o OK do aluno (achado 9, 24/11)."""

    def test_lista_das_que_gravam_e_do_conector(self):
        gravam, _ = trava_esperada()
        self.assertTrue(gravam)
        self.assertEqual(set(gravam) - FERRAMENTAS_DO_CONECTOR, set())
        for nome in ('sofia_salvar', 'sofia_grifos', 'sofia_apagar', 'cerebro_guardar', 'cerebro_esquecer',
                     'planejamento_mover_card', 'planejamento_editar_card', 'planejamento_salvar_pesquisa',
                     'referencia_apagar', 'perfil_ler_da_rede'):
            with self.subTest(ferramenta=nome):
                self.assertIn(nome, gravam)
        for nome in ('sofia_briefing', 'sofia_conferir', 'sofia_metodo', 'sofia_video'):
            with self.subTest(ferramenta=nome):
                self.assertNotIn(nome, gravam)

    @unittest.skipIf(yaml is None, 'PyYAML não instalado')
    def test_todo_agente_tem_a_trava_completa(self):
        _, esperada = trava_esperada()
        for nome in sorted(AGENTES_DA_SOFIA):
            with self.subTest(agente=nome):
                dados, _ = corpo_e_cabecalho(ROOT / 'agents' / f'{nome}.md')
                self.assertNotIn('tools', dados)
                self.assertEqual([t.strip() for t in dados['disallowedTools'].split(',')], esperada)

    @unittest.skipUnless(os.environ.get('SOFIA_WEBAPP'), 'sem SOFIA_WEBAPP')
    def test_lista_bate_com_as_anotacoes_do_servidor(self):
        import subprocess
        codigo = ("import('./src/lib/mcp/gravacao.ts').then((m) => "
                  "console.log('GRAVAM=' + JSON.stringify(m.ferramentasQueGravam())))")
        saida = subprocess.run(['npx', 'tsx', '--eval', codigo], cwd=os.environ['SOFIA_WEBAPP'], capture_output=True,
                               text=True, env={**os.environ, 'CONVERSAS_SEGREDO': 'so-para-listar-as-ferramentas-0000000000'},
                               timeout=300)
        linha = next(l for l in saida.stdout.splitlines() if l.startswith('GRAVAM='))
        gravam, _ = trava_esperada()
        self.assertEqual(json.loads(linha[len('GRAVAM='):]), gravam, 'rode exportar-referencias.mts no webapp')


class TextoNovoTest(unittest.TestCase):
    def test_regras_de_texto_e_teste_da_loja(self):
        for arquivo in TEXTOS_NOVOS:
            texto = sem_trava(arquivo.read_text(encoding='utf-8'))
            # A regra citada entre aspas ("não é X, é Y") é o nome da regra, e não um uso dela.
            sem_citacao = re.sub(r'"[^"\n]*"', '', texto)
            nome = arquivo.relative_to(ROOT).as_posix()
            with self.subTest(arquivo=nome, regra='loja'):
                self.assertEqual(LOJA.findall(texto), [])
            with self.subTest(arquivo=nome, regra='-mente'):
                adverbios = [p for p in MENTE.findall(sem_citacao) if p.lower() not in NAO_SAO_ADVERBIO]
                self.assertEqual(adverbios, [])
            with self.subTest(arquivo=nome, regra='não é X, é Y'):
                self.assertEqual(MOLDE.findall(sem_citacao), [])


if __name__ == '__main__':
    unittest.main()
