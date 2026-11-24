# Passadas: a equipe da Sofia onde não há agentes

No Claude Code e no Cowork, cada papel da equipe é um agente do plugin. No Claude do site e do celular, no ChatGPT e em qualquer app em que os agentes não abrem, o mesmo plano roda em **passadas**: você faz um papel por vez, na própria conversa, e busca a fatia certa do método na hora de usar.

O plano de cada etapa vem do conector, na seção "Passos e equipe desta etapa" do pacote (`sofia_preparar_escrita`). Se o plano do pacote disser outra coisa que esta página, vale o pacote.

## Sumário

1. As regras de toda passada
2. Brainstorm (ideia, bolha e pesquisa)
3. Pesquisa
4. Hook
5. Roteiro
6. Ajuste
7. Crítica e lapidar
8. Codex
9. Sem o conector

## 1. As regras de toda passada

- **Escrever separado de conferir.** Primeiro escreva tudo, sem mostrar. Depois confira, como revisor, com as cartas na frente. Só depois corrija.
- **Veredito antes da correção.** Para cada opção e cada carta, escreva para você passa, falha ou não se aplica antes de mudar qualquer palavra. A correção vem da lista de falhas.
- **Ordem para juntar as falhas**, quando duas brigam:
  1. Piso;
  2. fatos;
  3. a voz da pessoa e o "como trabalhar" dela;
  4. hook (assunto e clareza antes de estilo);
  5. bolha;
  6. método.
- **No máximo 2 rodadas.** Na segunda, confira só os códigos que falharam. O que ainda falhar vai para a pessoa como observação curta.
- **Gerar muitos, mostrar poucos.** Hook: de 8 a 10 escritos, de 3 a 5 mostrados, com tipos diferentes e menos falhas.
- **Uma linha para a pessoa.** Depois do selo de conferência, diga só que o texto passou pela conferência. A tabela dos vereditos fica para quando ela pedir.
- **Muitas chamadas numa resposta.** Se o app cortar a resposta no meio das chamadas, junte passos: um só `sofia_briefing` com vários papéis em `modo: "cartas"` serve a todos os revisores da etapa.

## 2. Brainstorm (ideia, bolha e pesquisa)

1. `sofia_preparar_escrita` com `tipo: "ideia"` e `entrega: "orquestrar"`.
2. `sofia_briefing` com `papel: "estrategista-de-ideias"` e `etapa: "ideia"`, todas as partes. Monte, sem mostrar, de 3 a 5 direções no modelo de ideia e até 5 perguntas, da que mais muda a direção para a que menos muda.
3. `sofia_briefing` com `papel: "especialista-em-bolha"` e `etapa: "ideia"`. Monte 2 ou 3 bolhas candidatas com o plano de pesquisa de cada uma.
4. Os dois briefings entram uma vez por conversa. Se a resposta da pessoa mudar a direção, releia só as cartas do papel (`modo: "cartas"`).
5. Converse: uma pergunta por vez, a mais valiosa primeiro. Grave cada decisão na hora: a bolha com `cerebro_bolha`, os achados com `planejamento_salvar_pesquisa`, a ideia e o formato com `planejamento_editar_card`, os blocos com `planejamento_estruturar_card` e, com o OK da pessoa, a preferência com `cerebro_preferencia`.
6. Fechar a ideia: `sofia_briefing` com `papel: ["revisor-de-estrutura", "especialista-em-bolha"]`, `etapa: "ideia"` e `modo: "cartas"`. Veredito por carta, correção, e `sofia_conferir` com `etapa: "ideia"`, as ideias em `opcoes` (campo `texto`) e os vereditos.

## 3. Pesquisa

1. Com busca na internet ou um conector de pesquisa ligado: `sofia_briefing` com `papel: "pesquisador"` e `etapa: "pesquisa"`, e pesquise pelo briefing. Cada achado sai marcado (tipo, acesso, data, ressalva e link), os comentários como foram escritos, sem @, e o que ficou sem fonte vai para "Não verificado".
2. Sem como pesquisar: mostre como ligar um conector de busca no app em uso, só os passos daquele app. Serviço pago só com o OK da pessoa e com a estimativa de custo.
3. Se não der para ligar, siga a peça `pesquisa-manual` (`pesquisa-manual.md`): o que buscar, onde, que prints tirar e como mandar.
4. Cada print que chegar vira:
   - comentário guardado como foi escrito (`cerebro_bolha` e `planejamento_salvar_pesquisa` no grupo `bolha`), com as curtidas como aparecem e o link, se houver;
   - fato com `acesso: "print"` e `dataDaFonte`, a data que o print mostra;
   - "Não verificado", para o que não tem fonte. Isso fica fora do roteiro.

## 4. Hook

1. `sofia_preparar_escrita` com `tipo: "hook"` e `entrega: "orquestrar"`.
2. `sofia_briefing` com `papel: "redator-de-hook"`, `etapa: "hook"` e o `videoId`, todas as partes.
3. Escreva de 8 a 10 opções, sem mostrar, no bloco do briefing: fala, texto na tela, primeiros 2 a 3 segundos, logo depois, tipo de hook e elementos, por que pega com esta bolha. Use as falas da pessoa nesta conversa como ela disse.
4. `sofia_conferir` com `etapa: "hook"`, o `videoId` e as opções em `opcoes`. Corrija toda falha de código.
5. `sofia_briefing` com `papel: ["revisor-o-que-nao-fazer", "revisor-de-hook", "revisor-de-voz", "especialista-em-bolha"]`, `etapa: "hook"` e `modo: "cartas"`.
6. Veredito por carta, para cada opção. Junte as falhas pela ordem da parte 1 e corrija. Rodada 2 só nos códigos que falharam.
7. `sofia_conferir` de novo, com as opções finais e os `vereditos` (`conferidas` com todos os códigos conferidos e `falhas` com o que ficou em aberto). Sem selo, a resposta diz o motivo: corrija se der.
8. Mostre de 3 a 5 e os estilos de gravação, com a linha da conferência. Com a escolha da pessoa, `planejamento_mover_card` com o hook, o estilo e o selo do pacote do hook.

## 5. Roteiro

Igual ao hook, com estas trocas:

- `sofia_preparar_escrita` com `tipo: "roteiro"` e `entrega: "orquestrar"`.
- O escritor é o `roteirista`, com 2 ou 3 versões (uma, se a pessoa pediu). O briefing dele vem em até 4 partes: leia todas.
- `sofia_conferir` com `etapa: "roteiro"` e cada versão em `opcoes` (campo `roteiro`).
- Revisores, equipe completa: `revisor-o-que-nao-fazer`, `revisor-de-hook` (só o hook e a zona de fixação), `revisor-de-voz`, `especialista-em-bolha`, `revisor-de-estrutura` e `revisor-de-fatos`. Com seis papéis, o modo cartas fica grande: chame em dois grupos de três.
- Equipe econômica, quando o plano do pacote mandar: `revisor-o-que-nao-fazer`, `revisor-de-estrutura` e `revisor-de-voz`, e `equipe: "economica"` no `sofia_conferir`.
- Salve cada versão com `sofia_salvar`, o selo do pacote em `selo` e o selo de conferência em `conferencia`. A lista de gravação vai junto, como antes.

## 6. Ajuste

- `sofia_preparar_escrita` com `tipo: "ajuste"`.
- Mude só o trecho pedido. `sofia_conferir` com `etapa: "ajuste"` e o trecho novo em `texto`.
- `sofia_briefing` com `papel: ["revisor-o-que-nao-fazer", "revisor-de-voz"]`, `etapa: "ajuste"` e `modo: "cartas"`, só sobre o trecho mudado.
- Quando o ajuste muda um bloco inteiro, escreva pelo briefing do `roteirista` com `etapa: "ajuste"`.
- Salve com `sofia_salvar`, `nasceuDe`, o selo do pacote e o de conferência.

## 7. Crítica e lapidar

1. `sofia_preparar_escrita` com `tipo: "critica"` e `entrega: "orquestrar"`.
2. `sofia_conferir` com `etapa: "critica"` e o roteiro em `opcoes`. Cada falha de código vira grifo pronto, com o código M.
3. `sofia_briefing` com os revisores do roteiro e o `critico`, `etapa: "critica"` e `modo: "cartas"` (em dois grupos, se ficar grande). Cada falha vira grifo: trecho exato, tipo (cortar, trocar, reforçar ou dúvida), comentário em palavras simples com o princípio entre parênteses, sugestão e os códigos.
4. Tire os grifos repetidos e ordene do que mais muda o vídeo para o que menos muda.
5. `sofia_conferir` com os vereditos completos para o selo. Na crítica, as falhas viram grifos e não seguram o selo.
6. Salve com `sofia_grifos`: o selo do pacote em `selo`, o de conferência em `conferencia` e os códigos de cada grifo em `regras`. No comentário do grifo, o princípio vai em palavras; o código fica só em `regras`.

## 8. Codex

O plugin do Codex não leva os arquivos de agente, mas o Codex tem subagentes próprios, que herdam o conector. Para cada papel do plano, abra um subagente (o padrão serve) com esta instrução:

> Chame `sofia_briefing` do conector Sofia Estrategista com papel {papel}, etapa {etapa} e videoId {videoId}, leia todas as partes, siga o procedimento do briefing e devolva no formato dele. Só leia e devolva: não grave nada no site. {o texto a conferir ou as notas da conversa}

Os revisores rodam juntos. Junte os vereditos como na parte 1 e siga os passos de selo e de salvar da etapa. Se os subagentes não abrirem, siga as passadas desta página.

## 9. Sem o conector

Sem conector não há briefing, conferência nem selo, e nada é salvo. Faça o mesmo caminho com os arquivos desta pasta:

- as cartas de cada papel e as peças que ele lê estão em `cartas.md`, na parte "Por papel";
- as regras M1 a M16, que o conector confere por código, estão no começo de `cartas.md`: confira à mão;
- escreva, confira como revisor e corrija, na mesma ordem das partes acima, e entregue no chat.
