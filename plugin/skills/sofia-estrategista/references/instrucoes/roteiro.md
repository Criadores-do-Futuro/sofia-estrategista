# Escrever um roteiro com o conector

> Cópia da peça `instrucoes/roteiro` do método (gerada do webapp, método 660ad6a20d05). Com o conector ligado, vale a versão de `sofia_metodo` com `instrucoes/roteiro`, que é a mais nova. Não edite à mão: o arquivo é regerado.

Este guia descreve o caminho de escrita de um roteiro de vídeo curto no Criador Estrategista. O conector
guarda o método, os dados do aluno e o que a conversa produz. O caminho funciona em português do Brasil,
com uma pergunta ou um bloco curto por vez, e cada passo é salvo quando o aluno pede ou confirma.

Cada fase é um ponto de parada, e o que falta de uma não trava a seguinte. O aluno pode começar em
qualquer uma. Ao chegar, veja o que das fases anteriores falta, diga em uma frase por que aquilo deixa
o vídeo melhor e ofereça fazer junto. Nunca sugira pular por conta própria. Se o aluno quiser seguir
sem, siga sem insistir. Não há número mínimo de achados, comentários ou referências, nem ordem fixa
dentro da fase. Só duas passagens dependem do que a anterior produz: o roteiro parte de um hook e um
estilo escolhidos, e o card só entra em Lapidar com grifos. Nesses dois casos, o pacote que volta é o
do que falta (o do hook ou o da crítica), e você faz esse passo com o aluno.

## Começo

A `sofia_meus_videos` mostra os vídeos em andamento, a coluna de cada um no quadro, se há perfil e voz
salvos e o próximo passo sugerido. Se ele tem vídeo parado, a pergunta é se quer continuar aquele ou
começar outro. Para ver um vídeo inteiro, serve a `sofia_video`.

As peças do método saem da `sofia_metodo`, pelo nome: `principios`, `regras-universais`, `sem-slop`,
`como-escrever-bem`, `diagnostico`, `formatos/README`, `formatos/<formato>`,
`estruturas-de-roteiro/README`, `estruturas-de-roteiro/<estrutura>`, `elementos-viciantes/README`,
`exemplos-analisados/<formato>`, `knowledge/arquetipos-nichos-bolhas`, `knowledge/hooks-que-funcionam`,
`knowledge/principios-exemplos`. A peça serve de base para o texto do passo: o roteiro parte dela, e não
de memória.

**Um pacote por etapa.** Cada etapa (ideia, hook, roteiro, ajuste, crítica) pede o pacote da
`sofia_preparar_escrita`. O pacote termina com um selo: ao gravar o que saiu dele (`sofia_salvar`,
`sofia_grifos`, `planejamento_mover_card`), mande o selo em `selo`. No pacote seguinte do mesmo card,
diga em `ja_tenho` o que do anterior ainda está na conversa (`metodo`, `perfil`, `cerebro`, `pesquisa`,
`base`; `[]` quando nada) e mande o selo dele em `selo`: essas partes não voltam, a não ser que tenham
mudado, e as regras delas continuam valendo. Sem o selo, o pacote vem inteiro. Parte que saiu da
conversa não entra em `ja_tenho`. As regras e o método de cada escrita vêm sempre.

O pacote já traz as peças do método da etapa. As peças que o passo pede além do pacote são lidas uma
vez por conversa; fora isso, a `sofia_metodo` volta só para o formato, a estrutura ou o elemento que o
aluno citar e o pacote não trouxe.

**Texto sem cara de IA.** A peça `sem-slop` (pela `sofia_metodo`) traz as regras para os textos do aluno
(hook, roteiro, ângulo, lista de gravação). O texto pronto é conferido contra elas, uma por uma, e o que
bater é reescrito. O resumo de bolso está em `sem-slop-resumo`.

As respostas das ferramentas de escrita terminam com um bloco "Vale agora": os princípios resumidos, as
regras do formato, a estrutura e a voz do aluno. Esse bloco vale para o próximo passo.

## Fase 0: a voz

Leia o perfil com `sofia_perfil`. A voz guardada (tom, vocabulário, expressões e o que ele evita)
também vem no pacote do hook, do roteiro e do ajuste.

- Com voz salva: avise "Vou escrever no seu jeito de falar" e siga o tom, o ritmo, as palavras e o tipo
  de abertura do perfil.
- Sem voz: ofereça aprender, uma vez. Se ele aceitar, siga `instrucoes/estilo` (pela `sofia_metodo`).
  Se recusar, use `como-escrever-bem` como guia.

## Fase 1: tema, bolha e pesquisa

Cada vídeo é um card do quadro. Se o aluno já tem o card deste tema, use o id dele. Se não tem, crie
com `planejamento_criar_card`, só com o tema: ele entra em Brainstorming.

O objetivo de todo roteiro é furar uma bolha, para aumentar a chance de o vídeo viralizar. Leia a peça
`furar-bolha` (pela `sofia_metodo`) uma vez por conversa, antes da primeira ideia: ela traz a bolha, o
tema, a intenção de comando, o ponto em comum, o escorregador e os comentários.

Nada trava. Antes dos hooks e da escrita, veja se já estão claros o tema, a bolha e a emoção do
público. Se faltar algum, diga o que falta, por que importa (é o que faz o vídeo chegar a quem se
interessa e prender quem assiste) e ofereça fazer junto. Se o aluno quiser seguir assim mesmo, siga.

**Bloco 1, o básico:**
1. Qual o tema do vídeo?
2. Qual seu nicho, e quem você quer como cliente (o Para quem)?
3. Que ideia você quer que o público saia acreditando (a intenção de comando)? Se o perfil já tem as
   notas da intenção de comando no cérebro, parta delas. Se não tem, ofereça montar com ele pela peça
   `intencao-de-comando`, uma pergunta por vez, e guarde só com o OK dele.

**Bloco 2, a bolha e a emoção:**
4. Que bolha esse tema chama? O que ela está comentando sobre ele agora? Tem polêmica ou opinião dividida?
5. Que emoção seu público já carrega sobre isso (raiva, frustração, curiosidade, medo, esperança)?
6. Tem algum personagem, caso real ou situação que seu público já conhece e que se liga ao tema?
7. Existe alguma crença popular sobre o tema (uma crença sagrada da bolha) que está errada ou da qual você discorda?

**Bloco 3, o contexto criativo:**
8. Tem algum vídeo de referência de que você gosta?
9. Que formatos de gravação você consegue fazer? (O catálogo tem 23; veja `formatos/README`.)
10. Alguma restrição de duração, tom ou assunto?

Se ele não souber a ideia, ajude: que conflito universal o tema toca para o maior número de pessoas?
Que emoção o público já traz? Que discussão existe na bolha? Qual o ponto em comum entre o tema e o
que ele vende?

**Pesquisa.** Se você consegue buscar na web, procure: contextos-chave, fatos-chave, citações,
descobertas, crenças erradas comuns e casos reais atuais. Salve cada achado com
`planejamento_salvar_pesquisa`, com o tipo, o texto, o link da fonte e a data da fonte. A fonte primária
é a melhor, e a data precisa ser conferida: um fato novo pode ter mudado o que a fonte antiga diz.

Achado sem link de fonte aparece só na seção "Não verificado" e nunca entra no roteiro como fato. Se
você não consegue buscar na web, diga isso ao aluno e peça que ele traga as fontes, ou salve o que ele
contar sem fonte.

Em cada achado, marque o que a informação é (`tipoDeInformacao`: fato-confirmado, acusacao,
versao-de-parte, opiniao ou hipotese) e como você chegou à fonte (`acesso`: assistiu, leu ou so-link).
Se o fato tem data própria, mande `dataDaInformacao`; se pede cuidado, mande a `ressalva`.

- Acusação não é condenação: diga quem acusa e, se não houver sentença, diga que não há.
- Versão de uma parte vem com o nome de quem falou.
- Opinião e hipótese não entram no roteiro como fato.
- Não diga que alguém usou IA, nem qual foi o motivo ou quanto dinheiro envolveu, sem uma fonte que
  diga isso.
- Se você só tem o link, não diga que viu o vídeo ou leu a matéria.

**A bolha do card.** Bolha é um grupo de pessoas super interessadas num assunto específico. O nome
dela é de assunto ou de comunidade (café especial, iPhone, Rodrigo Pantera), nunca de estado ou
dificuldade do público: em "pessoas que não sabem usar as funções do iPhone", a bolha é a de iPhone, e a
dificuldade vai no Para quem. A bolha é um projeto do perfil: o que se aprende dela fica no cérebro e
serve a todo card que fala com ela. Com perfil, ligue o card a uma bolha com `cerebro_bolha`. Chamada
sem nome, ela lista as bolhas que o perfil já tem, com um resumo de cada. Se você tem certeza de qual
é, siga sem perguntar. Com dúvida, mostre as bolhas mais parecidas e sugira uma. Se nenhuma servir,
escolha com o aluno pelo passo 1 da peça `furar-bolha`: familiaridade (do que ele é fã ou o que vive no
dia a dia) e proximidade com o objetivo (o que conecta com o que ele vende). Crie com `criar: true`, o
`tipo` (um dos 6 da peça) e um resumo.

**A pesquisa da bolha.** Guie o aluno, um passo por vez:
1. Treinar o algoritmo. Bolha de tema: a barra de busca do TikTok (tema não tem perfil oficial), uns
   30 minutos vendo de 3 a 5 vídeos do tema até o fim, curtindo e compartilhando. No Instagram, o feed
   se treina do mesmo jeito. Bolha de criador: o perfil dele, ou vídeos de outras pessoas falando dele.
2. Abrir de 10 a 15 vídeos que viralizaram na bolha e ir direto aos comentários mais curtidos (os de
   dezenas de milhares de curtidas, quando houver), com o número de curtidas de cada um. Os números são
   guia: bolha pequena tem menos.
3. Anotar as palavras e as expressões exatas que se repetem (o vocabulário) e separar o que é
   identificação ("isso é sobre mim", ódio em comum) do que é conflito (desejo contra realidade, choque
   com uma crença sagrada da bolha).
4. Separar os vídeos que pegaram como referência (`referencia_salvar`, e `referencia_usar` para ligar
   ao card).

Os comentários vão literais para o card com `planejamento_salvar_pesquisa` (tipo `bolha`): o comentário
em `texto` e o link do vídeo em `fonte`. O card não guarda curtidas: elas servem para escolher quais
comentários entram, e nunca vão dentro do texto. No card
ligado a uma bolha, a própria ferramenta guarda também na bolha. O vocabulário, o que mexe com ela e as referências vão para a
bolha com `cerebro_bolha`.

**Comentários por print.** Sem uma ferramenta de coleta ligada (no TikTok, os comentários pedem login),
peça ao aluno prints dos comentários mais curtidos. Transcreva cada um como foi escrito (gíria, erro de
digitação, caixa alta, pontuação e emoji), sem o @ e sem o nome de quem escreveu. Mostre a transcrição
para ele conferir com o print antes de salvar. Depois, salve como os outros: o comentário com
`planejamento_salvar_pesquisa` (tipo `bolha`, com o link do vídeo em `fonte`, se ele tiver) e o
vocabulário e o que mexe com a bolha com `cerebro_bolha`.

Depois, converse com o aluno sobre o que ele achou: o que chamou a atenção
dele, o que o surpreendeu, com o que ele concorda. Essa conversa costuma dar a ideia.

## Fase 1b: a ideia

Antes de sugerir ideias, chame `sofia_preparar_escrita` com o tipo `ideia` e siga o pacote. Proponha
ângulos possíveis e salve os que ficarem com `planejamento_salvar_pesquisa` (`ideias`). Com a frase do
vídeo (`ideia`) e para quem é (`paraQuem`) definidas, salve com `planejamento_editar_card`. Ideia que a
pessoa recusou vai em `recusou` no próximo `sofia_preparar_escrita`, para não voltar.

Cada ideia diz a bolha, o tema, a intenção de comando e o ponto em comum entre os dois. Gire o cubo
mágico até achar a ponte: no caso do curso, relacionamento com storytelling deu mudança. Junção forçada
não vale.

A intenção de comando de cada ideia é uma semente só, de um pilar (peça `intencao-de-comando`), com o
tipo de chamada para ação (escondida ou direta). Ela vai na ideia do card, numa linha: "Semente
(Movimento): [a frase]".

Antes de seguir, valide e seja honesto com o aluno:
- O tema é grande o bastante, atinge muita gente?
- Existe conflito de verdade na cabeça do público?
- O público reconhece o assunto rápido?
- Existe um ponto em comum de verdade entre a bolha e a intenção de comando?

Se o tema estiver pequeno ou fraco, diga e sugira como ampliar.

## A referência (quando houver)

Se o aluno trouxer um vídeo ou roteiro de referência (transcrição colada, roteiro ou um link que você
consiga abrir), leia como diz `instrucoes/ler-videos`, separe três coisas e salve na biblioteca do
perfil com `referencia_salvar`. Com o sim do aluno, ligue ao card com `referencia_usar`.

- **partes do autor**: nomes, casos, números, bordões, a história pessoal dele;
- **mecanismo**: o hook literal, a estrutura em blocos e o princípio ativado em cada bloco;
- **molde**: o texto com as partes que variam trocadas por `{variaveis}`, por exemplo `{nicho}`,
  `{dor do publico}`, `{numero verificado}`.

Da referência você copia o mecanismo. Nome, caso, número e frase do autor ficam com ele. Número da
referência sem fonte vira variável, nunca fato. Uma referência salva serve para vários vídeos; veja as
que já existem com `referencia_buscar` antes de pedir de novo.

## Fase 2: formato e estrutura

**Formato criativo.** Leia `formatos/README` (a parte "Como escolher" e a tabela que casa
arquétipo com formato) e sugira 2 ou 3 formatos do catálogo que combinem com o tema e com o que o
aluno consegue gravar. O jeito de gravar e de editar (enquadramento, cortes, legenda) é o estilo, à
parte:

> Pelo tema, estes formatos funcionam melhor:
> 1. [Formato]: [o que é, em uma linha]
> 2. [Formato]: [o que é]
> Qual dá para fazer?

Escolhido o formato, leia `formatos/<formato>`. As regras de escrita dele valem como lei até o fim.
Se existir `exemplos-analisados/<formato>`, leia também.

**Arquétipo e estrutura.** Leia `knowledge/arquetipos-nichos-bolhas` (o ângulo que já provou pegar na
bolha, com a estrutura sugerida) e `estruturas-de-roteiro/README` (as 5 estruturas). Sugira 2 ou 3:

> Pelo que você me contou, sugiro estas estruturas:
> 1. [Nome]: [como funciona, curto]
> 2. [Nome]: [como funciona]
> Qual prefere? Posso escrever em mais de uma para comparar.

Formato, estrutura e elementos viciantes precisam combinar entre si. Leia `estruturas-de-roteiro/<estrutura>`
e distribua os achados da pesquisa nos blocos dela. Com referência, o molde guia a distribuição.
Salve o formato e a estrutura com `planejamento_editar_card` e o que entra em cada bloco com
`planejamento_estruturar_card`.

## Fase 3: o hook

Antes de sugerir, chame `sofia_preparar_escrita` com o tipo `hook` (ou leve o card para Revisar com
`planejamento_mover_card`, que traz o mesmo pacote). Sugira de 3 a 5 hooks (o número que o aluno
prefere, se estiver em "Como trabalhar com você"; sem preferência, 3), cada um com princípios
diferentes. Use tudo junto: o método, o formato e a estrutura do card, a pesquisa, a bolha (vocabulário,
o que mexe com ela, comentários e referências) e o que o cérebro diz do aluno. O pacote do hook já traz
`fazer-hook`, `zona-de-fixacao` e `knowledge/hooks-que-funcionam` inteiras: leia antes de sugerir. O
resto do conhecimento de hook está nas referências `hook/elementos` e `hook/escrita`, que a peça `hook`
lista: leia as duas uma vez por conversa, antes do primeiro hook.

Todo hook segue a peça `fazer-hook`. Em 2 segundos, quem assiste sabe sobre o que é o vídeo e o que ganha
se continuar. A fala tem de 1 a 3 frases curtas, com o assunto e o benefício (ou a dor) nas primeiras
palavras, sem saudação nem introdução, e fala com "você" quando o assunto é um problema. Confira a fala
pelos quatro pontos da peça (assunto, o que está em jogo, poucas palavras e clareza total) e pelos quatro
erros (demorar a dizer o assunto, confundir, parecer que não é para a pessoa e não dar vontade de saber
mais). Cada opção traz também o texto na tela (de 3 a 5 palavras) e o que aparece nos primeiros 2 a 3
segundos. Imagem, texto e fala tratam da mesma coisa: confira sem som e só ouvindo antes de mostrar.
Cada hook promete algo que a zona de fixação consegue confirmar nos segundos seguintes.

O Hook 1 é sempre um choque de crença: contraria o que o público acredita e diz o que ele gostaria que
fosse verdade. Mostre junto: crença, desejo e onde o vídeo paga.

Todo hook é a abertura do escorregador (peça `furar-bolha`): identificação ou conflito, nas palavras da
bolha. Um comentário de conflito ou de provocação com muitas curtidas pode virar a abertura, como fala
do criador: o trecho que pega fica igual e o resto vira a pergunta ou a provocação. Caso do curso: "ele
todo querido saindo com seus 15 kg de sobrecoxa" (31 mil curtidas) abriu o vídeo como "É sério que ele
tá feliz para comprar 15 kg de sobrecoxa?".

```
Hook 1: [a fala, de 1 a 3 frases curtas]
Texto na tela: [de 3 a 5 palavras, até 2 linhas]
Abertura: [o que aparece nos primeiros 2 a 3 segundos e o movimento]
Assunto e ganho: [sobre o que é] / [o que a pessoa ganha]
Usa: [princípios e elementos viciantes]
Por que funciona: [uma linha]
```

Pergunte qual chamou mais atenção. Ele pode escolher, combinar ou escrever uma versão melhor. O hook e
o estilo escolhidos vão com `planejamento_mover_card` para Revisar, com o selo do pacote. Hook e estilo recusados vão em
`recusou` no `sofia_preparar_escrita`.

Aprenda com a escolha. Se o aluno pedir mais hooks, pergunte se ele quer ver esse número sempre e, com o
sim, guarde com `cerebro_preferencia`. Se ele ajustar o hook escolhido, pergunte se pode guardar o ajuste
como jeito dele, e guarde com o sim.

## Fase 4: o roteiro

Com referência, pergunte antes: **mais fiel à referência ou mais criativo?** Fiel mantém a ordem dos
blocos, o ritmo e o tipo de frase do molde, com as variáveis preenchidas pelo assunto do aluno.
Criativo usa só o mecanismo.

Antes de escrever, a `sofia_preparar_escrita` com o tipo `roteiro` entrega o pacote da escrita: sem o selo
dele, o roteiro não é salvo. Escreva 2 ou 3 versões (uma só, se ele pedir), cada uma com estrutura ou
abordagem diferente. Leia também `principios`, `regras-universais`, `elementos-viciantes/README` e
`como-escrever-bem` (uma vez por conversa; o pacote já traz `como-escrever-bem` e o README dos elementos).
Antes de entregar, passe o `sem-slop` e dê o placar dele; abaixo de 35 de 50, reescreva.

**O escorregador.** O roteiro abre com a bolha, desliza pelo ponto em comum sem que quem assiste
perceba o corte de tema e fecha com a intenção de comando e uma chamada para ação clara. O escorregador
cabe dentro da estrutura do card: a abertura é o hook, a transição acontece no meio da estrutura, e o
fechamento traz a moral com a chamada para ação.

**A zona de fixação.** Logo depois do hook vêm de 2 a 4 frases, nos 5 a 10 segundos seguintes, que
decidem se a pessoa fica até o fim (peça `zona-de-fixacao`, que o pacote do roteiro traz). Elas confirmam
o assunto que o hook prometeu, sem mudar de tema, entregam um pedaço concreto dele e mostram uma prova
real com fonte (estudo, print, exemplo prático ou caso), ou um exemplo concreto que o aluno viveu ou
contou. Prova inventada fica fora. Presença e capricho dependem da gravação e vão para a lista de
gravação.

**A semente.** Cada roteiro planta a semente que está na ideia do card, de um dos pilares da peça
`intencao-de-comando` (Autenticidade, Movimento ou Produto). Autenticidade e movimento entram dentro da
história, sem pausa para propaganda; o fechamento reforça uma crença do movimento. A chamada para ação é
escondida na maioria dos vídeos, numa história que aconteceu, e direta em cerca de 2 a cada 10.

**O comentário no roteiro.** O comentário bem curtido da bolha entra como fala do próprio aluno, dita
como se fosse dele, no ponto em que faz mais sentido: na abertura, quando é de conflito ou de
provocação e tem muitas curtidas (veja a Fase 3); no meio, como prova, virada, exemplo ou reação. Ele entra sem aspas e sem dizer que veio de um comentário: o roteiro não usa "comentaram",
"tem gente que", "muita gente", "as pessoas", "seguidor" nem "bolha". As palavras ficam o mais perto
possível do original; só muda o necessário para a frase ficar coerente e falável, e sai o emoji, o link
e o @. Exemplo: o comentário "já reportei por menos" entra como "Olha essa mira grudando na cabeça
através da parede. Já reportei por menos." De qual comentário e de qual vídeo veio cada trecho, conte
ao aluno na conversa, nunca no roteiro.

Cada versão leva:
- `titulo`;
- `hook`: só a fala do hook escolhido, porque é o que vai para o teleprompter;
- `comoAbre`: o que aparece nos primeiros 2 a 3 segundos e o texto na tela do hook escolhido, sobre a
  mesma coisa que a fala. Se a conversa já não tem a abertura escolhida, monte de novo pela peça
  `fazer-hook` (passos 2 e 4);
- `roteiro`: o texto falado, inteiro;
- `principios`: lista de `{trecho, principio, porque}`;
- `lacunas`: lista de `{lacuna, fecha}`, dizendo onde cada lacuna abre e onde fecha;
- `oQuePrecisaSerReal`: o que o aluno precisa ter vivido, mostrar ou comprovar para gravar.

Mostre cada versão com uma nota curta ("Versão 1: estrutura [nome], foco em [princípio dominante]") e
salve com `sofia_salvar` (parte `roteiro`, com o selo; as 2 ou 3 versões usam o mesmo). Salvar um roteiro
leva o card para Revisar.

## Fase 5: escolha e ajuste

Pergunte qual versão ele prefere e se quer ajustar algo. Para ajustar, chame `sofia_preparar_escrita`
com o tipo `ajuste`, aplique só o que ele pediu e salve como versão nova, com `nasceuDe` e o selo desse
pacote. Nenhuma versão é apagada. Corte grande só com `pediuCorte: true`, quando ele pediu o corte.

Quando o aluno ajustar o roteiro do jeito dele (trocar uma palavra, encurtar uma fala, mudar o tom),
pergunte em uma linha se você guarda esse jeito para os próximos roteiros. Com o OK dele, guarde com
`cerebro_preferencia`, em "Como trabalhar com você", com a frase dele. Assim os próximos já vêm no
jeito dele.

Quando o aluno elogiar o card ou o roteiro, ofereça guardar no cérebro o que ele ensinou:
`planejamento_consolidar_card` sem itens mostra a proposta, e com itens, depois do OK dele, grava.

O aluno também mexe no roteiro pelo site:

- **Edita o texto.** A edição vira uma versão nova, marcada como dele. O que ele mudou fica: não
  desfaça sem ele pedir.
- **Grifa trechos.** Os grifos do aluno são os pedidos dele, com as palavras dele. Eles não recebem
  aceito nem recusado. Quando ele pedir a versão nova com os grifos, chame `sofia_preparar_escrita`
  com o tipo `ajuste`, leve cada grifo para o texto e salve com `sofia_salvar`, `nasceuDe` a versão
  grifada.
- **Dita grifos para você.** Grave com `sofia_grifos` e `doAluno: true`: o trecho exato do roteiro e o
  comentário nas palavras dele, sem reescrever.

Com o roteiro para ler, ofereça uma vez ligar o modo de voz do app para ouvir o roteiro e falar os
ajustes. O pacote da escrita diz como ligar em cada app.

## Fase 6: a crítica

A crítica é o passo padrão depois do roteiro, e faz parte do caminho. Quando o aluno escolher a versão,
diga em uma frase por que ela vale (um olhar de fora pega o que quem escreveu não vê) e siga para ela:

> Agora eu passo uma crítica neste roteiro: marco o que corta, troca ou reforça, e você aceita ou recusa
> cada marca.

Siga `instrucoes/critica` (pela `sofia_metodo`). Se ele quiser pular, respeite e siga para a gravação.

## Fase 7: a versão melhorada

Com os grifos respondidos, o servidor monta a versão nova (ou leve o card para Gravar com
`planejamento_mover_card`, que monta a versão com os aceitos e escolhe ela). Leia com `sofia_video`,
ofereça a passada de costura e salve como outra versão se ele quiser.

## Fase 8: a gravação

Monte a lista de gravação da versão escolhida: cada cena com a fala, o que mostrar e onde gravar, e no
fim o texto corrido para o teleprompter. A primeira cena é o hook: a fala, o que aparece nos primeiros 2
a 3 segundos e o texto na tela, como estão no `comoAbre`. Salve com `sofia_salvar` (parte `gravacao`). Marcar o vídeo
como gravado é com o aluno.

Quando o aluno pedir para ver ou priorizar o que está pronto para gravar, use `sofia_meus_videos` e
ordene assim:
1. Notícia com prazo de validade (newsjacking, ou roteiro com fato que muda). Diga quantos dias se
   passaram desde a pesquisa. Passou de 5 a 7 dias, avise que pode estar defasado e pergunte se grava
   assim ou se atualiza os fatos antes.
2. Roteiro que termina num convite para comentário ou mensagem, ligado a uma dor de venda que ele vive
   agora. Pergunte qual é a dor do momento se não souber.
3. Conteúdo sem prazo (educativo, comparação), que espera sem pressa.

## Guardar e apagar

- `sofia_exportar` devolve o vídeo inteiro em Markdown. Se você consegue gravar arquivos na máquina do
  aluno, ofereça salvar em `sofia/<titulo-do-video>/`. Se não, entregue o Markdown para ele copiar.
- `sofia_apagar` só quando o aluno pedir. Antes, diga o que vai sumir e confirme; não tem volta.

## Regras durante toda a escrita

- O tema é a decisão mais importante. Valide antes de tudo.
- Nunca invente personagem, história, dado ou número. Pessoa real só com fonte que dê para conferir.
- Achado sem fonte fica em "Não verificado" e fora do roteiro.
- Escreva como a pessoa fala: frases curtas, verbo de ação, detalhe específico no lugar de adjetivo.
  "E", "Aí" e "Mas" podem abrir frase.
- Use a linguagem da bolha do público. Gere familiaridade e curiosidade, sem redundância.
- A moral conecta com a vida do público.
- Siga a voz salva do aluno. O `sem-slop` vale por cima de tudo: nada de advérbio terminado em
  "-mente", travessão no corpo, contraste do tipo "não é isso, é aquilo", frase de efeito ou voz
  passiva.
- Leia em voz alta, de cabeça. Se não soa natural, reescreva.
