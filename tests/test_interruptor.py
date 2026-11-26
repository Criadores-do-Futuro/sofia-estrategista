"""Confere a lista de nomes do interruptor (plugin/hooks/interruptor.ts) contra as pastas do plugin.

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
TS = PLUGIN / 'hooks' / 'interruptor.ts'

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


class EmpacotarTest(unittest.TestCase):
    def test_testes_do_gancho_ficam_fora_do_pacote(self):
        script = (RAIZ / 'scripts' / 'empacotar.sh').read_text(encoding='utf-8')
        fora = re.search(r'FORA=\((.*?)\n\)', script, re.S)
        self.assertTrue(fora)
        self.assertIn("'hooks/*.test.ts'", fora.group(1))


if __name__ == '__main__':
    unittest.main()
