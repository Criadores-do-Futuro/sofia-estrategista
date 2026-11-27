---
description: Desliga a Sofia neste lugar, para usar o Claude sem ela. Para ligar de novo, diga "liga a Sofia".
---

A pessoa pediu para desligar a Sofia.

Siga "Ligar, desligar e mudar o modo" em `references/interruptor.md`, da skill `sofia-estrategista`:

- **Com a linha `Interruptor local:` no contexto (Claude Code com o plugin `sofia-painel`):** o `sofia-painel` guarda o modo neste computador quando este comando roda. Não grave arquivo nenhum.
- **Sem a linha, com memória (o chat, o Cowork e o Claude Code sem o `sofia-painel`):** guarde a nota `Sofia Estrategista: desligada no chat. Para ligar, dizer "liga a Sofia".` e apague a nota `Sofia Estrategista: só quando chamada pelo nome.`, se houver. No chat, vale em todos os aparelhos da conta. Dentro de um Projeto, diga numa linha: "Aqui dentro de um Projeto, isso pode valer só para este Projeto."
- **Sem onde guardar:** vale só nesta conversa. Diga numa linha: "Aqui eu não tenho onde guardar, então vale só nesta conversa." No chat, ensine a chave do app: Personalizar › Skills e Conectores.

Confirme em uma linha: "Pronto, desliguei. Para me ligar de novo, diga "liga a Sofia"." Depois disso, responda sem a Sofia e sem as ferramentas do conector Sofia Estrategista.
