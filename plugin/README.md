# Sofia Estrategista

A estrategista de vídeo curto do curso Criador Estrategista, dos Criadores do Futuro. Ela ajuda a criar vídeos para Instagram, TikTok e YouTube com o método do curso: ideia, pesquisa com fonte, formato, estrutura, hook, roteiro, grifos e análise de vídeo ou de perfil.

## O que vem no plugin

- **Skill `sofia-estrategista`:** o método inteiro (princípios da viralização, elementos viciantes, formatos, estruturas, hooks, pesquisa e checagem de fatos) e o caminho de cada tarefa.
- **Atalhos:** `roteiro`, `ideias`, `pesquisa`, `analisar`, `critica`, `conectar` e `atualizar`. O `/atualizar` mostra o caminho de atualizar a Sofia em cada app e, no Claude Code, só roda os comandos depois do OK da pessoa.
- **Equipe da Sofia** (agentes no Claude Code e no Cowork): quem escreve são `estrategista-de-ideias`, `especialista-em-bolha`, `pesquisador`, `redator-de-hook` e `roteirista`; quem confere são `revisor-o-que-nao-fazer`, `revisor-de-hook`, `revisor-de-voz`, `revisor-de-estrutura`, `revisor-de-fatos`, `especialista-em-bolha` e `critico`. Cada um busca no conector o briefing do seu papel, e todos só leem e devolvem o resultado.
- **Conector Sofia Estrategista:** liga o Claude ao planejamento do aluno no site do curso.

## Versão 1.6.0: a equipe da Sofia

Ideia, hook, roteiro, ajuste e crítica deixam de ser escritos e conferidos numa passada só:

- **Quem escreve** gera mais opções do que mostra, com o método inteiro da etapa e a voz da pessoa.
- **Os revisores** conferem juntos, cada um com uma fatia do método e as regras com código dela (as cartas): o que não fazer, o hook, a voz, a estrutura, os fatos e a bolha. Até 2 rodadas de correção.
- **O conector** manda o plano de cada etapa, o briefing de cada papel e confere por código o que é mecânico. Quando tudo passa, devolve o selo de conferência, que vai junto ao salvar. Texto salvo sem o selo fica marcado como sem conferência.
- **Em cada app:** no Claude Code e no Cowork, os papéis são agentes do plugin; no Codex, subagentes do próprio Codex; no Claude do site e do celular e no ChatGPT, passadas na conversa (`skills/sofia-estrategista/references/passadas.md`).
- **As referências do método** são cópia gerada do conector, com as cartas de cada papel em `cartas.md`, para quando o conector está desligado.

## Como funciona com e sem o conector

Sem o conector, a Sofia trabalha com o método que vem no plugin e entrega tudo no chat.

Com o conector ligado e com login (o e-mail de compra do curso), ela lê os números do perfil, o cérebro e os cards, e salva ideias, pesquisas, roteiros e grifos no site. Também guarda a leitura dos números do perfil, quando a pessoa pede, e o site mostra a evolução semana a semana. Com o YouTube, o Instagram ou o TikTok conectado em Meus dados, a Sofia lê os números direto da rede e o site lê o perfil sozinho toda segunda; sem a rede conectada, a pessoa pode pedir uma tarefa agendada para toda segunda. Toda gravação é contada no chat. Preferências da pessoa só são guardadas com o OK dela, e aparecem na página Cérebro do perfil, onde podem ser apagadas.

## Instalar

- **Claude no navegador ou no app:** baixe o arquivo do plugin na página Kit do site do curso e envie em Personalizar › Plugins › Adicionar › Enviar plugin. Depois, na aba Conectores do plugin, clique em Conectar e entre com o e-mail do curso.
- **Claude Code:** para instalar direto do repositório, no terminal: `claude plugin install sofia-estrategista --marketplace bento-dev-ia/sofia-estrategista`. Dentro do Claude Code: `/plugin marketplace add bento-dev-ia/sofia-estrategista` e depois `/plugin install sofia-estrategista@criadores-do-futuro`. Depois, `/mcp` para entrar no conector.

O passo a passo está em https://criador-estrategista.vercel.app/kit, depois do login com o e-mail do curso.

## Privacidade

O conector só funciona para alunos do curso, depois do login. O que ele guarda e como apagar está em https://criador-estrategista.vercel.app/privacidade.

## English

Sofia Estrategista is the short-form video strategist from the Criador Estrategista course (Brazilian Portuguese). It helps with video ideas, primary-source research, format, structure, hooks, scripts, line-by-line critique, and video or profile analysis, following the course method. It works on its own, and when the Sofia Estrategista connector is connected and signed in with a course account, it reads and saves to the student's planning board on the course website. It asks before remembering a preference, and says what it saved after every write.

## Licença

Pode baixar, instalar e usar para criar o seu conteúdo ou o de clientes. Redistribuir, revender ou publicar cópias não é permitido. O conector é de uso dos alunos do curso. Veja [LICENSE](LICENSE).
