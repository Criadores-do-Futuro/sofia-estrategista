import json
import unittest
from pathlib import Path

# Os catálogos ficam na raiz do repositório; o plugin é a pasta plugin/.
REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / 'plugin'
PAINEL = REPO / 'painel-plugin'


class MarketplaceTest(unittest.TestCase):
    def test_catalogos_apontam_para_o_plugin_em_plugin(self):
        claude = json.loads((REPO / '.claude-plugin/marketplace.json').read_text())
        codex = json.loads((REPO / '.agents/plugins/marketplace.json').read_text())
        manifests = [json.loads((ROOT / '.claude-plugin/plugin.json').read_text()),
                     json.loads((ROOT / '.codex-plugin/plugin.json').read_text())]
        self.assertEqual(manifests[0]['name'], 'sofia-estrategista')
        self.assertEqual(manifests[0]['version'], '2.2.1')
        for campo in ('name', 'version', 'description', 'author'):
            self.assertEqual(manifests[0][campo], manifests[1][campo], campo)
        # O upload de plugin no app (Customize › Plugins › Upload) recusa descrição com mais de 500
        # caracteres ("Plugin description must be at most 500 characters"); o `claude plugin validate`
        # não confere isso.
        self.assertLessEqual(len(manifests[0]['description']), 500)
        # O conector e o /atualizar mandam rodar `... marketplace update/upgrade criadores-do-futuro`
        # no terminal e no Codex: os dois catálogos têm esse nome.
        self.assertEqual(claude['name'], 'criadores-do-futuro')
        self.assertEqual(codex['name'], 'criadores-do-futuro')
        # O sofia-painel é um mod, que o Codex não roda: ele fica só no catálogo do Claude.
        self.assertEqual([p['name'] for p in claude['plugins']], ['sofia-estrategista', 'sofia-painel'])
        self.assertEqual([p['name'] for p in codex['plugins']], ['sofia-estrategista'])
        entrada = claude['plugins'][0]
        self.assertEqual(entrada['source'], './plugin')
        self.assertEqual((REPO / entrada['source']).resolve(), ROOT)
        self.assertEqual(entrada.get('version', manifests[0]['version']), manifests[0]['version'])
        source = codex['plugins'][0]['source']
        self.assertEqual(source['source'], 'local')
        self.assertTrue(source['path'].startswith('./'))
        self.assertEqual((REPO / source['path']).resolve(), ROOT)
        self.assertTrue((ROOT / 'scripts/preparar_estilo.py').is_file())

    def test_o_sofia_painel_no_catalogo_do_claude(self):
        claude = json.loads((REPO / '.claude-plugin/marketplace.json').read_text())
        entrada = next(p for p in claude['plugins'] if p['name'] == 'sofia-painel')
        manifesto = json.loads((PAINEL / '.claude-plugin/plugin.json').read_text())
        self.assertEqual(entrada['source'], './painel-plugin')
        self.assertEqual((REPO / entrada['source']).resolve(), PAINEL)
        self.assertEqual(manifesto['name'], 'sofia-painel')
        self.assertEqual(manifesto['version'], '1.0.0')
        self.assertEqual(entrada['version'], manifesto['version'])
        # Sem faixa de versão: faixa exige tags git do plugin de que ele depende.
        self.assertEqual(manifesto['dependencies'], ['sofia-estrategista'])
        self.assertEqual(manifesto['types'], './types/index.d.ts')
        self.assertTrue((PAINEL / manifesto['icon']).is_file())
        self.assertLessEqual(len(manifesto['description']), 500)
        for arquivo in ('README.md', 'LICENSE', 'hooks/hooks.json', 'hooks/register.tsx', 'types/index.d.ts'):
            self.assertTrue((PAINEL / arquivo).is_file(), arquivo)
        # Nada de segunda cópia do conector, nem de manifesto do Codex.
        self.assertFalse((PAINEL / '.mcp.json').exists())
        self.assertFalse((PAINEL / '.codex-plugin').exists())
        self.assertNotIn('mcpServers', manifesto)

    def test_nenhum_catalogo_lista_o_nome_antigo(self):
        for arquivo in (REPO / '.claude-plugin/marketplace.json', REPO / '.agents/plugins/marketplace.json'):
            with self.subTest(arquivo=arquivo.relative_to(REPO).as_posix()):
                texto = arquivo.read_text()
                self.assertNotIn('sofia-estrategista-editora', texto)
                self.assertNotIn('sofia-editora', texto)

    def test_as_duas_skills_e_o_conector_vem_no_plugin(self):
        for skill in ('sofia-estrategista', 'sofia-editora'):
            texto = (ROOT / 'skills' / skill / 'SKILL.md').read_text()
            self.assertIn(f'name: {skill}\n', texto)
        mcp = json.loads((ROOT / '.mcp.json').read_text())
        self.assertIn('sofia-estrategista', mcp['mcpServers'])
        self.assertTrue(mcp['mcpServers']['sofia-estrategista']['url'].startswith('https://'))
        codex = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())
        self.assertEqual((ROOT / codex['mcpServers']).resolve(), (ROOT / '.mcp.json').resolve())
        self.assertTrue((ROOT / codex['skills']).is_dir())

    def test_atalhos_e_ajudantes_citam_skills_que_existem(self):
        skills = {p.name for p in (ROOT / 'skills').iterdir() if (p / 'SKILL.md').is_file()}
        for arquivo in sorted((ROOT / 'commands').glob('*.md')) + sorted((ROOT / 'agents').glob('*.md')):
            texto = arquivo.read_text()
            self.assertTrue(texto.startswith('---\n'), arquivo.name)
            citadas = {s for s in ('sofia-estrategista', 'sofia-editora') if f'`{s}`' in texto}
            self.assertTrue(citadas <= skills, arquivo.name)

    def test_codex_pede_o_computador_porque_a_edicao_roda_programas_locais(self):
        # developers.openai.com/plugins/deploy/desktop-only: plugin de skills que roda algo na máquina
        # declara requires_local_executor (no formato .codex-plugin, no topo do manifesto).
        codex = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())
        self.assertIs(codex['requires_local_executor'], True)


if __name__ == '__main__':
    unittest.main()
