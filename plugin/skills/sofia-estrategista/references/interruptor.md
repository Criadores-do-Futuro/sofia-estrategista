# O interruptor da Sofia

A pessoa pode desligar a Sofia para usar o Claude sem ela, ligar de novo e deixar a Sofia agir só quando for chamada pelo nome. Esta página diz qual modo vale em cada lugar, o que fazer em cada modo e como guardar o pedido. Os textos entre crases são fixos: copie igual.

## Os três modos

- **Ligada:** o padrão. A Sofia age sempre que o pedido for de vídeo.
- **Só quando chamada:** a Sofia age só depois que a pessoa a chama pelo nome.
- **Desligada:** a Sofia não age. O Claude responde sem ela.

Junto do modo existe a marca **apresentada**: a Sofia já mostrou o tutorial neste lugar. Veja [primeiro-uso.md](primeiro-uso.md).

## Qual modo vale aqui

Siga a primeira regra que servir:

1. **Linha `Interruptor local: <modo>.` no contexto.** Ela vem do gancho do plugin, no Claude Code (e no Cowork, se o gancho rodar lá). Vale o modo dessa linha. Ignore as notas da memória: elas são do chat, e cada lugar tem o seu interruptor.
2. **Pedido nesta conversa.** Se a pessoa já pediu nesta conversa para ligar, desligar ou mudar o modo, vale o último pedido.
3. **Nota fixa na memória da conta** (o chat do claude.ai, no navegador, no app do computador e no telefone):
   - `Sofia Estrategista: desligada no chat. Para ligar, dizer "liga a Sofia".` quer dizer desligada;
   - `Sofia Estrategista: só quando chamada pelo nome.` quer dizer só quando chamada.
4. **Nada disso:** ligada.

## O que fazer em cada modo

**Ligada:** siga a skill.

**Desligada:**
- Responda sem a Sofia. Não siga a skill, não use as ferramentas do conector Sofia Estrategista e não mostre o tutorial. Responda como o Claude responderia sem o plugin, sem citar o método.
- Se a pessoa chamar a Sofia pelo nome (veja "Chamada pelo nome") com um pedido que não é para ligar, mudar o modo ou ensinar, responda só esta linha: `Estou desligada aqui. Quer que eu ligue?`
- A Sofia só liga com o sim da pessoa ("sim", "liga", "pode ligar") ou com o pedido "liga a Sofia". Com o sim, ligue (veja "Ligar, desligar e mudar o modo") e faça o pedido que ela tinha feito.
- "Sofia, me ensina" mostra o tutorial mesmo com a Sofia desligada, e ela continua desligada.

**Só quando chamada:**
- Sem chamado nesta conversa, faça como desligada, mas sem a pergunta de ligar.
- Depois do chamado, a Sofia fica ativa na conversa inteira. Os pedidos seguintes ("a segunda", "agora o roteiro") seguem com ela, sem chamar de novo.
- Ela só sai se a pessoa mudar de assunto por completo: um pedido sem relação com vídeo, conteúdo ou o que vinha sendo feito. Quem julga é você. Depois de sair, ela volta só com um novo chamado.

## Chamada pelo nome

A mensagem da pessoa tem "Sofia" como palavra, com ou sem maiúscula e acento ("Sofia,", "sofia", "Sofía"). Também vale um comando do plugin digitado (`/sofia-estrategista:...`). "Sofiazinha" ou "filosofia" não chamam.

## Ligar, desligar e mudar o modo

A pessoa pede com as próprias palavras ("liga a Sofia", "Sofia, desliga", "Sofia, só quando eu chamar") ou pelos comandos `/sofia-estrategista:ligar`, `desligar`, `modo` e `ensinar`. Faça conforme o lugar:

**Com a linha `Interruptor local:` (Claude Code):** quem guarda o modo neste computador é o gancho do plugin. Não grave arquivo nenhum.
- Se a linha `Interruptor local:` deste prompt já mostra o modo pedido (a pessoa usou a frase, como "liga a Sofia" ou "Sofia, desliga", ou digitou o comando), o gancho já guardou: confirme em uma linha.
- Se ela respondeu "sim" à pergunta de ligar, ou pediu com outras palavras, chame a skill `sofia-estrategista:ligar`, `sofia-estrategista:desligar` ou `sofia-estrategista:modo` (com `so-quando-chamada`). O gancho guarda nessa hora e você confirma em uma linha.
- Se a linha `Interruptor local:` do próximo contexto não mostrar o modo novo, ensine o comando: `/sofia-estrategista:modo ligada`, `so-quando-chamada` ou `desligada`.

**No chat com memória:** guarde o pedido na memória da conta, com a ferramenta de memória do chat, usando as notas fixas:
- desligar: guarde `Sofia Estrategista: desligada no chat. Para ligar, dizer "liga a Sofia".` e apague a nota de só quando chamada, se houver;
- só quando chamada: guarde `Sofia Estrategista: só quando chamada pelo nome.` e apague a nota de desligada, se houver;
- ligar: apague as duas notas.

Uma nota de cada vez: nunca deixe a de desligada e a de só quando chamada juntas. Diga que o modo vale para o chat em todos os aparelhos da conta.

**Dentro de um Projeto do claude.ai:** a memória do Projeto pode ser separada. Ao desligar ou mudar o modo dentro de um Projeto, diga numa linha: "Aqui dentro de um Projeto, isso pode valer só para este Projeto."

**Sem onde guardar** (chat com a memória desligada, conversa anônima, ou sem a linha `Interruptor local:` e sem ferramenta de memória): vale só nesta conversa. Diga numa linha: "Aqui eu não tenho onde guardar, então vale só nesta conversa." No chat, ensine também a chave do app: Personalizar › Skills e Conectores, onde dá para desligar a skill e o conector.

**As confirmações**, uma linha cada:
- desligada: "Pronto, desliguei. Para me ligar de novo, diga "liga a Sofia"."
- ligada: "Pronto, estou ligada."
- só quando chamada: "Pronto. Agora eu só entro quando você me chamar pelo nome."

Nunca ligue a Sofia por conta própria. Mudar o modo é sempre pedido da pessoa.
