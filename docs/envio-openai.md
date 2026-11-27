# Enviar a Sofia ao diretório de plugins da OpenAI (ChatGPT e Codex)

O pacote está pronto e conferido, mas nada foi enviado. Este é o passo a passo do portal, na ordem que a skill oficial da OpenAI (`plugin-creator` 0.1.28, `prepare-plugin-submission`) pede. Conferido em 27/11/2026 contra a documentação oficial (fontes no fim).

## O pacote

```sh
scripts/empacotar.sh                                   # o pacote do Claude e do kit (limpa a pasta dist/)
scripts/empacotar-openai.sh --webapp CAMINHO_DO_WEBAPP --links
```

O segundo gera `dist/sofia-estrategista-openai.zip`: uma pasta `sofia-estrategista/` com o `plugin.json` no formato Agent Plugins, o `mcp.json`, as quatro skills, o ícone e as pastas que as skills usam. Os manifestos do Claude e do Codex (`.claude-plugin`, `.codex-plugin`, `.mcp.json`) não entram, nem `hooks/`, `.app.json` ou catálogo. O `--webapp` confere os casos de revisão e as anotações das ferramentas no código do site (use a `main`); o `--links` abre os quatro links da ficha. Com erro, o script não deixa o ZIP em `dist/`.

O que o envio lê está em `openai/plugin.json` (ficha, casos de revisão, notas da versão e tradução, em `extensions.com.openai`) e `openai/mcp.json` (o conector). Para mudar a ficha ou os casos, edite esses dois arquivos e rode o script de novo.

### Decisões tomadas

- **Formato.** `plugin.json` na raiz com `$schema` do Agent Plugins 1.0.0 e tudo da OpenAI em `extensions.com.openai`, como a documentação pede para pacote novo. Quando esse objeto existe, o portal ignora o `.codex-plugin`.
- **Idioma da ficha.** A documentação diz que os campos da ficha são o inglês e que outros idiomas vão em `publication.translations`. A ficha está em inglês e diz que a Sofia funciona em português; o português (o mesmo texto do Codex) está em `translations.pt-BR`. Hoje o diretório ainda mostra só os campos em inglês. As três sugestões de pedido ficaram em português, iguais às do Codex.
- **OAuth: `cimd`.** O servidor anuncia os dois registros: `registration_endpoint` (DCR) e `client_id_metadata_document_supported: true` (CIMD), com cliente público, PKCE S256 e escopo `curso`. Com `cimd`, o pacote não leva `client_id` nem segredo, não fica registro guardado no portal, e o cliente da OpenAI ainda pode cair para o DCR. Se a conexão no portal falhar, troque para `{"mode": "dcr"}` em `openai/mcp.json` e suba o ZIP de novo. Atenção ao filtro do site contra imitação (`imitaAppConhecido`): um app chamado ChatGPT ou OpenAI só passa se o documento de metadados ou o endereço de retorno estiverem em `chatgpt.com` ou `openai.com`.
- **Só no computador.** `requires_local_executor: true`, como no Codex: a edição roda FFmpeg, Python e o editor na máquina. O diretório marca o plugin como "Desktop only" (instala só pelo app de desktop). A página de plugins só para desktop descreve esse campo para plugins sem MCP; se o portal disser que o campo não é permitido, a saída é pedir liberação à OpenAI (com o ID da organização) ou enviar um pacote só com a skill `sofia-estrategista` e o conector, que funcionam no ChatGPT do site e do celular.
- **Site da ficha.** `websiteURL` é o repositório público no GitHub, porque `/kit` manda para o login. Suporte, privacidade e termos são as páginas em inglês que o Codex já usava.
- **Sem e-mail no pacote.** O `author` leva só nome e o link de suporte.
- **Casos de revisão.** Saíram do `.codex-plugin` e moram só em `openai/plugin.json`. São 5 positivos (quadro, roteiro para gravar, criar card, cérebro do perfil, método) e 3 negativos (vídeo inteiro gerado por IA, reembolso, dados de outro aluno), com os nomes reais das ferramentas e dos argumentos. Também há `review.prompts`, campo da skill oficial 0.1.28 que a página de envio ainda não lista: se o portal recusar, apague esse campo.

## Passo a passo

### 1. Antes do portal

1. **Conta de teste.** O site entra sem senha (link no e-mail, Google, Microsoft ou chave de acesso). A diretriz pede uma conta que o revisor use sem pedir código ou link a ninguém; a skill oficial diz que, com login por link ou código no e-mail, a conta de teste usa o e-mail da equipe de revisão, `mcp-review@theaicompany.org`. No webapp: ponha esse e-mail em `ACESSO_EMAILS_LIBERADOS` na Vercel e prepare os dados dessa conta (pelo admin ou por um script, porque o link de entrada vai para a caixa da OpenAI). Os casos pedem: um perfil avaliado só (o dela), com pelo menos um card em cada coluna, um card em Gravar com roteiro salvo e uma nota sobre hooks no cérebro do perfil.
2. **Vídeo de demonstração.** Grave, no app de desktop do ChatGPT, os 5 casos positivos e um negativo com a conta de teste, mais a edição no CapCut ou no DaVinci. Hospede com acesso por link (YouTube não listado, por exemplo), confira que abre sem login e ponha o endereço em `extensions.com.openai.review.demo_recording_url`, no `openai/plugin.json`.
3. **Países.** Escolha onde o plugin aparece e ponha em `extensions.com.openai.publication.countries` (por exemplo `["BR"]`, ou `[]` para todos). Sem o campo, a escolha fica no portal.
4. **Links.** A política em inglês (`/sofia-editora/privacy`) ainda cita o conector antigo (`criador-estrategista.vercel.app`) e fala só de Claude e Codex; a página de suporte cita o nome antigo `sofia-estrategista-editora@sofia-editora`. Atualize as duas no site da academia antes do envio: a revisão confere se a política cobre o que o plugin faz.
5. Rode `scripts/empacotar-openai.sh --webapp CAMINHO_DO_WEBAPP --links` de novo. Sem pendentes, o ZIP está pronto.

### 2. Organização verificada

Em [platform.openai.com/settings/organization/general](https://platform.openai.com/settings/organization/general), verifique a pessoa ou a empresa (Action Criação Digital Ltda) em nome de quem a Sofia vai aparecer. Quem envia precisa ser dono da organização ou ter o papel **Apps Management Write**. O diretório mostra o nome da identidade verificada, seja qual for o `developerName` do pacote (hoje "Criadores do Futuro").

### 3. Rascunho com o ZIP

1. Em [platform.openai.com/plugins](https://platform.openai.com/plugins), **Upload new or existing plugin**.
2. Escolha a **Developer identity** verificada e envie `dist/sofia-estrategista-openai.zip` em **Upload plugin**.
3. Em **Metadata & Skills**, espere as conferências e leia **Issues** (o botão **Copy issues** copia tudo). A varredura de segurança das skills leva até 2 horas.
4. Confira o que foi importado: nome, ficha, ícone, quatro skills, casos de revisão, notas e tradução.

### 4. Conectar o MCP

1. Em **MCPs**, escolha `sofia-estrategista` e clique em **Connect**. Confira o endereço `https://plataforma.criadorestrategista.com.br/api/mcp` e a autenticação OAuth.
2. **Domínio.** O portal mostra um token. Ponha-o na variável `OPENAI_APPS_CHALLENGE` do projeto do site na Vercel (ambiente Production) e faça um **Redeploy** da produção: a rota é gerada no build, então salvar a variável sozinho não muda o que ela responde. Sem a variável, ela responde `404 Not found`. Depois do deploy, confira que `https://plataforma.criadorestrategista.com.br/.well-known/openai-apps-challenge` devolve só o token, em texto puro (nada de JSON), e clique em **Verify Domain**.
3. Conecte e entre com a conta de teste na página `/conectar`, com **Permitir**.
4. Espere a varredura das ferramentas e leia **Issues**. As 58 ferramentas têm `readOnlyHint`, `openWorldHint` e `destructiveHint` explícitos, e `--webapp` confere isso no código do site. Desde 27/11/2026, as que apagam ou sobrescrevem dados levam `destructiveHint: true`, como a diretriz pede. São 14:
   - 7 que já tinham a marca: `sofia_apagar`, `referencia_apagar` e `planejamento_juntar_duplicado`, que apagam, e `cerebro_guardar`, `cerebro_preferencia`, `cerebro_esquecer` e `cerebro_desfazer`, que trocam ou tiram notas;
   - 7 que passaram a ter a marca, porque sobrescrevem: `planejamento_editar_card`, `planejamento_estruturar_card`, `referencia_editar`, `perfil_salvar_avaliacao`, `perfil_definir_alvo`, `perfil_salvar_leitura` e `sofia_perfil`.

   `perfil_desfazer_alvo`, `planejamento_salvar_pesquisa` e `sofia_salvar` ficam com `false`, porque alternam, acrescentam ou criam uma versão nova sem perder nada. Se a varredura reter alguma, ajuste no site e use **Rescan**.

### 5. Informações de revisão e envio

1. Em **Metadata & Skills › Review information › Review details**: o endereço de entrada (`https://plataforma.criadorestrategista.com.br/entrar`), o método (link no e-mail) e o e-mail de teste, só nesses campos protegidos, nunca no ZIP. Escolha o método "magic link/email code" onde o formulário oferecer.
2. Rode os 8 casos na versão salva e anote passou ou falhou.
3. **Submit for review** e as declarações (entre elas, não ter como público crianças com menos de 13 anos). Só uma revisão por vez. A resposta chega por e-mail; para recorrer, responda ao e-mail.
4. Aprovado, **Publish plugin** na versão aprovada.

## Versões novas

- **Ferramentas do conector.** Depois de publicado, a OpenAI varre o servidor todo dia e libera sozinha o que passar nas conferências. Para não esperar: deploy, **MCPs › Issues › Rescan**. Ferramenta nova fica indisponível até aprovada; mantenha o servidor compatível com os campos já aprovados. Trocar o endereço do conector só pelo suporte.
- **Skills, ficha ou ícone.** Pedem ZIP novo: suba a versão nos três manifestos e no catálogo, escreva `publication.release_notes`, rode `scripts/empacotar-openai.sh`, envie em **Upload plugin to make changes**, revise e publique. O portal avisa se a versão não mudou. Cada envio troca o pacote inteiro e zera as declarações; os casos vindos do ZIP só mudam por ZIP.

## O que só o portal confere

Varredura de segurança das skills e das ferramentas, anotações e retenções, domínio, conexão OAuth, identidade verificada, declarações, a leitura humana dos links e da ficha, e a importação da tradução e dos países.

## Pontos de atenção

- A skill `beditor` depende do plugin oficial do CapCut (outro MCP) e sobe a mídia para o CapCut; a ficha diz isso. A revisão pode perguntar.
- O `SKILL.md` da `motion-vox` fala de uma pasta `assets/` com 16 objetos que não existe no repositório (o pacote do Claude também sai sem ela).
- No formato portátil, os 28 atalhos de `commands/` não viram skill: no Codex, pelo ZIP, aparecem só as quatro skills. Pelo marketplace `criadores-do-futuro` nada muda.
- O `mcp.schema.json` do Agent Plugins 1.0.0 não lista `extensions` no servidor. A OpenAI lê a autenticação dali; outro cliente Agent Plugins pode ignorar essa entrada.

## Fontes

- [OpenAI: enviar plugins](https://developers.openai.com/plugins/deploy/submission)
- [OpenAI: erros do envio](https://developers.openai.com/plugins/deploy/submission-errors)
- [OpenAI: empacotar plugins](https://developers.openai.com/plugins/build/plugins)
- [OpenAI: plugins só para desktop](https://developers.openai.com/plugins/deploy/desktop-only)
- [OpenAI: diretrizes de plugins](https://developers.openai.com/plugins/plugin-guidelines)
- `plugin-creator` 0.1.28 da OpenAI: `prepare-plugin-submission` (`listing.md`, `review-materials.md`, `submission-lifecycle.md`) e `create-plugin` (`zip-requirements.md`, `plugin-packages.md`)
