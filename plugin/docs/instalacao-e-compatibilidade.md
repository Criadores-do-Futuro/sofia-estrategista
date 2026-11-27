# Instalação e compatibilidade

Os manifestos e catálogos do repositório `Criadores-do-Futuro/sofia-estrategista` preparam a distribuição para o Claude e para o Codex. Eles não provam que tudo funciona em todo host. Instalar o pacote, entrar no conector, conectar o editor e testar uma edição são etapas separadas.

## Claude Code

O catálogo é o `.claude-plugin/marketplace.json` da raiz do repositório (marketplace `criadores-do-futuro`), e o plugin é a pasta `plugin/`.

```sh
claude plugin marketplace add Criadores-do-Futuro/sofia-estrategista
claude plugin install sofia-estrategista@criadores-do-futuro
```

Depois, `/mcp` para entrar no conector Sofia Estrategista. Para desenvolver, carregue um checkout confiável com `claude --plugin-dir CAMINHO_DO_REPOSITORIO/plugin`. Confira o manifesto com `claude plugin validate plugin` e o catálogo com `claude plugin validate .`, os dois na raiz do repositório.
[Documentação oficial dos marketplaces do Claude](https://code.claude.com/docs/en/plugin-marketplaces).

O painel ao lado da conversa e o interruptor técnico são, desde a 2.2.0, o plugin `sofia-painel`, do mesmo marketplace: `claude plugin install sofia-painel@criadores-do-futuro`. Ele é um mod, que só roda no Claude Code, e depende da `sofia-estrategista`. Para desenvolver os dois juntos: `claude --plugin-dir CAMINHO_DO_REPOSITORIO/plugin --plugin-dir CAMINHO_DO_REPOSITORIO/painel-plugin`.

Desde a versão 2.0.0 existe uma Sofia só, a `sofia-estrategista@criadores-do-futuro`. Se a `sofia-estrategista-editora`, ou a `sofia-estrategista` de outro marketplace, também estiver instalada, as skills `sofia-estrategista` aparecem repetidas: troque pelo prompt de migração do README do repositório, que desinstala a antiga. O mesmo vale para o plugin `beditor` antigo: este já traz as skills `beditor` e `motion-vox`, os ajudantes `diretor`, `enriquecedor` e `analista-de-estilo` e os atalhos, agora como `/sofia-estrategista:...` (`aprender` virou `aprender-motion` e `analise` virou `editar-analise`).

Depois de instalar, rode `/sofia-estrategista:setup`: ele confere Python, FFmpeg, Whisper, Node e o resto, e mostra o comando de cada item que falta. Para atualizar: `claude plugin marketplace update criadores-do-futuro` e depois `claude plugin update sofia-estrategista@criadores-do-futuro`, ou a atualização automática do marketplace, ligada em `/plugin`.

## Claude no navegador, no app e no Cowork

O `scripts/empacotar.sh` da raiz do repositório gera `dist/sofia-estrategista.zip`, com o plugin inteiro dentro da pasta `sofia-estrategista/` (a forma que o envio aceita: o `.claude-plugin/plugin.json` dentro de uma única pasta no topo do `.zip`). Envie o `.zip` em Personalizar › Plugins › Adicionar › Enviar plugin e conecte na aba Conectores do plugin.

Desde a 2.2.0 o pacote não leva mod nem `hooks/`. A página de plataformas do Claude diz que o Cowork carrega skills, comandos, agentes e o MCP remoto de um plugin, e o diretório lista um mod só para o Claude Code; até a 2.1.1, com o mod dentro, o Cowork recusava as skills do plugin e só o conector funcionava. O `empacotar.sh` recusa montar o pacote se `hooks/` voltar.

O pacote segue as regras do envio: em `.claude-plugin/` vão só o `plugin.json` e o ícone (o `marketplace.json` fica na raiz do repositório, para instalar pelo GitHub); o ícone também fica em `assets/`; o cabeçalho de cada skill e de cada comando usa só os campos aceitos fora do Claude Code (`name`, `description`, `license`, `compatibility`, `metadata` e `allowed-tools`), porque no chat cada comando vira uma skill. O `tests/test_pacote.py` do repositório confere essas regras, e o `empacotar.sh` roda o `claude plugin validate` na pasta montada antes de fechar o `.zip`.

Se o Safari abrir o `.zip` sozinho ao baixar, baixe de novo pelo Chrome ou desligue a opção de abrir arquivos seguros nos ajustes do Safari. Não comprima a pasta pelo Finder: ele junta a pasta `__MACOSX` ao `.zip`, e o envio deixa de achar o plugin. O método e o conector funcionam em qualquer um desses hosts. A edição usa Python, FFmpeg, os arquivos de vídeo e o editor aberto no computador, então só funciona onde o host dá acesso a eles.

## Codex

O manifesto é `.codex-plugin/plugin.json`, com as skills em `./skills/` e o conector em `./.mcp.json`. O catálogo é o `.agents/plugins/marketplace.json` da raiz do repositório (marketplace `criadores-do-futuro`).

```sh
codex plugin marketplace add Criadores-do-Futuro/sofia-estrategista
codex plugin add sofia-estrategista@criadores-do-futuro
```

Pelo `.zip` do kit, que traz o próprio catálogo (marketplace `sofia-estrategista-local`):

```sh
unzip sofia-estrategista.zip
codex plugin marketplace add ./sofia-estrategista
codex plugin add sofia-estrategista@sofia-estrategista-local
```

O caminho pelo `.zip` foi testado num perfil limpo do Codex CLI 0.160.0, ainda com o nome antigo do plugin: o plugin instala, as quatro skills aparecem e o conector aparece em `codex mcp list` com o endereço do domínio próprio. Ajudantes (`agents/`) são do Claude. O Codex transforma em skill só os comandos sem argumento (`conectar` e `branding`); no Codex, as quatro skills (`sofia-estrategista`, `sofia-editora`, `beditor` e `motion-vox`) fazem o mesmo trabalho sem os atalhos. O `hooks/hooks.json` só declara o painel do Claude Code (`modules`); no teste, o Codex montou a sessão com o plugin sem aviso nem erro. O manifesto marca `requires_local_executor`, porque a edição precisa do computador: o Codex só oferece o plugin onde há execução local. Inicie uma sessão nova depois de instalar e confira se as skills e o conector aparecem.
[Documentação oficial de plugins do Codex](https://developers.openai.com/plugins/build/plugins).

## ChatGPT e outras ferramentas

ChatGPT na web e no celular, GPTs personalizados e outras IAs não rodam este pacote sozinhos nem herdam conectores de outra sessão. Cada host, o acesso aos arquivos, as ferramentas do editor e o login precisam ser comprovados um por um. Os recursos do CapCut variam por cliente: não prometa edição colaborativa, geração ou legenda automática onde essas operações não existem.

## Dependências e privacidade

- O plugin orienta o agente. Ele não inclui o plugin oficial do CapCut, o DaVinci Resolve nem os conectores deles. Instale e conecte cada um pelo canal do fornecedor.
- As fichas do método vêm no plugin, em `skills/sofia-estrategista/references/`. Com o conector ligado, `sofia_metodo` devolve a versão do site, que vale mais.
- Os scripts usam a biblioteca padrão do Python, com dependências opcionais listadas no README (`requirements-editorial.txt`, `requirements-capcut-desktop.txt` e `requirements-motion.txt`). O README também lista tudo o que o plugin roda, envia e baixa. Eles precisam do plugin inteiro: copiar só um `SKILL.md` não instala as ferramentas.
- Não distribua uma pasta de trabalho com vídeos, transcrições, credenciais, dependências ou arquivos locais sem olhar antes. Git e ignore não limpam arquivo já rastreado nem garantem filtro em todo host.
