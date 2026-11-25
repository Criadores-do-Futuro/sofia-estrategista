---
description: Liga a Sofia de novo neste lugar, sempre ligada ou só quando chamada pelo nome.
---

A pessoa pediu para ligar a Sofia. Argumento: `$ARGUMENTS`. Vazio quer dizer sempre ligada. "Só quando chamada" (ou parecido) quer dizer o modo só quando chamada.

Siga "Ligar, desligar e mudar o modo" em `references/interruptor.md`, da skill `sofia-estrategista`:

- **Com a linha `Interruptor local:` no contexto (Claude Code):** o gancho do plugin guarda o modo neste computador quando este comando roda. Não grave arquivo nenhum. Confirme em uma linha.
- **No chat com memória:** apague a nota `Sofia Estrategista: desligada no chat. Para ligar, dizer "liga a Sofia".`. Para só quando chamada, guarde `Sofia Estrategista: só quando chamada pelo nome.`; para sempre ligada, apague essa nota também. Dentro de um Projeto, diga numa linha que pode valer só para o Projeto.
- **Sem onde guardar:** vale só nesta conversa. Diga isso numa linha.

Confirme com uma destas linhas: "Pronto, estou ligada." ou "Pronto. Agora eu só entro quando você me chamar pelo nome." Se a pessoa tinha feito um pedido antes de ligar, faça o pedido logo depois, pela skill `sofia-estrategista`.
