# Sofia Estrategista

A Sofia Estrategista do curso Criador Estrategista, dos Criadores do Futuro, numa Sofia só: o método, o conector e a edição de vídeo. Um plugin só, para o Claude e para o Codex, que junta:

- **a Sofia Estrategista:** o método do curso inteiro (princípios da viralização, elementos viciantes, formatos, estruturas, hooks, pesquisa com fonte, roteiro, grifos, análise de vídeo e de perfil), a equipe de revisores que confere cada texto e o conector que lê e salva no planejamento da pessoa no site;
- **o bEditor Estrategista:** edição na timeline do CapCut ou do DaVinci Resolve, aprendizado de estilo a partir de um vídeo já editado, biblioteca de estilos, plano editorial validado e motion;
- **o bEditor original:** guia de edição do diretor, decupagem com revisão, corte de silêncio e de erro, motion graphics em Remotion e no estilo editorial `motion-vox`, cama musical, legenda, master, QA medido, branding do canal, painel de revisão e preparo da publicação.

O mesmo método que escolhe o formato, a estrutura e o hook decide o corte, a imagem, a legenda e o som.

## O que vem no plugin

| Parte | O que é |
|---|---|
| Skill `sofia-estrategista` | Ideia, pesquisa, formato, estrutura, hook, roteiro, grifos, análise de vídeo e de perfil, com e sem o conector |
| Skill `sofia-editora` | Edição na timeline, aprendizado de estilo, biblioteca de estilos e motion |
| Skill `beditor` | Decupagem, guia de edição, montagem, motion graphics em Remotion, finalização, QA e publicação (o bEditor original) |
| Skill `motion-vox` | Motion graphics no estilo editorial de papel e legenda queimada sobre um clipe vertical já cortado |
| Atalhos da Sofia | `roteiro`, `ideias`, `pesquisa`, `analisar`, `critica`, `conectar`, `atualizar`, `editar`, `aprender-edicao` e `estilos` |
| Atalhos do interruptor | `ligar`, `desligar`, `modo` e `ensinar` (veja "Ligar, desligar e só quando chamada") |
| Atalhos do bEditor | `setup`, `dirigir`, `cortar`, `motion-graficos`, `finalizar`, `publicar`, `montar`, `plano`, `motion`, `aprender-motion`, `editar-analise`, `qa`, `branding` e `painel` |
| Equipe da Sofia (agentes no Claude Code e no Cowork) | quem escreve: `estrategista-de-ideias`, `especialista-em-bolha`, `pesquisador`, `redator-de-hook` e `roteirista`; quem confere: `revisor-o-que-nao-fazer`, `revisor-de-hook`, `revisor-de-voz`, `revisor-de-estrutura`, `revisor-de-fatos`, `especialista-em-bolha` e `critico`. Cada um busca no conector o briefing do seu papel |
| Ajudantes da edição (Claude Code e Cowork) | `analista-de-edicao` (lê as pranchas de quadros de uma referência), `diretor` (guia de edição de um take), `enriquecedor` (confere os fatos marcados no guia) e `analista-de-estilo` (lê as folhas de contato de um estilo de motion) |
| Conector | Sofia Estrategista, em `.mcp.json` |
| Painel (só no Claude Code) | `hooks/register.tsx`: um painel ao lado da conversa com os cards de cada etapa do planejamento, o @ do perfil e o uso das janelas de 5 horas e de 7 dias do Claude, com quanto falta para zerar. Abre sozinho no início da sessão e pelo comando `/sofia-painel`. É também o interruptor da Sofia neste computador (veja "Ligar, desligar e só quando chamada"). No site, no app de conversa e no Codex, fica parado |
| Ferramentas | `scripts/` e o pacote Python `beditor/` (medição, pranchas, transcrição, biblioteca, plano editorial, pontes do CapCut e do DaVinci), `schemas/`, `motion/`, os scripts das skills `beditor` e `motion-vox`, o `painel/` de revisão e as fontes livres (OFL) do motion |

## Versão 2.1.0: liga, desliga e só quando chamada

- **O interruptor.** A pessoa liga e desliga a Sofia com um pedido ("Sofia, desliga", "liga a Sofia", "Sofia, só quando eu chamar") e escolhe o modo: `ligada` (o padrão), `so-quando-chamada` (a Sofia só age depois que a pessoa a chama pelo nome) ou `desligada` (o Claude responde sem ela). Quem não mexe em nada continua com a Sofia ligada, como na 2.0.0.
- **O primeiro uso.** Na primeira vez em cada lugar, a Sofia se apresenta em 4 ou 5 linhas (o que faz, 3 exemplos de pedido, onde ver os cards no site, como desligar e ligar), faz o que foi pedido e pergunta se fica sempre ligada ou só quando chamada.
- **Os atalhos novos.** `/sofia-estrategista:ligar` liga (sempre ligada, ou só quando chamada com o argumento). `/sofia-estrategista:desligar` desliga. `/sofia-estrategista:modo` mostra o modo de agora e, com `ligada`, `so-quando-chamada` ou `desligada`, troca. `/sofia-estrategista:ensinar` mostra o tutorial de novo, sem mudar o modo.
- **Como volta ao padrão.** Diga "liga a Sofia" ou apague o `estado.json` (veja abaixo): sem ele, a Sofia está ligada.

## Ligar, desligar e só quando chamada

**No Claude Code**, o painel (`hooks/register.tsx`) é também o interruptor, e é ele que guarda o modo:

- **O que o gancho lê e grava:** um arquivo só, o `estado.json`, na pasta de dados do próprio plugin (`CLAUDE_PLUGIN_DATA`), neste computador. Ele guarda o modo (`ligada`, `so-quando-chamada` ou `desligada`), se a Sofia já se apresentou (`apresentada`) e quando o modo mudou (`mudouEm`). Só é gravado quando a pessoa muda o modo ou quando a Sofia se apresenta pela primeira vez. Sem o arquivo, ou com ele ilegível, a Sofia fica ligada.
- **O que ele faz com isso:** põe no contexto de cada pedido a linha `Interruptor local: <modo>.` e, quando o modo manda, nega a skill da Sofia e as ferramentas do conector Sofia Estrategista. Com a Sofia desligada, o painel também não lê o quadro de cards no conector.
- **As marcas da sessão:** além do `estado.json`, o gancho guarda algumas marcas por sessão no armazenamento local do Claude Code: se a Sofia foi chamada pelo nome, se ela ofereceu ligar, se o modelo pode trocar o modo e se ela perguntou o modo (e se a linha do primeiro uso já veio na sessão). Elas valem só a sessão em curso e ficam neste computador.
- **Nada vai ao servidor ao desligar.** O modo e as marcas não são enviados ao conector nem a nenhum outro serviço.
- **Desligada, chamar a Sofia faz uma oferta.** Se a pessoa fala com a Sofia desligada, ela responde só "Estou desligada aqui. Quer que eu ligue?" e liga só com o sim da pessoa ("sim", "pode", "Sofia, sim"). Um "não", ou qualquer outra resposta, não liga e não repete a oferta.
- **Cada computador tem o seu:** o modo vale para este computador, em todos os projetos. Em outro computador, ou no chat, é outro interruptor.

**No Cowork:** ainda não testado.

**No chat do claude.ai** (navegador, app e telefone) não há trava técnica: quem segue a regra é o Claude, pela nota na memória da conta (`Sofia Estrategista: desligada no chat. Para ligar, dizer "liga a Sofia".` ou `Sofia Estrategista: só quando chamada pelo nome.`), quando a memória aceitar a nota. A Sofia guarda e apaga a nota com a ferramenta de memória do próprio chat. Sem memória, o desligar vale só na conversa. Dentro de um Projeto, a memória pode ser separada. A regra completa, para quem escreve a Sofia, está em `skills/sofia-estrategista/references/interruptor.md`.

**Os comandos:**

| Comando | O que faz |
|---|---|
| `ligar` | Liga a Sofia neste lugar. Sem argumento, sempre ligada; com "só quando chamada", no modo só quando chamada |
| `desligar` | Desliga a Sofia neste lugar. Para ligar de novo: "liga a Sofia" |
| `modo` | Sem argumento, diz qual modo vale e mostra os três. Com `ligada`, `so-quando-chamada` ou `desligada`, troca o modo |
| `ensinar` | Mostra de novo o tutorial (o que a Sofia faz, exemplos, onde ficam os cards, como ligar e desligar), mesmo desligada, sem mudar o modo |

No painel do Claude Code, os mesmos comandos existem sem o prefixo: `/sofia-ligar`, `/sofia-desligar`, `/sofia-modo` e `/sofia-ensinar`.

## Versão 2.0.0: uma Sofia só

- **Um nome, um marketplace.** A Sofia Estrategista (`sofia-estrategista` 1.6.0) e a Sofia Estrategista com edição (`sofia-estrategista-editora` 0.6.0) viraram um plugin só, o `sofia-estrategista`, instalado pelo marketplace `criadores-do-futuro`. Nada das duas ficou de fora: o método, a equipe, a conferência, a trava de gravação dos agentes, o espelho do método, a análise de vídeo e de perfil e toda a edição de vídeo.
- **Os nomes mudaram junto.** Os atalhos são `/sofia-estrategista:<atalho>` e os agentes, `sofia-estrategista:<papel>`. O conector da conta não muda: o que está salvo no site continua lá.
- **Quem tem uma Sofia de antes** troca uma vez, pelo prompt de migração do [README do repositório](https://github.com/Criadores-do-Futuro/sofia-estrategista#já-tem-uma-sofia-instalada), que também está na página Conector do site do curso. Depois disso, as versões novas chegam por atualização.
- **A chave de volta:** se o conector desligar a equipe, o pacote de cada etapa chega sem a seção "Passos e equipe desta etapa", e a Sofia segue o pacote inteiro na conversa, como antes da equipe.

## A equipe da Sofia

Ideia, hook, roteiro, ajuste e crítica não são escritos e conferidos numa passada só:

- **Quem escreve** gera mais opções do que mostra, com o método inteiro da etapa e a voz da pessoa.
- **Os revisores** conferem juntos, cada um com uma fatia do método e as regras com código dela (as cartas): o que não fazer, o hook, a voz, a estrutura, os fatos e a bolha. Até 2 rodadas de correção.
- **O conector** manda o plano de cada etapa, o briefing de cada papel e confere por código o que é mecânico. Quando tudo passa, devolve o selo de conferência, que vai junto ao salvar. Texto salvo sem o selo fica marcado como sem conferência.
- **Em cada app:** no Claude Code e no Cowork, os papéis são agentes do plugin; no Codex, subagentes do próprio Codex; no Claude do site e do celular e no ChatGPT, passadas na conversa (`skills/sofia-estrategista/references/passadas.md`).
- **As referências do método** são cópia gerada do conector (`exportar-referencias.mts`, no webapp), com as cartas de cada papel em `cartas.md`, para quando o conector está desligado. O que antes só existia no plugin (os tipos de hook, as estruturas, a crítica, a voz, a análise de vídeo e o glossário) passou para o conector e chega aos agentes pelo briefing.
- **Os agentes não gravam no site:** as ferramentas do conector que gravam, mudam ou apagam ficam travadas neles (`disallowedTools`, gerado pelo mesmo script do espelho). Só a conversa grava, com o OK do aluno.

## O que a Sofia faz na edição

1. **Do card ao corte.** Lê o card do planejamento (formato, estrutura, hook, roteiro escolhido), entende o bruto (inventário, transcrição, erros, respiros, pranchas), monta um plano editorial por momento, valida, monta no editor escolhido e confere o projeto salvo contra o plano.
2. **Aprender a editar com um vídeo editado.** Mede cada quadro decodificado e cada trilha de áudio, gera pranchas com todos os quadros, transcreve com tempo por palavra e lê a edição bloco a bloco: cortes e ritmo, J-cut e L-cut, enquadramento, zoom e movimento, transições, legenda, lettering, imagens de apoio, cor, som, abertura e fim. Cada regra do guia tem evidência de tempo e diz se foi medida, inferida ou se não deu para saber. O guia vai para a biblioteca, com versões, e é aplicado nos próximos brutos.
3. **Estilos.** Lista, carrega e versiona os guias guardados. Estilo salvo nunca é usado como se a pessoa tivesse escolhido.
4. **Motion.** Cria, mostra a prévia, registra a revisão, renderiza e importa o clipe numa pista própria.
5. **Take a take, em etapas aprovadas.** `dirigir` (guia), `cortar` (decupagem), `motion-graficos`, `finalizar` (cama, legenda, grade e master) e `publicar` (título, descrição, capa e agendamento). Cada etapa entrega algo para a pessoa ver antes da seguinte. Detalhes em [docs/beditor-motion.md](docs/beditor-motion.md).

## Regras do produto

- A montagem, o texto, a legenda, o som, os efeitos e a revisão final vivem na timeline do editor escolhido. Os scripts medem, preparam e conferem; não trocam a timeline por um MP4 montado fora.
- Projeto editável salvo e vídeo exportado são entregas diferentes. Exportar, publicar e marcar o card como gravado ou postado só com pedido da pessoa.
- Geração de vídeo, imagem ou voz e coletor pago só com OK, depois de dizer o que vai gerar e quanto custa.
- Medição de quadro não reconhece efeito, fonte, máscara nem intenção. O que vem da leitura das pranchas fica como hipótese quando não há prova.
- Preferência da pessoa só é guardada com o OK dela.

## Instalar

**Claude Code**

```sh
claude plugin marketplace add Criadores-do-Futuro/sofia-estrategista
claude plugin install sofia-estrategista@criadores-do-futuro
```

Depois, `/reload-plugins` (ou uma sessão nova) e `/mcp` para entrar no conector Sofia Estrategista com o e-mail do curso. Para as versões novas chegarem sozinhas, ligue a atualização automática do marketplace `criadores-do-futuro` em `/plugin`, na aba dos marketplaces. Para testar um checkout: `claude --plugin-dir "CAMINHO_DO_REPOSITORIO/plugin"`.

**Já tem uma Sofia instalada?** Se for a `sofia-estrategista-editora`, ou a `sofia-estrategista` de outro marketplace (como o `sofia-plugins`), use o prompt de migração do [README do repositório](https://github.com/Criadores-do-Futuro/sofia-estrategista#já-tem-uma-sofia-instalada): ele desinstala a antiga e instala esta, com o seu OK.

**Claude no navegador ou no app**

O `.zip` da página Kit do site traz o plugin dentro da pasta `sofia-estrategista/` (o `scripts/empacotar.sh` do repositório gera esse arquivo). Envie o `.zip` em Personalizar › Plugins › Adicionar › Enviar plugin e conecte o conector na aba Conectores do plugin. O método e o conector funcionam ali. A edição precisa de um computador com Python, FFmpeg e o editor aberto, então depende do que o host oferece.

**Codex**

```sh
codex plugin marketplace add Criadores-do-Futuro/sofia-estrategista
codex plugin add sofia-estrategista@criadores-do-futuro
```

O catálogo do Codex é o `.agents/plugins/marketplace.json` da raiz do repositório. Com o `.zip` do kit, descompacte e aponte para a pasta:

```sh
unzip sofia-estrategista.zip
codex plugin marketplace add ./sofia-estrategista
codex plugin add sofia-estrategista@sofia-estrategista-local
```

No Codex, a Sofia aparece como "só no computador" (`requires_local_executor`): a edição e a leitura dos quadros de um vídeo rodam programas na máquina da pessoa.

Os detalhes por ferramenta estão em [docs/instalacao-e-compatibilidade.md](docs/instalacao-e-compatibilidade.md).

## O que precisa no computador para editar

- Python 3.10 ou mais novo, FFmpeg e ffprobe.
- `yt-dlp` para baixar referência por link; Whisper com um modelo `.pt` já baixado para transcrição local.
- `pip install -r requirements-editorial.txt` para validar o plano editorial; `requirements-capcut-desktop.txt` para a ponte do CapCut Desktop.
- Node, Chrome e `npm ci --prefix motion` para motion.
- Para as skills `beditor` e `motion-vox`: `pip install -r requirements-motion.txt`, e o `/sofia-estrategista:setup` confere o resto e diz o comando de cada item que falta.
- O editor: o plugin oficial do CapCut no host (CapCut Web), a ponte local (CapCut Desktop) ou o MCP do DaVinci Resolve com o Resolve aberto.

A biblioteca de estilos fica na pasta de `BIBLIOTECA_ESTILOS_RAIZ`. Aponte para um disco com espaço: pranchas e análises de vídeo longo crescem rápido.

## Documentação

- [De onde veio cada parte](docs/origens.md)
- [Instalação e compatibilidade](docs/instalacao-e-compatibilidade.md)
- [Contrato editorial e validação](docs/contrato-editorial.md)
- [Análise de estilo](docs/analise-de-estilo.md) e [enriquecer o manual](docs/enriquecer-manual-estilo.md)
- [Baixar referência](docs/download-referencia.md) e [transcrição local](docs/transcricao-local.md)
- [CapCut Web](docs/ponte-capcut-web.md), [CapCut Desktop](docs/ponte-capcut-desktop.md) e [DaVinci Resolve](docs/ponte-davinci.md)
- [Arquitetura](docs/arquitetura.md), [plano e critérios](docs/plano.md), [referências técnicas](docs/referencias-tecnicas.md)
- [Proteção de arquivos e distribuição](docs/seguranca-distribuicao.md)
- [bEditor: motion, decupagem, finalização e publicação](docs/beditor-motion.md) e o [manual interativo](docs/manual.html) que o setup preenche

Os testes, o empacotamento e o envio aos diretórios ficam na raiz do repositório, fora do plugin.

## O que o plugin roda, envia e baixa

**Roda no computador**, só quando a pessoa pede a etapa: Python 3, FFmpeg e ffprobe, Whisper local (mlx-whisper ou faster-whisper), OpenCV, Node com Remotion e Chrome para o render de motion, `xcrun swiftc` no macOS para compilar o recorte de pessoa (Vision), e um servidor de prévia só em `127.0.0.1`.

**Instala só com o sim da pessoa:** `setup.py --instalar` e `--atualizar` mostram os comandos (`brew`, `pip`, `git pull --ff-only` num clone, `claude plugin install`, `claude plugin marketplace update criadores-do-futuro` e `claude plugin update`) e só executam com `--sim`. O comando `/atualizar` mostra o caminho de atualizar em cada app e, no Claude Code, só roda os comandos depois do OK da pessoa.

**Envia**, sempre com a conta e a escolha da pessoa:

- ao conector Sofia Estrategista (`https://plataforma.criadorestrategista.com.br/api/mcp`), depois do login: o que ela pede para ler ou salvar no planejamento, no cérebro e nas referências;
- à API Gemini do Google, só com a chave `GEMINI_API_KEY` da própria pessoa: os prompts das imagens geradas;
- ao Zernio ou ao Metricool, só com o sim a cada publicação: vídeo, capa, título e descrição do post;
- ao CapCut e ao DaVinci Resolve, pelas ferramentas dos próprios fornecedores: a montagem na timeline.

**Baixa:** vídeo público pelo link que a pessoa der (`yt-dlp`, sem cookies nem login); modelos de visão na primeira vez (OpenCV Zoo no GitHub e MediaPipe no Google Cloud Storage); fontes do Google Fonts e a GSAP do jsDelivr nas prévias em HTML; pacotes npm do `motion/` com `npm ci`; os pacotes do projeto de motion da skill `beditor` com `npm install` (`scripts/projeto.sh`, versões fixas no `package.json` do modelo); e o CLI de render `hyperframes@0.9.58` da HeyGen pelo `npx`, só nas etapas de motion e legenda que o usam (a variável `BEDITOR_HYPERFRAMES` troca a versão).

**Lê no computador**, só quando a pessoa roda: `custos.py` e `painel/telemetria.py` leem os registros de sessão do Claude Code (`~/.claude/projects`) para somar tokens e tempo por etapa. O resultado fica num arquivo local.

**Lê e grava no computador, pelo painel do Claude Code:** o `estado.json` do interruptor, na pasta de dados do próprio plugin (`CLAUDE_PLUGIN_DATA`): o modo da Sofia, se ela já se apresentou e quando o modo mudou. O gancho lê esse arquivo a cada pedido e só o grava quando a pessoa muda o modo ou na primeira apresentação. Ele não vai a lugar nenhum: ligar ou desligar a Sofia não manda nada ao servidor.

Nada é enviado para a Criadores do Futuro além do que passa pelo conector. Não há telemetria.

## Privacidade, termos e suporte

O conector só funciona para alunos do curso, depois do login. Vídeos, transcrições, pranchas e guias de estilo ficam no computador de quem usa; o plugin nunca copia nem altera o vídeo original.

| | Português | Español | English |
|---|---|---|---|
| Privacidade | [privacidade](https://plataforma.academiacriadoresdofuturo.com.br/sofia-editora/privacidade) | [privacidad](https://plataforma.academiacriadoresdofuturo.com.br/sofia-editora/privacidad) | [privacy](https://plataforma.academiacriadoresdofuturo.com.br/sofia-editora/privacy) |
| Termos de uso | [termos](https://plataforma.academiacriadoresdofuturo.com.br/sofia-editora/termos) | [términos](https://plataforma.academiacriadoresdofuturo.com.br/sofia-editora/terminos) | [terms](https://plataforma.academiacriadoresdofuturo.com.br/sofia-editora/terms) |
| Suporte | [suporte](https://plataforma.academiacriadoresdofuturo.com.br/sofia-editora/suporte) | [soporte](https://plataforma.academiacriadoresdofuturo.com.br/sofia-editora/soporte) | [support](https://plataforma.academiacriadoresdofuturo.com.br/sofia-editora/support) |

## Licença

Pode baixar, instalar e usar para criar o seu conteúdo ou o de clientes. Redistribuir, revender ou publicar cópias não é permitido. Veja [LICENSE](LICENSE).
