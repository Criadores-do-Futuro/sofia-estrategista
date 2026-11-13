# Sofia Estrategista

A estrategista de vídeo curto do curso Criador Estrategista, dos Criadores do Futuro. Ela ajuda a criar vídeos para Instagram, TikTok e YouTube com o método do curso: ideia, pesquisa com fonte, formato, estrutura, hook, roteiro, grifos e análise de vídeo ou de perfil.

## O que vem no plugin

- **Skill `sofia-estrategista`:** o método inteiro (princípios da viralização, elementos viciantes, formatos, estruturas, hooks, pesquisa e checagem de fatos) e o caminho de cada tarefa.
- **Atalhos:** `roteiro`, `ideias`, `pesquisa`, `analisar`, `critica` e `conectar`.
- **Ajudantes** (no Claude Code e no Cowork): `pesquisador`, que pesquisa em fonte primária, e `critico`, que faz a primeira leitura crítica de um roteiro. Os dois só leem e devolvem o resultado.
- **Conector Sofia Estrategista:** liga o Claude ao planejamento do aluno no site do curso.

## Como funciona com e sem o conector

Sem o conector, a Sofia trabalha com o método que vem no plugin e entrega tudo no chat.

Com o conector ligado e com login (o e-mail de compra do curso), ela lê os números do perfil, o cérebro e os cards, e salva ideias, pesquisas, roteiros e grifos no site. Toda gravação é contada no chat. Preferências da pessoa só são guardadas com o OK dela, e aparecem na página Cérebro do perfil, onde podem ser apagadas.

## Instalar

- **Claude no navegador ou no app:** baixe o arquivo do plugin na página Kit do site do curso e envie em Personalizar › Plugins › Adicionar › Enviar plugin. Depois, na aba Conectores do plugin, clique em Conectar e entre com o e-mail do curso.
- **Claude Code:** o plugin enviado no Claude aparece também no Claude Code da mesma conta. Para instalar direto do repositório, no terminal: `claude plugin install sofia-estrategista --marketplace bento-dev-ia/sofia-estrategista`. Dentro do Claude Code: `/plugin marketplace add bento-dev-ia/sofia-estrategista` e depois `/plugin install sofia-estrategista@criadores-do-futuro`. Depois, `/mcp` para entrar no conector.

O passo a passo com imagens está em https://criador-estrategista.vercel.app/kit.

## Privacidade

O conector só funciona para alunos do curso, depois do login. O que ele guarda e como apagar está em https://criador-estrategista.vercel.app/privacidade.

## English

Sofia Estrategista is the short-form video strategist from the Criador Estrategista course (Brazilian Portuguese). It helps with video ideas, primary-source research, format, structure, hooks, scripts, line-by-line critique, and video or profile analysis, following the course method. It works on its own, and when the Sofia Estrategista connector is connected and signed in with a course account, it reads and saves to the student's planning board on the course website. It asks before remembering a preference, and says what it saved after every write.

## Licença

Pode baixar, instalar e usar para criar o seu conteúdo ou o de clientes. Redistribuir, revender ou publicar cópias não é permitido. O conector é de uso dos alunos do curso. Veja [LICENSE](LICENSE).
