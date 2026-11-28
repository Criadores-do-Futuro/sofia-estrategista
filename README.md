# Sofia Estrategista

A Sofia Estrategista do curso Criador Estrategista, dos Criadores do Futuro: estrategista e editora de vídeo curto, numa Sofia só. O plugin junta o método do curso (ideia, pesquisa com fonte, formato, estrutura, hook, roteiro, grifos, análise de vídeo e de perfil), a equipe de agentes que escreve e confere cada etapa, o conector do planejamento do site e a edição do vídeo gravado no CapCut ou no DaVinci Resolve. O que o plugin faz, para quem usa, está em [plugin/README.md](plugin/README.md).

Este repositório é o marketplace `criadores-do-futuro`, com dois plugins: a `sofia-estrategista` e o `sofia-painel`. A versão atual da Sofia é a **2.3.0**: ela aprende a prospecção (alvos, presentes e acompanhamento) e o guia de cena, com as ferramentas novas do conector. A 2.2.1 fez do marketplace o caminho ensinado em todo app (o arquivo do kit fica como alternativa) e deu ao repositório o pacote de envio ao diretório da OpenAI, em `openai/`. Na 2.2.0, o painel do Claude Code e o interruptor técnico (um mod) saíram dela e viraram o plugin `sofia-painel` 1.0.0, só do Claude Code ([painel-plugin/README.md](painel-plugin/README.md)). Sem o mod, a Sofia carrega no chat, no Cowork e no Claude Code. A 2.1.1 fez a descrição caber no limite de 500 caracteres do envio pelo app. A 2.1.0 trouxe o interruptor: a Sofia liga e desliga com um pedido e pode agir só quando chamada pelo nome. A 2.0.0 foi a Sofia única: a Sofia Estrategista (`sofia-estrategista`) e a Sofia Estrategista com edição (`sofia-estrategista-editora`) viraram um plugin só, o `sofia-estrategista`.

## Instalar

Pelo marketplace, em todo app: é o caminho que recebe as versões novas. O arquivo da página Conector do site fica como alternativa, para quem não conseguir pelo marketplace.

**Claude Code**

```bash
claude plugin marketplace add Criadores-do-Futuro/sofia-estrategista
claude plugin install sofia-estrategista@criadores-do-futuro
claude plugin install sofia-painel@criadores-do-futuro   # opcional: o painel e o interruptor, só no Claude Code
```

Depois, `/reload-plugins` (ou uma sessão nova) e `/mcp` para entrar no conector com o e-mail do curso. Para as próximas versões chegarem sozinhas, digite `/plugin`, abra a aba Marketplaces, escolha `criadores-do-futuro` e ligue a atualização automática.

**Claude no site, no app de computador, no celular e no Cowork:** adicione o marketplace `Criadores-do-Futuro/sofia-estrategista` em Personalizar › Plugins, instale a Sofia Estrategista, ligue a sincronização automática do marketplace e conecte o conector na aba Conectores do plugin. A Sofia fica na conta e chega também ao Claude Code que entra com a mesma conta. O passo a passo está na página Conector do site do curso.

**Codex e app do ChatGPT no computador**

```bash
codex plugin marketplace add Criadores-do-Futuro/sofia-estrategista
codex plugin add sofia-estrategista@criadores-do-futuro
codex mcp login sofia-estrategista
```

O app do ChatGPT para Mac e Windows lê o mesmo marketplace: reinicie o app e instale a Sofia em Plugins. No ChatGPT de empresa ou escola, quem administra importa este repositório em Admin › Plugins › Add › Import marketplace. O envio ao diretório da OpenAI, para o site e o celular de conta pessoal, está em [docs/envio-openai.md](docs/envio-openai.md).

## Já tem uma Sofia instalada?

Quem tem a `sofia-estrategista-editora` (de qualquer marketplace), ou a `sofia-estrategista` vinda de outro marketplace (como o `sofia-plugins`), troca uma vez. Copie o texto abaixo e cole no Claude Code: ele acha as Sofias antigas, mostra o que vai fazer, pede o OK, desinstala as antigas e instala esta pelo marketplace `criadores-do-futuro`. O conector da conta não muda: o que está salvo no site continua lá.

```text
Quero trocar a minha Sofia pela Sofia Estrategista 2.0.0. Agora ela é uma Sofia só, com a edição de vídeo dentro, e vem do marketplace criadores-do-futuro. Faça nesta ordem e não mexa em mais nada:

1. Rode claude plugin list e claude plugin marketplace list. Ache as Sofias antigas: toda sofia-estrategista-editora, de qualquer marketplace, e a sofia-estrategista que veio de um marketplace diferente do criadores-do-futuro. Os outros plugins ficam, inclusive as outras Sofias (sofia-br, sofia-latam, sofia-english, sofia-interna).
2. Me mostre o que achou e diga em uma frase o que vai fazer. Só rode comando que muda alguma coisa depois do meu OK.
3. Desinstale cada Sofia antiga pelo nome que a lista mostra, no formato nome@marketplace: claude plugin uninstall <nome@marketplace>. Se a lista mostrar um escopo diferente de user, acrescente --scope com esse escopo.
4. Se o marketplace sofia-editora existir e nenhum plugin instalado vier mais dele, remova: claude plugin marketplace remove sofia-editora. Não remova o sofia-plugins, nem outro marketplace que ainda tenha plugin instalado.
5. Se o marketplace criadores-do-futuro já existir, atualize: claude plugin marketplace update criadores-do-futuro. Se não existir, adicione: claude plugin marketplace add Criadores-do-Futuro/sofia-estrategista
6. Instale: claude plugin install sofia-estrategista@criadores-do-futuro. Se ela já estiver instalada por esse marketplace, rode claude plugin update sofia-estrategista@criadores-do-futuro.
7. Rode claude plugin list de novo e confira que a sofia-estrategista@criadores-do-futuro está na versão 2.0.0 ou acima. Se não estiver, me diga a versão que apareceu.
8. Me explique como ligar a atualização automática, que é pela tela: digitar /plugin, abrir a aba Marketplaces, escolher criadores-do-futuro e ligar o auto-update.
9. Peça para eu digitar /reload-plugins, ou abrir uma sessão nova, para a Sofia nova valer.

Se o comando claude não rodar aqui, me guie para fazer o mesmo pela tela do /plugin. O conector Sofia Estrategista da minha conta continua como está, com tudo o que salvei no site: não mexa nele.
```

## Atualizar

Dentro da Sofia, o atalho `/atualizar` mostra o caminho de cada app e, no Claude Code, roda os comandos depois do OK. Pelo terminal:

```bash
claude plugin marketplace update criadores-do-futuro
claude plugin update sofia-estrategista@criadores-do-futuro
claude plugin install sofia-painel@criadores-do-futuro   # quem usava o painel, a partir da 2.2.0
```

Quem já tem o `sofia-painel`: `claude plugin update sofia-painel@criadores-do-futuro`. No Codex: `codex plugin marketplace upgrade criadores-do-futuro`.

## Pastas

| Pasta | O que tem |
|---|---|
| `plugin/` | O plugin em si: manifestos do Claude (`.claude-plugin/plugin.json`) e do Codex (`.codex-plugin/plugin.json`), `.mcp.json` com o conector, as skills (`sofia-estrategista`, `sofia-editora`, `beditor` e `motion-vox`), atalhos (inclusive `ligar`, `desligar`, `modo` e `ensinar`), agentes, os scripts e o pacote `beditor/` da edição, `docs/` de uso, README e LICENSE. Sem `hooks/` desde a 2.2.0 |
| `painel-plugin/` | O plugin `sofia-painel`: o mod do painel e do interruptor no Claude Code (`hooks/register.tsx`, `hooks/interruptor.ts` e os testes), o contrato do estado (`types/`), README e LICENSE. Depende da `sofia-estrategista` |
| `.claude-plugin/marketplace.json` | O catálogo `criadores-do-futuro`, com os dois plugins, para instalar pelo Claude Code direto deste repositório |
| `.agents/plugins/marketplace.json` | O catálogo do Codex, com o mesmo nome e só a `sofia-estrategista` (o Codex não roda mod) |
| `scripts/empacotar.sh` | Monta `dist/sofia-estrategista.zip` (o plugin numa pasta, para enviar no Claude e instalar no Codex), a cópia `dist/sofia-estrategista.plugin` e `dist/sofia-estrategista.skill` (só a skill) |
| `openai/` | O `plugin.json` (formato Agent Plugins, com a ficha, os casos de revisão, as notas da versão e a tradução) e o `mcp.json` (o conector com o OAuth) do pacote de envio ao diretório da OpenAI |
| `scripts/empacotar-openai.sh` | Monta `dist/sofia-estrategista-openai.zip`, o pacote de envio ao diretório da OpenAI, e confere com o `scripts/validar_pacote_openai.py` (o passo a passo do portal está em `docs/envio-openai.md`) |
| `scripts/conferir-ferramentas.mjs` | Confere se toda ferramenta citada no plugin existe no conector |
| `tests/` | Os testes do plugin (pacote, equipe, catálogos, scripts de análise, pontes dos editores, motion). Ficam fora do pacote. Os testes do bEditor ficam em `plugin/skills/beditor/tests/`. Os do mod (`painel-plugin/hooks/*.test.ts`) ficam dentro do `sofia-painel`, porque o `claude plugin test` só os acha ali: quem instala o `sofia-painel` recebe os dois arquivos junto (são inertes: o mod não os carrega) |
| `docs/desenho.md` | Por que o plugin é assim: regras, escolhas e o que fica para depois |
| `docs/diretorios.md` | O que falta para enviar aos diretórios da Anthropic e da OpenAI |
| `docs/envio-openai.md` | O envio ao diretório da OpenAI (ChatGPT e Codex), passo a passo no portal |

## Antes de cada versão

1. `claude plugin validate plugin`, `claude plugin validate --strict painel-plugin` e `claude plugin validate .` sem erro, e `claude plugin test painel-plugin` (os testes do mod) sem falha.
2. `node scripts/conferir-ferramentas.mjs <pasta-do-webapp>` sem ferramenta faltando, com a pasta do webapp na `main` (é a `main` que está no ar). O script não confere os campos de cada ferramenta: confira à mão os que o plugin cita, como `nasceuDe`, `pediuCorte` e `escolhidoPeloAluno`.
3. `python3 -m unittest discover -s tests` sem falha. Com `SOFIA_WEBAPP=<pasta-do-webapp>`, a lista de ferramentas do teste também é comparada com o servidor. Os do bEditor: `cd plugin/skills/beditor && python3 -m unittest discover -s tests`.
4. Suba a versão em `plugin/.claude-plugin/plugin.json`, em `plugin/.codex-plugin/plugin.json`, em `openai/plugin.json` (com as notas da versão em `publication.release_notes`), na entrada do `.claude-plugin/marketplace.json` e na seção "Versão e atualização" da skill ("Esta é a versão X.Y.Z": o conector compara esse texto). Mudou o `sofia-painel`? Suba a versão em `painel-plugin/.claude-plugin/plugin.json` e na entrada dele no catálogo.
5. `bash scripts/empacotar.sh` e copie os arquivos de `dist/` para `public/kit/` do webapp. Para o diretório da OpenAI, rode depois `bash scripts/empacotar-openai.sh` (o `empacotar.sh` limpa a pasta `dist/`) e siga `docs/envio-openai.md`.

As referências marcadas como "Cópia da peça" e o `cartas.md` (em `plugin/skills/sofia-estrategista/references/`) não se editam aqui: mude a peça no webapp e rode, nele, `npx tsx scripts/exportar-referencias.mts CAMINHO_DESTE_REPOSITORIO/plugin`. O mesmo comando reescreve a linha `disallowedTools` de cada agente da equipe com as ferramentas do conector que gravam (a trava). O `tests/test_equipe.py` acusa arquivo do espelho mudado à mão e agente sem a trava completa.

## Voltar atrás

- **Sem ninguém reinstalar:** o conector desliga a equipe (`SOFIA_EQUIPE=desligada`). O pacote de cada etapa chega sem a seção "Passos e equipe desta etapa", e a Sofia 2.0.0 segue o pacote inteiro na conversa, como antes.
- **Interruptor:** quem não quiser o interruptor não precisa fazer nada, porque o padrão é a Sofia ligada. Quem desligou volta ao padrão dizendo "liga a Sofia" ou, no Claude Code com o `sofia-painel`, apagando o `estado.json` da pasta de dados do `sofia-painel`.
- **Plugin:** a tag `antes-da-sofia-unica` marca a `main` antes da 2.0.0. Como o `update` não volta versão, a volta é uma versão nova (por exemplo 2.0.1) com o conteúdo dessa tag.
