---
description: "Mostra ou muda o modo da Sofia neste lugar: ligada, so-quando-chamada ou desligada."
---

Argumento: `$ARGUMENTS`.

**Vazio:** diga em uma linha qual modo vale aqui, pelas regras de "Qual modo vale aqui" em `references/interruptor.md`, da skill `sofia-estrategista`. Na linha seguinte, mostre os três modos: `ligada` (o padrão), `so-quando-chamada` (só age quando você diz "Sofia") e `desligada`. Não mude nada.

**Com um modo:** a pessoa pediu para mudar. Siga "Ligar, desligar e mudar o modo" no mesmo arquivo:

- **Com a linha `Interruptor local:` no contexto (Claude Code com o plugin `sofia-painel`):** o `sofia-painel` guarda o modo neste computador quando este comando roda. Não grave arquivo nenhum.
- **Sem a linha, com memória (o chat, o Cowork e o Claude Code sem o `sofia-painel`):** troque a nota da memória. `desligada` guarda `Sofia Estrategista: desligada no chat. Para ligar, dizer "liga a Sofia".`; `so-quando-chamada` guarda `Sofia Estrategista: só quando chamada pelo nome.`; `ligada` apaga as duas. Fica uma nota de modo só. Dentro de um Projeto, diga numa linha que pode valer só para o Projeto.
- **Sem onde guardar:** vale só nesta conversa. Diga isso numa linha.

Confirme em uma linha, com a frase do modo em `interruptor.md`. Se o argumento não for um dos três modos, mostre os três e pergunte qual.
