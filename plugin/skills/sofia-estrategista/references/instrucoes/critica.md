# Criticar e lapidar um roteiro

> Cópia da peça `instrucoes/critica` do método (gerada do webapp, método 9cfc1c460c97). Com o conector ligado, vale a versão de `sofia_metodo` com `instrucoes/critica`, que é a mais nova. Não edite à mão: o arquivo é regerado.

Você vai ler uma versão do roteiro e marcar o que corta, troca, reforça ou deixa em dúvida. Cada marca
é um grifo salvo com `sofia_grifos`. O aluno aceita ou recusa cada grifo, e o servidor monta a versão
nova sozinho com os aceitos.

## Antes de criticar

Chame `sofia_preparar_escrita` com o tipo `critica`: o pacote traz a versão atual, o card, o cérebro do
perfil e as regras da crítica. Os grifos vão com o selo do fim do pacote (em `selo`); sem ele, não são
gravados. Se a conversa já tem partes de um pacote anterior do card, diga quais em `ja_tenho` e mande o
selo desse pacote em `selo`; sem ele, o pacote vem inteiro. Para ver o resto do vídeo, use
`sofia_video`. Se faltar algo que muda a crítica, faça uma ou duas perguntas, no máximo:

- Para quem é?
- O que a pessoa deve fazer depois de assistir?
- Em que plataforma vai sair (Reels, TikTok, YouTube Shorts)?

Se já está claro, pule direto.

Para julgar, use o método: `principios`, `diagnostico`, `regras-universais`, `sem-slop` e as regras
do formato escolhido (`formatos/<formato>`), todos pela `sofia_metodo`. O bloco "Vale agora" das
respostas traz o resumo.

**Sem cara de IA.** Antes de grifar, chame `sofia_metodo` com `sem-slop`. Ele serve duas vezes: para
achar no roteiro o que soa como IA (cada ocorrência vira grifo de `trocar` ou `cortar`, com a regra no
comentário) e para conferir cada sugestão sua antes de entregar. O resumo de bolso está em
`sem-slop-resumo`.

## Os grifos

Cada grifo tem quatro campos:

- **trecho**: o texto do roteiro, copiado letra por letra. Se a frase aparece mais de uma vez, pegue um
  pedaço maior, que só exista num lugar. Sem o trecho exato o servidor não acha onde trocar.
- **tipo**, um destes:
  - `cortar`: o trecho sai. A sugestão fica vazia.
  - `trocar`: o trecho sai e entra a sugestão.
  - `reforcar`: o trecho funciona e pode render mais. A sugestão é a versão mais forte.
  - `duvida`: algo que só o aluno sabe responder (um fato, um dado, uma história dele). O texto não
    muda; a sugestão é a pergunta.
- **comentario**: uma ou duas frases. Diga o problema e nomeie o princípio entre parênteses, por
  exemplo "(Curiosidade) A lacuna fecha na segunda frase; segure o número até o fim."
- **sugestao**: o texto que entra no lugar, pronto para falar. Passe o `sem-slop` em cada sugestão e
  respeite a voz salva do aluno.

O que funciona bem também merece grifo de `reforcar` quando dá para render mais. Se funciona e não há
o que melhorar, diga no diagnóstico, sem grifo.

Trecho que veio de um comentário do público é fala do próprio criador: mantenha as palavras e só grife
se ficar incoerente. Mesmo aí, a sugestão fica o mais perto possível do comentário, sem aspas e sem
dizer de onde veio.

Ordem: o maior problema primeiro. Abertura e gancho costumam ser o maior.

**O hook.** Confira pela peça `fazer-hook` (pela `sofia_metodo`):

- Em 2 segundos dá para saber sobre o que é o vídeo e o que a pessoa ganha se continuar?
- A imagem dos primeiros 2 a 3 segundos, o texto na tela (no `comoAbre`) e a fala tratam da mesma coisa?
- Tem saudação, introdução ou frase vazia antes do assunto? Frase longa, passiva ou com palavra difícil?
- Quando o assunto é um problema, a fala se dirige a quem assiste, com "você"?
- O hook abre curiosidade, com um contraste concreto, ou só informa?
- O segundo seguinte entrega valor, ou o roteiro enrola e muda de assunto?

**A zona de fixação.** Confira as 2 a 4 frases depois do hook pela peça `zona-de-fixacao`:

- Ficam no assunto que o hook prometeu, sem mudar de tema?
- Entregam um pedaço concreto da promessa?
- Mostram uma prova real, com fonte, ou um exemplo concreto que o aluno viveu ou contou?
- A bolha se reconhece nelas, num detalhe do dia a dia e nas palavras dela?
- Presença e capricho estão na lista de gravação?

Cada falha vira grifo, com a sugestão pronta para falar.

## O diagnóstico na conversa

Junto com os grifos, escreva um diagnóstico curto:

```
Ideia central: [1 frase]
O que segura: [o ponto forte]
O que derruba: [o maior problema e como resolver]
Abertura: segura / mais ou menos / não, [1 frase: assunto e ganho em 2 segundos? imagem, texto e fala alinhados?]
Zona de fixação: segura / mais ou menos / não, [1 frase: a promessa se confirma? tem prova?]
Onde desiste: [o ponto exato e por quê]
Princípios que faltam: [nome, e onde encaixaria]
Veredicto: segura até o fim? faria compartilhar? vale postar? (sim / ajustar / não)
```

Antes de apontar falta, diga o que está carregando o vídeo.

## Depois dos grifos

1. Grave os grifos com `sofia_grifos`, ou leve o card para Lapidar com `planejamento_mover_card` e os
   grifos juntos: ele grava e move. Grifo repetido não entra de novo. Mostre os grifos ao aluno e peça
   para aceitar ou recusar cada um. Na tela da Sofia ele clica; por texto, você registra cada resposta
   com `sofia_grifos`.
2. Quando todos estiverem respondidos, o servidor monta a versão nova: troca cada trecho aceito pela
   sugestão, apaga os de `cortar` e não mexe nos de `duvida`. Se algum trecho não foi achado, a
   resposta lista quais; mostre ao aluno e combine a troca à mão.
3. Leia a versão nova com `sofia_video` e ofereça uma passada de costura: emendas entre frases que
   ficaram soltas, ritmo, o gancho no lugar. Se o aluno quiser, salve a costura como outra versão com
   `sofia_salvar` (parte `roteiro`, com `nasceuDe`), depois de `sofia_preparar_escrita` com o tipo
   `ajuste`.
4. Respostas de `duvida` que trouxerem fato novo precisam de fonte. Sem fonte, o fato vai para "Não
   verificado" e fica fora do roteiro.

## Os grifos do aluno

O aluno também grifa, no site ou ditando para você. O grifo dele é o pedido dele: não recebe aceito nem
recusado e não segura a montagem. Na montagem, o corte e a troca que ele pediu entram junto com os seus
grifos aceitos. Não critique um grifo dele como se fosse seu, e não desfaça o que ele editou no site sem
ele pedir. Se ele ditar um grifo, grave com `sofia_grifos` e `doAluno: true`, com as palavras dele.

## Regras

- Conciso: uma ou duas frases por ponto, sem repetir.
- Todo problema vem com sugestão.
- Nomeie o princípio, sempre, entre parênteses.
- Honesto: se funciona, diga; se não, diga o que fazer.
- Nunca invente dado, caso ou personagem na sugestão.

## O olho de quem assiste

Leia o roteiro como quem rola o feed e confira:

- **CR1.** O tema faz parar e a moral cabe em uma frase.
- **CR2.** A primeira frase desperta uma emoção.
- **CR3.** Existe conflito, e a mudança aparece.
- **CR4.** O hook abre uma pergunta e o roteiro responde.
- **CR5.** Todo nome tem contexto antes.
- **CR6.** Uma criança de 8 anos entende na primeira vez que ouve.
- **CR7.** Três frases seguidas não têm o mesmo tamanho, e nenhum parágrafo termina em frase de efeito.
