import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, ToolCallResult } from 'claude-code'

import type { Etapa, Janela, ModoDoInterruptor, Quadro } from '../types'
import {
  AVISO_DESLIGADA,
  AVISO_SO_QUANDO_CHAMADA,
  chamaSofia,
  decidir,
  ehDaSofia,
  ehLivre,
  lerEstado,
  pedidoDeModo,
  respostaDoModo,
  simCurto,
} from './interruptor'
import type { Estado, Modo } from './interruptor'

// Plugin sofia-painel: o painel da Sofia Estrategista no Claude Code. Mostra quantos cards há em cada etapa
// do planejamento, pela última leitura que a Sofia fez com planejamento_quadro, e quanto já foi usado das
// janelas de 5 horas e de 7 dias do Claude, com quanto falta para cada uma zerar.
// Também é o interruptor da Sofia neste computador: lê e grava estado.json na pasta de dados deste plugin,
// nega as ferramentas da Sofia quando o modo manda (a regra está em interruptor.ts) e avisa o modelo do modo.
// As skills, os comandos e o conector são do plugin sofia-estrategista (dependência deste): por isso os
// nomes conferidos aqui levam o prefixo `sofia-estrategista:`. Este mod não liga o conector nem o chama:
// ele só observa o resultado das chamadas que a Sofia já faz (hook tool.call) e devolve o resultado igual.
// Mods só rodam no Claude Code (terminal, aba Code do app, extensões de IDE).

const PAINEL = 'sofia-painel'
const TITULO = 'Sofia Estrategista'
// Troque a marca quando o formato guardado mudar: um reload mantém o que a versão anterior guardou.
const quadro = atom({ plugin: 'sofia-painel', key: 'quadro' } as const, null, { shape: 'quadro-2' })
const janelas = atom({ plugin: 'sofia-painel', key: 'janelas' } as const, [], { shape: 'janelas-1' })
const modoNoPainel = atom({ plugin: 'sofia-painel', key: 'modo' } as const, 'ligada' as ModoDoInterruptor, {
  shape: 'modo-1',
})

// ---------- interruptor ----------

const ESTADO = 'estado.json'
const PREFIXO_DO_PLUGIN = 'sofia-estrategista:'
const ESTOU_DESLIGADA = 'Estou desligada aqui. Quer que eu ligue?'
const LINHA_DESLIGADA_CHAMADA = `Se a pessoa falou com a Sofia (e não de um arquivo ou de outra pessoa chamada Sofia), responda só: "${ESTOU_DESLIGADA}"; senão, atenda o pedido sem a Sofia.`
const LINHA_DISSE_SIM = 'A pessoa disse sim: a Sofia está ligada. Confirme em uma linha e faça o pedido de antes.'
const LINHA_ENSINAR =
  'A pessoa quer aprender a usar a Sofia. Mostre o tutorial de skills/sofia-estrategista/references/primeiro-uso.md, mesmo com a Sofia desligada.'
const LINHA_PRIMEIRO_USO =
  'Primeiro uso da Sofia neste lugar: só se você agir como Sofia nesta resposta, abra com o tutorial de primeiro-uso.md; senão, ignore esta linha.'
/** A negação da skill de ligar, desligar ou modo quando a troca não foi gravada: a Sofia não confirma o que não houve. */
const naoTroquei = (comando: string) =>
  `Não troquei o modo da Sofia. Peça à pessoa para dizer 'liga a Sofia' ou 'Sofia, desliga', ou digitar /sofia-estrategista:${comando}.`
// O comando do mod /sofia-ensinar, se ele chegar também como prompt digitado.
const ENSINAR_DO_MOD = /^\s*\/sofia-ensinar\b/i
const COMO_TROCAR = 'Para trocar: /sofia-modo ligada, /sofia-modo so-quando-chamada ou /sofia-modo desligada.'
const linhaDoModo = (modo: Modo) => `Interruptor local: ${modo}.`

/** Minúsculas, sem acento, espaços e sublinhados viram hífen: "Só quando chamada" vira "so-quando-chamada". */
function modoDoTexto(texto: string): Modo | null {
  const t = texto.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().trim().replace(/[\s_]+/g, '-')
  return t === 'ligada' || t === 'so-quando-chamada' || t === 'desligada' ? t : null
}

/** Os argumentos pedem o modo de só quando chamada: "so-quando-chamada", "só quando chamada", "só quando eu chamar". */
function pedeSoQuandoChamada(args: string): boolean {
  if (modoDoTexto(args) === 'so-quando-chamada') return true
  const t = args.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/[\s_-]+/g, ' ').trim()
  return /\bso quando\b/.test(t)
}

/** O comando do plugin que a pessoa digitou (`/sofia-estrategista:nome args`), sem o prefixo, ou null. */
function comandoDigitado(texto: string, comando?: { name: string; args: string }): { nome: string; args: string } | null {
  if (comando && comando.name.toLowerCase().startsWith(PREFIXO_DO_PLUGIN)) {
    return { nome: comando.name.slice(PREFIXO_DO_PLUGIN.length).toLowerCase(), args: comando.args }
  }
  const m = /^\s*\/sofia-estrategista:([\w-]+)\s*([\s\S]*)$/i.exec(texto)
  return m ? { nome: (m[1] ?? '').toLowerCase(), args: (m[2] ?? '').trim() } : null
}

/** O que um comando de ligar, desligar, modo ou ensinar pede; null para qualquer outro comando. */
function pedidoDoComando(nome: string, args: string): Modo | 'ensinar' | null {
  // "ligar só quando chamada" liga no modo de só quando chamada; sem isso, ligada.
  if (nome === 'ligar') return pedeSoQuandoChamada(args) ? 'so-quando-chamada' : 'ligada'
  if (nome === 'desligar') return 'desligada'
  if (nome === 'ensinar') return 'ensinar'
  if (nome === 'modo') return modoDoTexto(args)
  return null
}

/** A pasta de dados do próprio plugin. Nunca $.env: ele lê o ambiente do processo, que traz a de outro plugin. */
async function pastaDeDados($: EngineInterface): Promise<string | null> {
  try {
    const pasta = (await $.process.hookEnv()).CLAUDE_PLUGIN_DATA
    return typeof pasta === 'string' && pasta ? pasta : null
  } catch {
    return null
  }
}

/** Põe o modo no painel quando ele mudou. Falhar aqui não muda nada do interruptor. */
async function mostrarModo($: EngineInterface, modo: Modo) {
  try {
    if ((await read($, modoNoPainel)) !== modo) {
      await update($, modoNoPainel, () => modo)
      await atualizarStatus($)
    }
  } catch {
    // o painel fica com o modo antigo até a próxima leitura
  }
}

/** O estado de estado.json. Sem pasta, sem arquivo ou com o arquivo torto: ligada. Nunca lança. */
async function lerInterruptor($: EngineInterface): Promise<Estado> {
  const pasta = await pastaDeDados($)
  let texto: string | null = null
  if (pasta) {
    try {
      texto = await $.fs.read(`${pasta}/${ESTADO}`)
    } catch {
      texto = null
    }
  }
  const estado = lerEstado(texto)
  await mostrarModo($, estado.modo)
  return estado
}

/** Grava o modo e devolve o estado que vale agora: o antigo quando não deu para gravar. */
async function gravarModo($: EngineInterface, modo: Modo): Promise<Estado> {
  const antes = await lerInterruptor($)
  const pasta = await pastaDeDados($)
  if (!pasta) return antes
  try {
    const depois: Estado = { modo, apresentada: antes.apresentada, mudouEm: new Date(await $.clock.now()).toISOString() }
    await $.fs.write(`${pasta}/${ESTADO}`, JSON.stringify(depois, null, 2) + '\n')
    await mostrarModo($, modo)
    return depois
  } catch {
    return antes
  }
}

async function idDaSessao($: EngineInterface): Promise<string | null> {
  try {
    return (await $.session.id()) || null
  } catch {
    return null
  }
}

/** A pessoa chamou a Sofia pelo nome nesta sessão. O chamado vale a sessão inteira. */
async function foiChamada($: EngineInterface, sessao: string | null): Promise<boolean> {
  if (!sessao) return false
  try {
    return (await $.state.get({ plugin: 'sofia-painel', key: 'chamada', id: sessao })).value === true
  } catch {
    return false
  }
}

async function marcarChamada($: EngineInterface, sessao: string | null) {
  if (!sessao) return
  try {
    await $.state.set({ plugin: 'sofia-painel', key: 'chamada', id: sessao }, true)
  } catch {
    // sem o registro, o modo "só quando chamada" segue negando: a pessoa chama de novo
  }
}

// Quatro marcas por sessão:
// - ofereceuLigar: o mod pôs a frase "Estou desligada aqui. Quer que eu ligue?" no último prompt;
// - podeTrocarModo: o último prompt de verdade chamou a Sofia, ou veio logo depois dessa frase;
// - perguntouModo: o mod pôs a linha do primeiro uso no último prompt, e a Sofia terminou com a pergunta do
//   modo; a resposta curta, sem o nome ("só quando eu chamar", "sempre ligada"), vale só no prompt seguinte;
// - avisouPrimeiroUso: a linha do primeiro uso já veio nesta sessão; sem chamar a Sofia, ela não volta.
type Marca = 'ofereceuLigar' | 'podeTrocarModo' | 'perguntouModo' | 'avisouPrimeiroUso'

async function lerMarca($: EngineInterface, marca: Marca, sessao: string | null): Promise<boolean> {
  if (!sessao) return false
  try {
    const lido =
      marca === 'ofereceuLigar'
        ? await $.state.get({ plugin: 'sofia-painel', key: 'ofereceuLigar', id: sessao })
        : marca === 'podeTrocarModo'
          ? await $.state.get({ plugin: 'sofia-painel', key: 'podeTrocarModo', id: sessao })
          : marca === 'perguntouModo'
            ? await $.state.get({ plugin: 'sofia-painel', key: 'perguntouModo', id: sessao })
            : await $.state.get({ plugin: 'sofia-painel', key: 'avisouPrimeiroUso', id: sessao })
    return lido.value === true
  } catch {
    return false
  }
}

async function gravarMarca($: EngineInterface, marca: Marca, sessao: string | null, valor: boolean) {
  if (!sessao) return
  try {
    if (marca === 'ofereceuLigar') await $.state.set({ plugin: 'sofia-painel', key: 'ofereceuLigar', id: sessao }, valor)
    else if (marca === 'podeTrocarModo') await $.state.set({ plugin: 'sofia-painel', key: 'podeTrocarModo', id: sessao }, valor)
    else if (marca === 'perguntouModo') await $.state.set({ plugin: 'sofia-painel', key: 'perguntouModo', id: sessao }, valor)
    else await $.state.set({ plugin: 'sofia-painel', key: 'avisouPrimeiroUso', id: sessao }, valor)
  } catch {
    // sem a marca, o modelo não troca o modo sozinho: a pessoa usa a frase ou o comando
  }
}

/** Grava apresentada: true, sem mudar o modo. Devolve false quando não deu para gravar. */
async function marcarApresentada($: EngineInterface, estado: Estado): Promise<boolean> {
  const pasta = await pastaDeDados($)
  if (!pasta) return false
  try {
    const depois: Estado = { ...estado, apresentada: true }
    await $.fs.write(`${pasta}/${ESTADO}`, JSON.stringify(depois, null, 2) + '\n')
    return true
  } catch {
    return false
  }
}

/** A Sofia fez (ou vai fazer) a pergunta do modo: marca apresentada e abre a janela do prompt seguinte. */
async function abrirPerguntaDoModo($: EngineInterface, estado: Estado, sessao: string | null) {
  if (!estado.apresentada) await marcarApresentada($, estado)
  await gravarMarca($, 'perguntouModo', sessao, true)
}

/** A primeira skill ou ferramenta da Sofia que passou neste computador: é o primeiro uso de fato. */
async function primeiroUsoNaFerramenta($: EngineInterface, ferramenta: string, entrada: Record<string, unknown>) {
  if (!ehDaSofia(ferramenta, entrada) || ehLivre(ferramenta, entrada)) return
  const estado = await lerInterruptor($)
  if (estado.apresentada || estado.modo === 'desligada') return
  await abrirPerguntaDoModo($, estado, await idDaSessao($))
}

/** As linhas que o modelo lê junto do que a pessoa digitou. Muda o modo quando a frase pede. */
async function linhasDoPrompt($: EngineInterface, texto: string, comando?: { name: string; args: string }): Promise<string[]> {
  const sessao = await idDaSessao($)
  const digitado = comandoDigitado(texto, comando)
  const ensinarDoMod = comando?.name.toLowerCase() === 'sofia-ensinar' || ENSINAR_DO_MOD.test(texto)
  let pedido = digitado ? pedidoDoComando(digitado.nome, digitado.args) : ensinarDoMod ? 'ensinar' : pedidoDeModo(texto)
  // A resposta à pergunta do modo vale só no prompt logo depois dela; aqui a janela fecha.
  const perguntouAntes = await lerMarca($, 'perguntouModo', sessao)
  await gravarMarca($, 'perguntouModo', sessao, false)
  if (!pedido && !digitado && perguntouAntes) pedido = respostaDoModo(texto)
  let estado = await lerInterruptor($)
  // A oferta de ligar vale só para a resposta seguinte: aqui ela é consumida. Um "sim" curto a ela liga
  // pelo próprio gancho (a Sofia só liga com o sim da pessoa, nunca no mesmo prompt em que foi chamada).
  const ofereceuAntes = await lerMarca($, 'ofereceuLigar', sessao)
  let disseSim = false
  if (!pedido && !digitado && ofereceuAntes && estado.modo === 'desligada' && simCurto(texto)) {
    pedido = 'ligada'
    disseSim = true
  }
  if (pedido && pedido !== 'ensinar') estado = await gravarModo($, pedido)
  const chamou = digitado !== null || chamaSofia(texto)
  if (chamou) await marcarChamada($, sessao)
  // Desligada, chamar a Sofia só faz a oferta. Na janela da pergunta do modo, a skill de modo também troca
  // (resposta com outras palavras).
  const soOferta = estado.modo === 'desligada' && !pedido && chamou && !ofereceuAntes
  await gravarMarca($, 'podeTrocarModo', sessao, soOferta ? false : chamou || ofereceuAntes || perguntouAntes)
  const ativa =
    estado.modo === 'ligada' || (estado.modo === 'so-quando-chamada' && (await foiChamada($, sessao)))

  const linhas = [linhaDoModo(estado.modo)]
  // O gancho gravou o sim: a linha só sai se o modo de fato virou ligada.
  if (disseSim && estado.modo === 'ligada') linhas.push(LINHA_DISSE_SIM)
  let ofereceAgora = false
  if (pedido === 'ensinar') {
    linhas.push(LINHA_ENSINAR)
    // Com a Sofia ativa, o tutorial termina com a pergunta do modo: a janela abre para a resposta.
    if (ativa) await abrirPerguntaDoModo($, estado, sessao)
  }
  // Um pedido de modo ou de "me ensina" nunca se nega.
  if (!pedido) {
    if (estado.modo === 'desligada') {
      linhas.push(AVISO_DESLIGADA)
      // Logo depois da oferta, a resposta que não é sim não liga e não repete a oferta.
      if (chamou && !ofereceuAntes) {
        linhas.push(LINHA_DESLIGADA_CHAMADA)
        ofereceAgora = true
      }
    } else if (estado.modo === 'so-quando-chamada' && !(await foiChamada($, sessao))) {
      linhas.push(AVISO_SO_QUANDO_CHAMADA)
    } else if (!estado.apresentada && (await pastaDeDados($))) {
      // Primeiro uso: a linha vem no primeiro prompt de cada sessão e quando a Sofia é chamada, até a
      // primeira skill ou ferramenta da Sofia passar (primeiroUsoNaFerramenta), que grava apresentada e abre
      // a janela da pergunta do modo. Sem pasta de dados não há onde guardar o apresentada: nunca vem.
      if (chamou || !(await lerMarca($, 'avisouPrimeiroUso', sessao))) {
        linhas.push(LINHA_PRIMEIRO_USO)
        await gravarMarca($, 'avisouPrimeiroUso', sessao, true)
      }
    }
  }
  await gravarMarca($, 'ofereceuLigar', sessao, ofereceAgora)
  return linhas
}

/**
 * A linha de negação para a ferramenta, ou null para liberar. Quando o modelo chama a skill de ligar,
 * desligar ou modo (com ou sem o prefixo do plugin) pedindo outro modo, grava o modo só se o último prompt
 * da pessoa chamou a Sofia ou respondeu à oferta de ligar. Se a troca não ficou gravada (sem essa marca, sem
 * pasta de dados ou com a gravação falhando), a skill é negada: a Sofia não confirma um modo que não mudou.
 * O comando digitado pela pessoa não passa por aqui: ele grava no prompt.submit.
 */
async function negacao($: EngineInterface, ferramenta: string, entrada: Record<string, unknown>): Promise<string | null> {
  let estado = await lerInterruptor($)
  if (ferramenta === 'Skill' && typeof entrada.skill === 'string') {
    const cru = entrada.skill.trim().toLowerCase()
    const nome = cru.startsWith(PREFIXO_DO_PLUGIN) ? cru.slice(PREFIXO_DO_PLUGIN.length) : cru.includes(':') ? null : cru
    if (nome === 'ligar' || nome === 'desligar' || nome === 'modo') {
      const pedido = pedidoDoComando(nome, typeof entrada.args === 'string' ? entrada.args : '')
      if (pedido && pedido !== 'ensinar' && pedido !== estado.modo) {
        if (await lerMarca($, 'podeTrocarModo', await idDaSessao($))) estado = await gravarModo($, pedido)
        if (estado.modo !== pedido) return naoTroquei(nome)
      }
    }
  }
  if (estado.modo === 'ligada') return null
  const chamada = estado.modo === 'so-quando-chamada' ? await foiChamada($, await idDaSessao($)) : false
  return decidir(estado, chamada, ferramenta, entrada).negar ?? null
}

/** Os comandos do mod: mudam o modo neste computador sem passar pelo modelo. */
async function rodarComandoDeModo($: EngineInterface, modo: Modo): Promise<{ text: string; context: string[] }> {
  const estado = await gravarModo($, modo)
  if (estado.modo !== modo) {
    return { text: `Não consegui guardar o modo neste computador. A Sofia segue ${estado.modo}.`, context: [linhaDoModo(estado.modo)] }
  }
  const textos: Record<Modo, string> = {
    ligada: 'Sofia ligada neste computador.',
    'so-quando-chamada': 'Sofia no modo so-quando-chamada: ela só age quando você a chama pelo nome.',
    desligada: 'Sofia desligada neste computador. Para ligar de novo: /sofia-ligar, ou diga "liga a Sofia".',
  }
  return { text: textos[modo], context: [linhaDoModo(modo)] }
}

// As ferramentas do planejamento no conector Sofia Estrategista, pelos dois nomes com que chegam: o do
// conector do plugin sofia-estrategista (.mcp.json dele) e o do conector ligado pelo site do Claude.
// planejamento_quadro traz o quadro inteiro; as outras podem mudá-lo (referencia_salvar também mexe no card).
const FERRAMENTAS_DO_PLANEJAMENTO =
  /^mcp__(?:plugin_sofia-estrategista_sofia-estrategista|claude_ai_Sofia_Estrategista)__(?:planejamento_[a-z_]+|referencia_salvar)$/
const LEITURA_DO_QUADRO = /__planejamento_quadro$/
const SEM_LEITURA = 'Os cards aparecem aqui quando a Sofia ler o seu planejamento.'
const ETAPAS = ['Brainstorming', 'Estruturar', 'Revisar', 'Lapidar', 'Gravar']
const CORES_DAS_ETAPAS = ['magenta', 'blue', 'cyan', 'yellow', 'green']
const NOME_DA_JANELA: Record<string, string> = { five_hour: 'Sessão de 5 horas', seven_day: 'Semana (7 dias)' }

// ---------- leitura ----------

/** As etapas a partir da resposta de planejamento_quadro: os dados estruturados, ou o texto "### Etapa (n)". */
export function etapasDaResposta(estruturado: unknown, texto: string): { perfil?: string; etapas: Etapa[] } {
  const dados = estruturado as
    | {
        perfilId?: string
        colunas?: { rotulo?: string; cards?: unknown[] }[]
        perfis?: { id?: string; arroba?: string; rede?: string }[]
      }
    | undefined
  if (dados && Array.isArray(dados.colunas)) {
    const p = Array.isArray(dados.perfis) ? dados.perfis.find((x) => x.id === dados.perfilId) : undefined
    return {
      perfil: p?.arroba ? comArroba(p.arroba, p.rede) : dados.perfilId,
      etapas: dados.colunas.map((c) => ({ rotulo: c.rotulo ?? '?', total: Array.isArray(c.cards) ? c.cards.length : 0 })),
    }
  }
  const etapas: Etapa[] = []
  for (const linha of texto.split('\n')) {
    const m = /^###\s+(.+?)\s+\((\d+)\)\s*$/.exec(linha.trim())
    const rotulo = m?.[1]
    if (rotulo && ETAPAS.includes(rotulo)) etapas.push({ rotulo, total: Number(m?.[2] ?? 0) })
  }
  const id = /^##\s+Quadro do perfil\s+(.+)$/m.exec(texto)?.[1]?.trim()
  // Na lista do fim do texto: "- `id`: nome (@arroba, rede)".
  const linha = id ? new RegExp('^- `' + id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '`: .*\\(([^,()]+), ([^()]+)\\)\\s*$', 'm').exec(texto) : null
  const perfil = linha?.[1] ? comArroba(linha[1], linha[2]) : id
  return { perfil, etapas }
}

/** "@mechamedebento · Instagram", com o @ na frente mesmo que o site tenha guardado sem. */
export function comArroba(arroba: string, rede?: string): string {
  const a = arroba.trim()
  const comAt = a.startsWith('@') ? a : `@${a}`
  return rede?.trim() ? `${comAt} · ${rede.trim()}` : comAt
}

/** As janelas do Claude que o painel mostra, na ordem 5 horas e 7 dias. */
export function janelasDoUso(limites: readonly { kind: string; percentUsed: number; resetsAt?: string }[]): Janela[] {
  return limites
    .filter((l) => l.kind in NOME_DA_JANELA)
    .sort((a, b) => (a.kind === 'five_hour' ? -1 : b.kind === 'five_hour' ? 1 : 0))
    .map((l) => {
      const zera = l.resetsAt ? Date.parse(l.resetsAt) : NaN
      return { tipo: l.kind, usado: l.percentUsed, ...(Number.isFinite(zera) ? { zeraEm: zera } : {}) }
    })
}

// ---------- desenho ----------

/** Uma barra de `largura` blocos com `fracao` (0 a 1) preenchida. */
export function barra(fracao: number, largura: number): [string, string] {
  const cheios = Math.max(0, Math.min(largura, Math.round(fracao * largura)))
  return ['█'.repeat(cheios), '░'.repeat(largura - cheios)]
}

/** Quanto falta para a janela zerar: "1h 48min", "3d 4h", "12min". */
export function quantoFalta(ms: number): string {
  if (ms <= 0) return 'agora'
  const min = Math.ceil(ms / 60000)
  const dias = Math.floor(min / 1440)
  const horas = Math.floor((min % 1440) / 60)
  const minutos = min % 60
  if (dias > 0) return `${dias}d ${horas}h`
  if (horas > 0) return `${horas}h ${String(minutos).padStart(2, '0')}min`
  return `${minutos}min`
}

const corDoUso = (p: number) => (p >= 85 ? 'red' : p >= 60 ? 'yellow' : 'green')
const hora = (ms: number) => {
  const d = new Date(ms)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

/**
 * O texto do resultado como o modelo leu: `text`, que o Claude Code põe em todo resultado. Se faltar, os
 * blocos de texto do resultado do MCP (`content`).
 */
export function textoDoResultado(r: { text?: string; result?: unknown }): string {
  if (typeof r.text === 'string') return r.text
  const bruto = r.result as { content?: unknown } | unknown[] | string | undefined
  if (typeof bruto === 'string') return bruto
  const blocos = Array.isArray(bruto) ? bruto : Array.isArray((bruto as { content?: unknown })?.content) ? ((bruto as { content: unknown[] }).content) : []
  return blocos
    .map((b) => {
      const bloco = b as { type?: unknown; text?: unknown }
      return bloco?.type === 'text' && typeof bloco.text === 'string' ? bloco.text : ''
    })
    .join('\n')
}

/** Os dados estruturados do resultado do MCP (`structuredContent`), quando vierem no registro da ferramenta. */
export function estruturadoDoResultado(resultado: unknown): unknown {
  if (typeof resultado !== 'object' || resultado === null) return undefined
  const r = resultado as { structuredContent?: unknown; colunas?: unknown }
  if (r.structuredContent !== undefined) return r.structuredContent
  return Array.isArray(r.colunas) ? r : undefined
}

/**
 * Guarda o que a chamada da Sofia ao conector diz do quadro. Só lê o resultado: nunca muda o que o modelo
 * recebe. Negada (a Sofia desligada), nada muda.
 * - planejamento_quadro com sucesso: as contagens por etapa;
 * - planejamento_quadro com erro: o motivo, se ainda não há quadro lido (um quadro lido antes fica);
 * - outra ferramenta do planejamento que grava (não somente leitura) e deu certo: o quadro lido pode ter
 *   mudado, e o painel avisa até a próxima leitura.
 */
async function guardarDoResultado($: EngineInterface, ferramenta: string, r: ToolCallResult) {
  if (r.deny !== undefined) return
  if (LEITURA_DO_QUADRO.test(ferramenta)) {
    const agora = await $.clock.now()
    const texto = textoDoResultado(r)
    if (r.isError) {
      const atual = await read($, quadro)
      if (atual?.situacao === 'ok') return
      const motivo = texto.trim().slice(0, 160) || 'O conector não devolveu o quadro.'
      const semLeitura: Quadro = { situacao: 'sem-leitura', motivo, lidoEm: agora }
      await update($, quadro, () => semLeitura)
      return
    }
    const { perfil, etapas } = etapasDaResposta(estruturadoDoResultado(r.result), texto)
    // Sem etapas e sem perfil, a resposta não deu para ler: o painel fica como estava. Com o perfil, o quadro
    // está vazio de verdade e o painel mostra 0 cards.
    if (etapas.length === 0 && !perfil) return
    const lido: Quadro = { situacao: 'ok', perfil: perfil ?? 'sem perfil', etapas, lidoEm: agora, mudouDepois: false }
    await update($, quadro, () => lido)
    // A barra de status é enfeite: uma falha nela (inclusive com a sessão já fechada) não vira erro solto.
    atualizarStatus($).catch(() => undefined)
    return
  }
  if (r.isError || r.isReadOnly) return
  await update($, quadro, (q) => (q?.situacao === 'ok' && !q.mudouDepois ? { ...q, mudouDepois: true } : q))
}

/** A linha curta da barra de status, para quando o painel não cabe na tela. */
async function atualizarStatus($: EngineInterface) {
    const q = await read($, quadro)
    const js = await read($, janelas)
    const modo = await read($, modoNoPainel)
    const partes: string[] = []
    if (modo === 'desligada') partes.push('desligada')
    else if (q?.situacao === 'ok') partes.push(`${q.etapas.reduce((s, e) => s + e.total, 0)} cards`)
    for (const j of js) partes.push(`${j.tipo === 'five_hour' ? '5h' : '7d'} ${Math.round(j.usado)}%`)
    $.ui.status(partes.length ? `Sofia · ${partes.join(' · ')}` : undefined)
}

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'sofia-painel', description: 'Abre o painel da Sofia: cards por etapa e uso do Claude' })
    await $.command.register({ name: 'sofia-ligar', description: 'Liga a Sofia neste computador' })
    await $.command.register({ name: 'sofia-desligar', description: 'Desliga a Sofia neste computador' })
    await $.command.register({
      name: 'sofia-modo',
      description: 'Mostra ou troca o modo da Sofia neste computador',
      argumentHint: '[ligada|so-quando-chamada|desligada]',
    })
    await $.command.register({ name: 'sofia-ensinar', description: 'A Sofia mostra como funciona' })
    await lerInterruptor($)
    const uso = await $.session.usage()
    await update($, janelas, () => janelasDoUso(uso.rateLimits))
    $.ui.open({ id: PAINEL, title: TITULO }).catch(() => undefined)
    return next(e)
  })

  on('command.run', { command: 'sofia-painel' }, async ($) => {
    await $.ui.open({ id: PAINEL, title: TITULO })
    return { text: 'Painel da Sofia aberto.' }
  })

  // O uso muda a cada resposta: o engine avisa quando uma janela anda um ponto inteiro.
  on('session.measure', async ($, e, next) => {
    if (e.changed.includes('rateLimits')) {
      await update($, janelas, () => janelasDoUso(e.rateLimits))
      await atualizarStatus($)
    }
    return next(e)
  })

  // O interruptor nega a ferramenta da Sofia quando o modo manda. Se a decisão falhar, a ferramenta segue:
  // na dúvida, ligada.
  // O try cobre só a decisão: o next(e) roda uma vez, fora dele. O .catch fica para o que escapar; nele o
  // next é seguro de repetir (tipo Caught): se o hook já chamou next, next(e) devolve o mesmo resultado sem
  // rodar a ferramenta de novo; se não chamou, roda uma vez.
  on('tool.call', async ($, e, next) => {
    let negar: string | null = null
    try {
      negar = await negacao($, e.tool, e as unknown as Record<string, unknown>)
    } catch {
      negar = null
    }
    if (negar) return { deny: negar }
    try {
      await primeiroUsoNaFerramenta($, e.tool, e as unknown as Record<string, unknown>)
    } catch {
      // sem a marca, a linha do primeiro uso volta no próximo prompt
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  // O painel aprende o quadro com as chamadas que a Sofia já faz ao conector: espera a ferramenta rodar, lê o
  // resultado e o devolve sem mudar nada. Uma falha ao guardar nunca chega ao modelo.
  on('tool.call', { tool: FERRAMENTAS_DO_PLANEJAMENTO }, async ($, e, next) => {
    const r = await next(e)
    try {
      await guardarDoResultado($, e.tool, r)
    } catch {
      // o painel fica com a leitura anterior
    }
    return r
  }).catch(($, e, next) => next(e))

  // O que a pessoa digitou: muda o modo quando a frase ou o comando pede, marca o chamado da sessão e põe
  // para o modelo a linha do interruptor local (e a de negação quando o modo nega). Avisos de tarefa em
  // segundo plano e mensagens de outra sessão não são a pessoa: passam sem nada.
  on('prompt.submit', async ($, e, next) => {
    if (e.origin?.kind === 'task-notification' || e.origin?.kind === 'peer') return next(e)
    let linhas: string[] = []
    try {
      linhas = await linhasDoPrompt($, e.text, e.command)
    } catch {
      linhas = []
    }
    return next(linhas.length ? { ...e, context: [...(e.context ?? []), ...linhas] } : e)
  }).catch(($, e, next) => next(e))

  on('command.run', { command: 'sofia-ligar' }, ($) => rodarComandoDeModo($, 'ligada'))
  on('command.run', { command: 'sofia-desligar' }, ($) => rodarComandoDeModo($, 'desligada'))

  on('command.run', { command: 'sofia-modo' }, async ($, e) => {
    const pedido = e.args.trim()
    if (!pedido) {
      const { modo } = await lerInterruptor($)
      return { text: `A Sofia está ${modo} neste computador. ${COMO_TROCAR}`, context: [linhaDoModo(modo)] }
    }
    const modo = modoDoTexto(pedido)
    if (!modo) return { text: `Não conheço o modo "${pedido}". ${COMO_TROCAR}` }
    return rodarComandoDeModo($, modo)
  })

  on('command.run', { command: 'sofia-ensinar' }, async ($) => {
    try {
      const estado = await lerInterruptor($)
      if (estado.modo !== 'desligada') await abrirPerguntaDoModo($, estado, await idDaSessao($))
    } catch {
      // sem a janela, a pessoa responde com o nome ("Sofia, só quando eu chamar") ou pelo comando
    }
    // O comando só põe a linha no contexto: o tutorial vem na próxima resposta, não agora.
    return { text: 'Diga qualquer coisa e a Sofia mostra como funciona.', context: [LINHA_ENSINAR] }
  })

  on('ui.render', { component: 'Pane', requestId: PAINEL }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const desligada = (await read($, modoNoPainel)) === 'desligada'
    // Desligada, o quadro não aparece (nem o lido antes): o painel mostra o aviso e o uso do Claude.
    const q = desligada ? undefined : await read($, quadro)
    const js = await read($, janelas)
    const agora = await $.clock.now()
    const colunas = e.viewport?.columns ?? 60
    const larguraDaBarra = Math.max(8, Math.min(30, colunas - 30))

    const maior = q?.situacao === 'ok' ? Math.max(1, ...q.etapas.map((x) => x.total)) : 1
    const total = q?.situacao === 'ok' ? q.etapas.reduce((s, x) => s + x.total, 0) : 0

    return (
      <Box flexDirection="column" paddingX={1}>
        <Box justifyContent="space-between">
          <Text bold color="magenta">✦ Sofia Estrategista</Text>
          {q && <Text dimColor>lido às {hora(q.lidoEm)}</Text>}
        </Box>

        <Box marginTop={1} flexDirection="column">
          <Box>
            <Text bold>Planejamento</Text>
            {q?.situacao === 'ok' && <Text color="magenta">{`  ${q.perfil}`}</Text>}
          </Box>
          {desligada && <Text color="yellow">Sofia desligada</Text>}
          {desligada && <Text dimColor>Para ligar: /sofia-ligar, ou diga "liga a Sofia".</Text>}
          {!desligada && (q === null || q === undefined) && <Text dimColor>{SEM_LEITURA}</Text>}
          {q?.situacao === 'sem-leitura' && <Text color="yellow">{q.motivo}</Text>}
          {q?.situacao === 'ok' &&
            q.etapas.map((etapa, i) => {
              const [cheio, vazio] = barra(etapa.total / maior, larguraDaBarra)
              return (
                <Box key={etapa.rotulo}>
                  <Text>{etapa.rotulo.padEnd(14)}</Text>
                  <Text color={CORES_DAS_ETAPAS[i % CORES_DAS_ETAPAS.length]}>{cheio}</Text>
                  <Text dimColor>{vazio}</Text>
                  <Text bold> {String(etapa.total).padStart(3)}</Text>
                </Box>
              )
            })}
          {q?.situacao === 'ok' && <Text dimColor>{total === 1 ? '1 card no quadro' : `${total} cards no quadro`}</Text>}
          {q?.situacao === 'ok' && q.mudouDepois && (
            <Text dimColor>O quadro mudou depois desta leitura. Atualiza quando a Sofia ler o planejamento de novo.</Text>
          )}
        </Box>

        <Box marginTop={1} flexDirection="column">
          <Text bold>Uso do Claude</Text>
          {js.length === 0 && <Text dimColor>Aparece depois da primeira resposta, em planos com limite de uso.</Text>}
          {js.map((j) => {
            const [cheio, vazio] = barra(j.usado / 100, larguraDaBarra)
            return (
              <Box key={j.tipo} flexDirection="column">
                <Box>
                  <Text>{(NOME_DA_JANELA[j.tipo] ?? j.tipo).padEnd(18)}</Text>
                  <Text color={corDoUso(j.usado)}>{cheio}</Text>
                  <Text dimColor>{vazio}</Text>
                  <Text bold color={corDoUso(j.usado)}> {String(Math.round(j.usado)).padStart(3)}%</Text>
                </Box>
                <Text dimColor>
                  {'  '}
                  {j.zeraEm ? `zera em ${quantoFalta(j.zeraEm - agora)} (às ${hora(j.zeraEm)})` : 'sem horário de reinício'}
                  {` · faltam ${Math.max(0, 100 - Math.round(j.usado))}%`}
                </Text>
              </Box>
            )
          })}
        </Box>
      </Box>
    )
  })
}
