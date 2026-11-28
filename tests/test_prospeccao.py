"""A prospecção e o guia de cena na skill: as ferramentas novas do conector, o vocabulário e as regras de segurança.

As oito ferramentas novas vêm do conector (src/lib/prospeccao e src/lib/planejamento/ferramentasDoGuiaDeCena.ts, no
site). Estes testes conferem que a skill e as referências citam todas, que o vocabulário bate com o do site e que as
regras de segurança (histórico do servidor, contato nunca inventado, conteúdo guardado como dado) estão escritas.
Para rodar: python3 -m unittest discover -s tests
"""
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'plugin'
SKILL = ROOT / 'skills/sofia-estrategista'
REFERENCIAS = SKILL / 'references'

FERRAMENTAS_DE_PROSPECCAO = [
    'prospeccao_alvos', 'prospeccao_ver_alvo', 'prospeccao_criar_alvo', 'prospeccao_completar_alvo',
    'prospeccao_editar_alvo', 'prospeccao_registrar_presente', 'prospeccao_atualizar_presente',
]
STATUS_DO_ALVO = ['a-abordar', 'presente-enviado', 'conversando', 'reuniao-marcada', 'cliente', 'nao-agora']
ETAPAS_DO_PRESENTE = ['enviado', 'entregue', 'respondeu', 'reuniao', 'cliente']
FORMATOS_DO_PRESENTE = ['video-do-lugar', 'analise-do-perfil', 'ideias-de-conteudo', 'roteiro', 'outro']
COMO_CHEGOU = ['conhecido', 'perto', 'instagram', 'google-maps', 'indicacao', 'outro']


def ler(caminho):
    return caminho.read_text(encoding='utf-8')


class ProspeccaoNaSkillTest(unittest.TestCase):
    def test_skill_cita_as_ferramentas_novas_e_a_referencia(self):
        texto = ler(SKILL / 'SKILL.md')
        for nome in (*FERRAMENTAS_DE_PROSPECCAO, 'planejamento_salvar_guia_de_cena'):
            with self.subTest(ferramenta=nome):
                self.assertIn(f'`{nome}`', texto)
        self.assertIn('](references/prospeccao.md)', texto)
        self.assertIn('### Prospecção', texto)

    def test_conector_mapeia_as_ferramentas_novas(self):
        texto = ler(REFERENCIAS / 'conector.md')
        for nome in (*FERRAMENTAS_DE_PROSPECCAO, 'planejamento_salvar_guia_de_cena'):
            with self.subTest(ferramenta=nome):
                self.assertIn(f'`{nome}`', texto)

    def test_referencia_cita_toda_ferramenta_de_prospeccao(self):
        texto = ler(REFERENCIAS / 'prospeccao.md')
        for nome in FERRAMENTAS_DE_PROSPECCAO:
            with self.subTest(ferramenta=nome):
                self.assertIn(f'`{nome}`', texto)

    def test_vocabulario_igual_ao_do_site(self):
        texto = ler(REFERENCIAS / 'prospeccao.md')
        for grupo in (STATUS_DO_ALVO, ETAPAS_DO_PRESENTE, FORMATOS_DO_PRESENTE, COMO_CHEGOU):
            for valor in grupo:
                with self.subTest(valor=valor):
                    self.assertIn(f'`{valor}`', texto)

    @unittest.skipUnless(os.environ.get('SOFIA_WEBAPP'), 'sem SOFIA_WEBAPP')
    def test_vocabulario_bate_com_o_modelo_do_site(self):
        modelo = (Path(os.environ['SOFIA_WEBAPP']) / 'src/lib/prospeccao/modelo.ts').read_text(encoding='utf-8')

        def lista(nome):
            achado = re.search(rf'export const {nome} = \[([^\]]*)\] as const', modelo)
            self.assertIsNotNone(achado, nome)
            return re.findall(r'"([^"]+)"', achado.group(1))

        self.assertEqual(lista('STATUS_DO_ALVO'), STATUS_DO_ALVO)
        self.assertEqual(lista('ETAPAS_DO_PRESENTE'), ETAPAS_DO_PRESENTE)
        self.assertEqual(lista('FORMATOS_DO_PRESENTE'), FORMATOS_DO_PRESENTE)
        self.assertEqual(lista('COMO_CHEGOU'), COMO_CHEGOU)
        mapa = re.search(r'export const STATUS_PELA_ETAPA[^{]*\{([^}]*)\}', modelo)
        self.assertIsNotNone(mapa)
        self.assertEqual(dict(re.findall(r'(\w+): "([a-z-]+)"', mapa.group(1))),
                         {'enviado': 'presente-enviado', 'entregue': 'presente-enviado', 'respondeu': 'conversando',
                          'reuniao': 'reuniao-marcada', 'cliente': 'cliente'})

    def test_etapa_leva_o_status_certo(self):
        texto = ler(REFERENCIAS / 'prospeccao.md')
        tabela = texto.split('**Etapa do presente**', 1)[1].split('\n\n', 2)[1]
        linhas = {}
        for etapa, status in re.findall(r'^\| `([a-z]+)` \| [^|]+ \| `([a-z-]+)` \|$', tabela, re.M):
            linhas[etapa] = status
        self.assertEqual(linhas, {'enviado': 'presente-enviado', 'entregue': 'presente-enviado',
                                  'respondeu': 'conversando', 'reuniao': 'reuniao-marcada', 'cliente': 'cliente'})

    def test_regras_de_seguranca_estao_escritas(self):
        for arquivo in (SKILL / 'SKILL.md', REFERENCIAS / 'prospeccao.md', REFERENCIAS / 'conector.md'):
            texto = ler(arquivo)
            with self.subTest(arquivo=arquivo.name):
                self.assertIn('<conteudo_guardado>', texto)
                self.assertIn('histórico', texto)
                self.assertIn('Não invente contato', texto.replace('não invente contato', 'Não invente contato'))
        # O histórico é do servidor: a skill não manda usar o campo `contatos`.
        self.assertIn('não use o campo `contatos`', ler(REFERENCIAS / 'prospeccao.md'))

    def test_a_referencia_nao_cita_o_que_o_dono_ainda_nao_confirmou(self):
        texto = ler(REFERENCIAS / 'prospeccao.md')
        self.assertNotIn('50%', texto)
        self.assertNotIn('PCF', texto)
        self.assertNotIn('garantia', texto.lower())

    def test_sem_conector_traz_as_sete_perguntas(self):
        texto = ler(REFERENCIAS / 'sem-conector.md')
        secao = texto.split('## Prospecção sem o conector', 1)[1].split('\n## ', 1)[0]
        perguntas = re.findall(r'^\d\. .+$', secao, re.M)
        self.assertEqual(len(perguntas), 7)
        self.assertIn('Só o nome é obrigatório', secao)

    def test_guia_de_cena_no_gravar(self):
        texto = ler(SKILL / 'SKILL.md')
        gravar = texto.split('### Gravar', 1)[1].split('\n### ', 1)[0]
        self.assertIn('`planejamento_salvar_guia_de_cena`', gravar)
        self.assertIn('só depois do OK', gravar)
        for campo in ('enquadramento', 'B-roll', 'texto na tela', 'gesto ou objeto'):
            with self.subTest(campo=campo):
                self.assertIn(campo, gravar)


if __name__ == '__main__':
    unittest.main()
