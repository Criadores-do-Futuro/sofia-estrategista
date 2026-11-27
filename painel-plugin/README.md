# Sofia Painel

O painel e o interruptor da [Sofia Estrategista](../plugin/README.md) no Claude Code. É um plugin à parte desde a Sofia 2.2.0: ele é um mod, e mods só rodam no Claude Code (terminal, aba Code do app e extensões de IDE). Separado, ele não impede a Sofia de carregar no chat e no Cowork.

Ele precisa do plugin `sofia-estrategista` (campo `dependencies` do manifesto) e não serve sozinho: as skills, os atalhos e o conector são da Sofia.

## O que ele faz

- **Painel ao lado da conversa.** Mostra quantos cards há em cada etapa do planejamento (Brainstorming, Estruturar, Revisar, Lapidar, Gravar), o @ do perfil e o uso das janelas de 5 horas e de 7 dias do Claude, com quanto falta para cada uma zerar. Abre sozinho no início da sessão, quando a tela tem largura para ele, e pelo comando `/sofia-painel`. A barra de status mostra o resumo.
- **De onde vêm os cards.** O painel não chama o conector. Quando a Sofia lê o planejamento (a ferramenta `planejamento_quadro` do conector Sofia Estrategista, pelo plugin ou pelo conector ligado no site do Claude), o painel lê a resposta e guarda as contagens. A resposta segue para o modelo sem mudança nenhuma. Antes da primeira leitura da sessão, o painel diz: "Os cards aparecem aqui quando a Sofia ler o seu planejamento." Depois que uma ferramenta grava no planejamento (criar, mover ou editar um card), ele avisa que o quadro mudou depois da última leitura.
- **Interruptor neste computador.** A Sofia pode ficar `ligada` (o padrão), `so-quando-chamada` (só age depois que a pessoa a chama pelo nome) ou `desligada`. O painel põe no contexto de cada pedido a linha `Interruptor local: <modo>.`, que a skill da Sofia segue, e, quando o modo manda, nega a skill da Sofia, os agentes dela e as ferramentas do conector. Pedidos como "Sofia, desliga", "liga a Sofia" e "Sofia, só quando eu chamar" mudam o modo. Com a Sofia desligada, chamar a Sofia pelo nome só faz a oferta "Estou desligada aqui. Quer que eu ligue?", e ela liga com o sim da pessoa.
- **Primeiro uso.** Na primeira vez que a Sofia age neste computador, o painel avisa o modelo para abrir com o tutorial curto e marca que ela já se apresentou.

## Comandos

| Comando | O que faz |
|---|---|
| `/sofia-painel` | Abre o painel |
| `/sofia-ligar` | Liga a Sofia neste computador |
| `/sofia-desligar` | Desliga a Sofia neste computador |
| `/sofia-modo` | Sem argumento, diz o modo de agora; com `ligada`, `so-quando-chamada` ou `desligada`, troca |
| `/sofia-ensinar` | Pede ao modelo o tutorial da Sofia |

Os atalhos da Sofia (`/sofia-estrategista:ligar`, `desligar`, `modo` e `ensinar`) também mudam o modo quando este plugin está instalado.

`/sofia-painel` (este painel ao lado da conversa) e `/sofia-estrategista:painel` são coisas diferentes: o segundo é o painel de revisão da edição de vídeo (bEditor), da própria Sofia.

## O que ele lê, grava e envia

- **Lê e grava um arquivo só:** `estado.json`, na pasta de dados deste plugin (`CLAUDE_PLUGIN_DATA`), neste computador. Ele guarda o modo, se a Sofia já se apresentou (`apresentada`) e quando o modo mudou (`mudouEm`). É lido a cada pedido e só é gravado quando a pessoa muda o modo ou quando a Sofia se apresenta pela primeira vez. Sem o arquivo, ou com ele ilegível, a Sofia fica ligada.
- **Guarda marcas da sessão** no estado de sessão do Claude Code (`$.state`): se a Sofia foi chamada pelo nome, se ela ofereceu ligar, se o modelo pode trocar o modo, se ela perguntou o modo e se a linha do primeiro uso já veio. Elas valem só a sessão em curso. O quadro e o uso das janelas também ficam ali, só para desenhar o painel.
- **Lê** o resultado das ferramentas do planejamento que a Sofia chamou, sem mudá-lo, e o uso das janelas do Claude que o próprio Claude Code informa.
- **Não envia nada a lugar nenhum.** Não faz requisição de rede, não chama o conector, não roda programa e não lê outros arquivos. Ligar ou desligar a Sofia não manda nada ao servidor.

## Vindo da Sofia 2.1 ou anterior

Até a 2.1.1, o painel morava dentro do plugin `sofia-estrategista`, e o `estado.json` ficava na pasta de dados dele. Agora o arquivo fica na pasta de dados do `sofia-painel`, então o interruptor volta para "ligada" uma vez. Quem tinha desligado a Sofia ou escolhido "só quando chamada" escolhe de novo depois de instalar este plugin.

## Instalar

```sh
claude plugin marketplace add Criadores-do-Futuro/sofia-estrategista
claude plugin install sofia-estrategista@criadores-do-futuro
claude plugin install sofia-painel@criadores-do-futuro
```

Depois, `/reload-plugins` ou uma sessão nova. Para testar um checkout: `claude --plugin-dir "CAMINHO_DO_REPOSITORIO/plugin" --plugin-dir "CAMINHO_DO_REPOSITORIO/painel-plugin"`.

Este plugin não entra no catálogo do Codex nem no pacote `.zip` do kit: o Codex e o app não rodam mod.

## Para quem mexe no código

- `hooks/hooks.json` carrega o módulo `hooks/register.tsx`. A regra do interruptor (funções puras) está em `hooks/interruptor.ts`. O contrato do estado está em `types/index.d.ts`.
- Testes do mod: `claude plugin test painel-plugin`. Validação: `claude plugin validate --strict painel-plugin`.
- O `validate` não confere os tipos de um mod que tem `dependencies`. Confira com o `tsc`: carregue o mod uma vez com `claude --plugin-dir` (o Claude Code escreve os tipos em `.claude-plugin/types/`) e rode `tsc -p painel-plugin`, ou use um `tsconfig.json` fora da pasta que inclua o `claude-code.d.ts` da skill `plugin-authoring`, `painel-plugin/hooks` e `painel-plugin/types`.
- A lista de nomes da Sofia em `interruptor.ts` é conferida contra as pastas de `plugin/skills` e `plugin/commands` por `tests/test_interruptor.py`, na raiz do repositório.

## Licença

Uso permitido junto com a Sofia Estrategista; redistribuição só com autorização. Veja [LICENSE](LICENSE).
