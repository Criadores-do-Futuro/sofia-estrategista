"""Confere a lista de nomes do interruptor (painel-plugin/hooks/interruptor.ts, do plugin sofia-painel) contra
as pastas do plugin sofia-estrategista (plugin/), onde moram as skills e os comandos que ele reconhece.

A regra em TypeScript não consegue ler disco dentro do `claude plugin test`; então a conferência mora aqui,
onde o `python3 -m unittest discover -s tests` a pega. NOMES_DA_SOFIA é uma lista de conferência, não a
decisão: a regra nega qualquer skill com o prefixo `sofia-estrategista:` sem olhar a lista, e sem o prefixo
só as quatro skills de NOMES_SEM_PREFIXO. A conferência avisa quando uma pasta nova (skill ou comando) fica
fora da lista, para que a lista e a regra sem prefixo sejam revistas juntas.
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1] / 'plugin'
RAIZ = PLUGIN.parent
PAINEL = RAIZ / 'painel-plugin'
TS = PAINEL / 'hooks' / 'interruptor.ts'

# Os comandos do interruptor: precisam estar na lista e ter arquivo em plugin/commands.
COMANDOS_DO_INTERRUPTOR = {'ligar', 'desligar', 'modo', 'ensinar'}


def _literal(nome: str) -> list[str]:
    """Os textos entre aspas do array `nome` em interruptor.ts, sem os comentários."""
    fonte = TS.read_text(encoding='utf-8')
    achado = re.search(r'\bconst\s+' + nome + r'\b[^=]*=\s*\[(.*?)\n?\]', fonte, re.S)
    assert achado, f'{nome} não achado em {TS}'
    sem_comentarios = re.sub(r'//[^\n]*', '', achado.group(1))
    return re.findall(r"'([^']+)'", sem_comentarios)


def _skills() -> set[str]:
    return {p.name for p in (PLUGIN / 'skills').iterdir() if p.is_dir() and not p.name.startswith('.')}


def _comandos() -> set[str]:
    return {p.stem for p in (PLUGIN / 'commands').glob('*.md')}


class NomesDaSofiaTest(unittest.TestCase):
    def setUp(self):
        self.lista = _literal('NOMES_DA_SOFIA')

    def test_a_lista_foi_lida(self):
        self.assertTrue(self.lista)
        self.assertEqual(len(self.lista), len(set(self.lista)), 'nome repetido na lista')

    def test_toda_skill_do_plugin_esta_na_lista(self):
        faltam = _skills() - set(self.lista)
        self.assertFalse(faltam, f'skill fora de NOMES_DA_SOFIA: {sorted(faltam)}')

    def test_todo_comando_do_plugin_esta_na_lista(self):
        faltam = _comandos() - set(self.lista)
        self.assertFalse(faltam, f'comando fora de NOMES_DA_SOFIA: {sorted(faltam)}')

    def test_nome_na_lista_tem_pasta_ou_arquivo(self):
        existentes = _skills() | _comandos()
        sobram = set(self.lista) - existentes
        self.assertFalse(sobram, f'nome em NOMES_DA_SOFIA sem pasta nem arquivo: {sorted(sobram)}')

    def test_os_quatro_comandos_do_interruptor_estao_na_lista(self):
        self.assertFalse(COMANDOS_DO_INTERRUPTOR - set(self.lista))

    def test_os_quatro_comandos_do_interruptor_tem_arquivo(self):
        faltam = COMANDOS_DO_INTERRUPTOR - _comandos()
        self.assertFalse(faltam, f'comando do interruptor sem arquivo em plugin/commands: {sorted(faltam)}')


class NomesSemPrefixoTest(unittest.TestCase):
    def test_sem_prefixo_so_as_skills_do_plugin(self):
        self.assertEqual(set(_literal('NOMES_SEM_PREFIXO')), _skills())


class SemModNoPluginPrincipalTest(unittest.TestCase):
    """Desde a 2.2.0 o mod mora no sofia-painel: o Cowork recusa o plugin inteiro quando há mod."""

    def test_o_plugin_principal_nao_tem_hooks_nem_types(self):
        self.assertFalse((PLUGIN / 'hooks').exists())
        self.assertFalse((PLUGIN / 'types').exists())
        manifesto = (PLUGIN / '.claude-plugin' / 'plugin.json').read_text(encoding='utf-8')
        self.assertNotIn('"types"', manifesto)
        self.assertNotIn('"hooks"', manifesto)

    def test_o_mod_esta_no_sofia_painel(self):
        self.assertEqual((PAINEL / 'hooks' / 'hooks.json').read_text(encoding='utf-8').strip(),
                         '{ "modules": ["./register.tsx"] }')
        for arquivo in ('register.tsx', 'interruptor.ts', 'register.test.ts', 'interruptor.test.ts'):
            self.assertTrue((PAINEL / 'hooks' / arquivo).is_file(), arquivo)
        self.assertTrue((PAINEL / 'types' / 'index.d.ts').is_file())

    def test_o_mod_nao_liga_nem_chama_o_conector(self):
        # A referência dos mods: `$.mcp.connect` liga só um servidor do manifesto do próprio plugin, e o
        # sofia-painel não declara conector. O painel aprende o quadro pelo hook tool.call.
        fonte = (PAINEL / 'hooks' / 'register.tsx').read_text(encoding='utf-8')
        self.assertNotIn('$.mcp.', fonte)
        self.assertIn("on('tool.call', { tool: FERRAMENTAS_DO_PLANEJAMENTO }", fonte)
        self.assertFalse((PAINEL / '.mcp.json').exists())

    def test_o_estado_do_mod_e_do_proprio_sofia_painel(self):
        # `$.state.set` só grava valor do próprio plugin.
        fonte = (PAINEL / 'hooks' / 'register.tsx').read_text(encoding='utf-8')
        self.assertNotIn("plugin: 'sofia-estrategista'", fonte)
        self.assertIn("plugin: 'sofia-painel'", fonte)
        self.assertIn("'sofia-painel': {", (PAINEL / 'types' / 'index.d.ts').read_text(encoding='utf-8'))


class EmpacotarTest(unittest.TestCase):
    def setUp(self):
        self.script = (RAIZ / 'scripts' / 'empacotar.sh').read_text(encoding='utf-8')

    def test_o_pacote_do_app_nao_leva_hooks_nem_types(self):
        itens = re.search(r'ITENS=\((.*?)\n\)', self.script, re.S)
        self.assertTrue(itens)
        linhas = {linha.strip() for linha in itens.group(1).splitlines()}
        self.assertNotIn('hooks', linhas)
        self.assertNotIn('types', linhas)
        self.assertIn('skills', linhas)

    def test_o_pacote_recusa_hooks_se_eles_voltarem(self):
        self.assertIn('[ -e "$MONTAGEM/$PASTA/hooks" ]', self.script)


if __name__ == '__main__':
    unittest.main()
