"""O pacote de envio ao diretório de plugins da OpenAI (openai/ e scripts/empacotar-openai.sh).

Fontes: developers.openai.com/plugins/deploy/submission e /submission-errors, e o plugin-creator 0.1.28 da OpenAI
(prepare-plugin-submission). As regras moram em scripts/validar_pacote_openai.py; aqui ficam a ligação com o resto
do repositório e a prova de que o validador recusa o que o portal recusa.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / 'plugin'
FONTE = REPO / 'openai'

spec = importlib.util.spec_from_file_location('validar_pacote_openai', REPO / 'scripts/validar_pacote_openai.py')
validar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validar)

# O mesmo teste da loja do test_pacote.py: expressões recusadas em descrição de plugin.
LOJA = re.compile(
    r'você é a sofia|comece por|prefira|pergunte ao aluno|diga ao aluno|não mostre|hotmart|checkout|\bcompre\b'
    r'|zernio|metricool|apify|mcp__|—|mediana', re.I)


def montar_pacote(destino: Path) -> Path:
    """Uma cópia mínima e válida do pacote: os dois manifestos, o ícone e a skill principal."""
    pasta = destino / 'sofia-estrategista'
    (pasta / 'assets').mkdir(parents=True)
    shutil.copy(FONTE / 'plugin.json', pasta / 'plugin.json')
    shutil.copy(FONTE / 'mcp.json', pasta / 'mcp.json')
    shutil.copy(ROOT / 'assets/icon.png', pasta / 'assets/icon.png')
    shutil.copytree(ROOT / 'skills/sofia-estrategista', pasta / 'skills/sofia-estrategista')
    return pasta


def editar_json(arquivo: Path, mudar):
    dados = json.loads(arquivo.read_text(encoding='utf-8'))
    mudar(dados)
    arquivo.write_text(json.dumps(dados, ensure_ascii=False), encoding='utf-8')


class ManifestoDaOpenAI(unittest.TestCase):
    def setUp(self):
        self.openai = json.loads((FONTE / 'plugin.json').read_text(encoding='utf-8'))
        self.mcp = json.loads((FONTE / 'mcp.json').read_text(encoding='utf-8'))
        self.claude = json.loads((ROOT / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))
        self.codex = json.loads((ROOT / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))
        self.extensao = self.openai['extensions']['com.openai']

    def test_identidade_igual_a_dos_outros_manifestos(self):
        for campo in ('name', 'version', 'license', 'repository'):
            self.assertEqual(self.openai[campo], self.claude[campo], campo)
            self.assertEqual(self.openai[campo], self.codex[campo], campo)

    def test_conector_e_o_mesmo_do_plugin(self):
        legado = json.loads((ROOT / '.mcp.json').read_text(encoding='utf-8'))['mcpServers']
        self.assertEqual(set(self.mcp['mcpServers']), set(legado))
        for nome, servidor in self.mcp['mcpServers'].items():
            self.assertEqual(servidor['url'], legado[nome]['url'])
            self.assertEqual(servidor['type'], 'streamable-http')

    def test_oauth_sem_segredo_nem_cabecalho(self):
        for servidor in self.mcp['mcpServers'].values():
            self.assertNotIn('headers', servidor)
            auth = servidor['extensions']['com.openai']['auth']
            self.assertEqual(auth['type'], 'oauth')
            # O servidor anuncia DCR e CIMD; cimd aceita só mode (o DCR fica de reserva no próprio cliente).
            self.assertEqual(auth['client'], {'mode': 'cimd'})

    def test_desktop_only_como_no_codex(self):
        # A edição roda programas na máquina; o Codex já declara isso no topo do .codex-plugin.
        self.assertIs(self.extensao['requires_local_executor'], self.codex['requires_local_executor'])

    def test_pedidos_iniciais_preservados_do_codex(self):
        # legacy-manifest-migration.md: os pedidos iniciais passam sem reescrever, na mesma ordem.
        self.assertEqual(self.extensao['interface']['defaultPrompt'], self.codex['interface']['defaultPrompt'])

    def test_traducao_pt_br_e_a_ficha_do_codex(self):
        traducao = self.extensao['publication']['translations']['pt-BR']
        self.assertEqual(traducao['subtitle'], self.codex['interface']['shortDescription'])
        self.assertEqual(traducao['description'], self.codex['interface']['longDescription'])

    def test_casos_de_revisao_citam_ferramentas_que_o_plugin_conhece(self):
        # Sem o site à mão, a prova é o próprio plugin: toda ferramenta do conector aparece entre crases nos .md
        # (scripts/conferir-ferramentas.mjs confere os .md contra o servidor).
        citadas = set()
        for md in ROOT.rglob('*.md'):
            citadas |= set(re.findall(r'`([a-z][a-z0-9_]*)`', md.read_text(encoding='utf-8')))
        for caso in self.extensao['review']['test_cases']['positive']:
            for ferramenta in (t.strip() for t in caso['tools_triggered'].split(',')):
                self.assertIn(ferramenta, citadas, caso['description'])

    def test_textos_da_ficha_passam_no_teste_da_loja(self):
        interface = self.extensao['interface']
        textos = [self.openai['description'], interface['shortDescription'], interface['longDescription'],
                  *self.extensao['publication']['translations']['pt-BR'].values()]
        for texto in textos:
            self.assertIsNone(LOJA.search(texto), texto[:80])

    def test_nada_de_email_pessoal_nem_credencial(self):
        texto = (FONTE / 'plugin.json').read_text(encoding='utf-8') + (FONTE / 'mcp.json').read_text(encoding='utf-8')
        self.assertNotRegex(texto, r'[\w.+-]+@[\w-]+\.[\w.]+')
        self.assertFalse(validar.procurar_chaves(self.openai, {'test_credentials', 'reviewer_instructions', 'clientSecret'}))


class Validador(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.pasta = montar_pacote(Path(self.temporario.name))

    def tearDown(self):
        self.temporario.cleanup()

    def conferir(self):
        return validar.conferir(self.pasta)

    def test_pacote_minimo_passa(self):
        r = self.conferir()
        self.assertEqual(r.erros, [])
        self.assertEqual({c for c, _ in r.pendentes}, {'review_demo_recording_missing', 'publication_countries_missing'})

    def test_recusa_subtitulo_longo_e_categoria_inventada(self):
        def mudar(m):
            m['extensions']['com.openai']['interface']['shortDescription'] = 'x' * 31
            m['extensions']['com.openai']['interface']['category'] = 'Design'
        editar_json(self.pasta / 'plugin.json', mudar)
        self.assertTrue({'submission_subtitle_too_long', 'plugin_category_unknown'} <= self.conferir().codigos())

    def test_recusa_link_faltando_ou_sem_https(self):
        def mudar(m):
            interface = m['extensions']['com.openai']['interface']
            del interface['termsOfServiceURL']
            interface['supportURL'] = 'mailto:suporte@example.com'
        editar_json(self.pasta / 'plugin.json', mudar)
        self.assertTrue({'plugin_terms_of_service_url_required', 'plugin_support_url_format'} <= self.conferir().codigos())

    def test_recusa_contagem_errada_de_casos(self):
        editar_json(self.pasta / 'plugin.json',
                    lambda m: m['extensions']['com.openai']['review']['test_cases']['positive'].pop())
        self.assertIn('review_test_cases_count', self.conferir().codigos())

    def test_recusa_caso_com_lista_no_lugar_de_texto(self):
        def mudar(m):
            m['extensions']['com.openai']['review']['test_cases']['positive'][0]['tools_triggered'] = ['planejamento_quadro']
        editar_json(self.pasta / 'plugin.json', mudar)
        self.assertIn('review_test_case_field_required', self.conferir().codigos())

    def test_recusa_pedido_inicial_com_mencao_ou_repetido(self):
        def mudar(m):
            m['extensions']['com.openai']['interface']['defaultPrompt'] = ['Abre @sofia-estrategista', 'Oi  sofia', 'oi sofia']
        editar_json(self.pasta / 'plugin.json', mudar)
        self.assertTrue({'plugin_default_prompt_mention', 'plugin_default_prompt_duplicate'} <= self.conferir().codigos())

    def test_recusa_apps_hooks_e_app_json(self):
        editar_json(self.pasta / 'plugin.json', lambda m: m['extensions']['com.openai'].update(apps='./.app.json'))
        (self.pasta / '.app.json').write_text('{"apps": {}}')
        (self.pasta / 'hooks').mkdir()
        self.assertTrue({'app_configuration_excluded', 'lifecycle_hooks_excluded'} <= self.conferir().codigos())

    def test_recusa_token_no_mcp(self):
        def mudar(m):
            servidor = m['mcpServers']['sofia-estrategista']
            servidor['headers'] = {'Authorization': 'Bearer abc'}
            servidor['extensions']['com.openai']['auth']['client'] = {'mode': 'provided', 'clientId': 'x', 'clientSecret': 'y'}
        editar_json(self.pasta / 'mcp.json', mudar)
        self.assertTrue({'mcp_server_headers_rejected', 'mcp_auth_secret_in_package'} <= self.conferir().codigos())

    def test_recusa_mcp_local_e_tipo_antigo(self):
        def mudar(m):
            m['mcpServers']['sofia-estrategista']['type'] = 'http'
            m['mcpServers']['local'] = {'type': 'stdio', 'command': 'node'}
        editar_json(self.pasta / 'mcp.json', mudar)
        self.assertTrue({'mcp_server_type', 'mcp_configuration_excluded'} <= self.conferir().codigos())

    def test_recusa_skill_sem_cabecalho_e_campo_fora_do_manifesto(self):
        skill = self.pasta / 'skills/sem-cabecalho'
        skill.mkdir()
        (skill / 'SKILL.md').write_text('Só texto, sem YAML.\n', encoding='utf-8')
        editar_json(self.pasta / 'plugin.json', lambda m: m.update(skills='./skills/'))
        self.assertTrue({'skill_frontmatter_missing', 'plugin_manifest_field_unsupported'} <= self.conferir().codigos())

    def test_recusa_icone_que_nao_e_quadrado(self):
        icone = self.pasta / 'assets/icon.png'
        dados = bytearray(icone.read_bytes())
        dados[20:24] = (300).to_bytes(4, 'big')  # altura no cabeçalho IHDR
        icone.write_bytes(bytes(dados))
        self.assertIn('raster_image_not_square', self.conferir().codigos())

    def test_zip_com_irmao_no_topo_e_recusado(self):
        destino = Path(self.temporario.name) / 'envio.zip'
        with zipfile.ZipFile(destino, 'w') as z:
            for arquivo in self.pasta.rglob('*'):
                z.write(arquivo, arquivo.relative_to(self.pasta.parent).as_posix())
            z.writestr('LEIA.txt', 'solto')
        self.assertIn('plugin_root_has_siblings', validar.conferir(destino).codigos())


@unittest.skipUnless(shutil.which('zip') and shutil.which('unzip'), 'zip e unzip não instalados')
class Empacotar(unittest.TestCase):
    def test_script_monta_um_zip_que_passa_e_so_tem_o_formato_portatil(self):
        with tempfile.TemporaryDirectory() as saida:
            ambiente = dict(os.environ, DIST_OPENAI=saida)
            feito = subprocess.run([str(REPO / 'scripts/empacotar-openai.sh')], env=ambiente, capture_output=True, text=True)
            self.assertEqual(feito.returncode, 0, feito.stdout + feito.stderr)
            with zipfile.ZipFile(Path(saida) / 'sofia-estrategista-openai.zip') as z:
                nomes = z.namelist()
                manifesto = json.loads(z.read('sofia-estrategista/plugin.json'))
        self.assertEqual({n.split('/')[0] for n in nomes}, {'sofia-estrategista'})
        for proibido in ('.claude-plugin/', '.codex-plugin/', '.mcp.json', '.agents/', 'hooks/', '.app.json', 'tests/'):
            self.assertFalse([n for n in nomes if f'/{proibido}' in n], proibido)
        self.assertIn('sofia-estrategista/mcp.json', nomes)
        self.assertEqual(manifesto, json.loads((FONTE / 'plugin.json').read_text(encoding='utf-8')))
        skills = {n.split('/')[2] for n in nomes if n.startswith('sofia-estrategista/skills/') and n.count('/') >= 3}
        self.assertEqual(skills, {p.name for p in (ROOT / 'skills').iterdir() if (p / 'SKILL.md').exists()})


if __name__ == '__main__':
    unittest.main()
