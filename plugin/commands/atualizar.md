---
description: Atualiza a Sofia Estrategista para a versão mais nova, pelo caminho do app em que a pessoa está.
---

Use a skill `sofia-estrategista`. A versão desta skill está na seção "Versão e atualização" dela. A versão mais nova aparece no começo das instruções do conector e no `onde_estou`. Se as duas forem iguais, diga em uma frase que a Sofia já está na versão mais nova e pare. Sem o conector, não dá para comparar: siga direto para o caminho do app.

Descubra em que app a pessoa está. Se não der para saber, pergunte em uma frase. Mostre só o caminho desse app:

- **Claude Code:** diga em uma frase que vai rodar dois comandos para buscar a versão nova e peça o OK. Com o OK, rode um depois do outro:
  1. `claude plugin marketplace update criadores-do-futuro`
  2. `claude plugin update sofia-estrategista@criadores-do-futuro`

  Desde a 2.2.0, o painel ao lado da conversa e o interruptor técnico do Claude Code são outro plugin, o `sofia-painel`. Se a pessoa usava o painel, ou quer guardar o modo da Sofia neste computador, diga isso em uma frase e, com o OK, rode também `claude plugin install sofia-painel@criadores-do-futuro` (se ele já estiver instalado, `claude plugin update sofia-painel@criadores-do-futuro`).

  Depois peça para a pessoa digitar `/reload-plugins`, ou abrir uma sessão nova, para a versão nova valer. Quem usa a edição de vídeo pode atualizar tudo de uma vez, com o context-mode junto: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/beditor/scripts/setup.py --atualizar` mostra os comandos, e com `--sim` roda, também só depois do OK. Para as próximas versões chegarem sozinhas, a pessoa pode ligar a atualização automática do marketplace `criadores-do-futuro` em `/plugin`, na aba dos marketplaces.

  Desde a versão 2.0.0 existe uma Sofia só, a `sofia-estrategista@criadores-do-futuro`. Se o segundo comando disser que o plugin não foi instalado por esse marketplace, ou se `/plugin` mostrar uma Sofia de antes (a `sofia-estrategista-editora`, ou a `sofia-estrategista` vinda do `sofia-plugins` ou de outro marketplace), a troca é feita uma vez, pelo prompt de migração. Ele está no README do repositório `Criadores-do-Futuro/sofia-estrategista` e na página Conector do site do curso: desinstala a Sofia antiga, adiciona o marketplace `criadores-do-futuro` e instala a Sofia nova, sempre com o OK da pessoa. O conector da conta continua ligado, com tudo o que está salvo.
- **Claude, no site ou no app de computador:** com a opção "Sync automatically" do marketplace ligada, a versão nova chega sozinha. Para buscar na hora, abra Customize › Plugins, entre no marketplace e clique em "Check for updates".
- **Codex:** o comando é `codex plugin marketplace upgrade criadores-do-futuro`. Se você tiver terminal, rode depois do OK da pessoa; se não, mostre o comando para ela rodar. Depois, uma sessão nova.
- **ChatGPT:** em chatgpt.com/plugins, abra a Sofia Estrategista, clique em Refresh e abra uma conversa nova.

Não mexa em mais nada além da Sofia.

Pedido: $ARGUMENTS
