---
description: Atualiza a Sofia Estrategista para a versão mais nova, pelo caminho do app em que a pessoa está.
---

Use a skill `sofia-estrategista`. A versão desta skill está na seção "Versão e atualização" dela. A versão mais nova aparece no começo das instruções do conector e no `onde_estou`. Se as duas forem iguais, diga em uma frase que a Sofia já está na versão mais nova e pare. Sem o conector, não dá para comparar: siga direto para o caminho do app.

Descubra em que app a pessoa está. Se não der para saber, pergunte em uma frase. Mostre só o caminho desse app:

- **Claude Code:** diga em uma frase que vai rodar dois comandos para buscar a versão nova e peça o OK. Com o OK, rode um depois do outro:
  1. `claude plugin marketplace update sofia-plugins`
  2. `claude plugin update sofia-estrategista-editora@sofia-plugins`

  Depois peça para a pessoa digitar `/reload-plugins`, ou abrir uma sessão nova, para a versão nova valer. Quem usa a edição de vídeo pode atualizar tudo de uma vez, com o context-mode junto: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/beditor/scripts/setup.py --atualizar` mostra os comandos, e com `--sim` roda, também só depois do OK.

  Se o segundo comando disser que o plugin não foi instalado por esse marketplace, veja em `/plugin` de qual marketplace a Sofia veio. Se for o `sofia-editora`, rode os mesmos dois comandos com `sofia-editora` no lugar de `sofia-plugins`: ele também recebe a versão nova. Se for outro, explique que é preciso remover a Sofia antiga (em `/plugin`) e instalar de novo pelo passo a passo da página Conector do site do curso. O conector da conta continua ligado, com tudo o que está salvo.
- **Claude, no site ou no app de computador:** com a opção "Sync automatically" do marketplace ligada, a versão nova chega sozinha. Para buscar na hora, abra Customize › Plugins, entre no marketplace e clique em "Check for updates".
- **Codex:** o comando é `codex plugin marketplace upgrade sofia-plugins`. Se você tiver terminal, rode depois do OK da pessoa; se não, mostre o comando para ela rodar. Depois, uma sessão nova.
- **ChatGPT:** em chatgpt.com/plugins, abra a Sofia Estrategista, clique em Refresh e abra uma conversa nova.

Não mexa em mais nada além da Sofia.

Pedido: $ARGUMENTS
