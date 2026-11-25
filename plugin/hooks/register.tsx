import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Etapa, Janela, ModoDoInterruptor, Quadro } from '../types'
import {
  AVISO_DESLIGADA,
  AVISO_SO_QUANDO_CHAMADA,
  chamaSofia,
  decidir,
  lerEstado,
  pedidoDeModo,
} from './interruptor'
import type { Estado, Modo } from './interruptor'

// Painel da Sofia Estrategista: quantos cards há em cada etapa do planejamento no site e quanto já foi
// usado das janelas de 5 horas e de 7 dias do Claude, com quanto falta para cada uma zerar.
// Também é o interruptor da Sofia neste computador: lê e grava estado.json na pasta de dados do plugin,
// nega as ferramentas dela quando o modo manda (a regra está em interruptor.ts) e avisa o modelo do modo.
// Só roda onde há mods (Claude Code): no site, no app de conversa e no Codex este arquivo fica parado.

const PAINEL = 'sofia-painel'
const TITULO = 'Sofia Estrategista'
// Troque a marca quando o formato guardado mudar: um reload mantém o que a versão anterior guardou.
const quadro = atom({ plugin: 'sofia-estrategista', key: 'quadro' } as const, null, { shape: 'quadro-1' })
const janelas = atom({ plugin: 'sofia-estrategista', key: 'janelas' } as const, [], { shape: 'janelas-1' })
const modoNoPainel = atom({ plugin: 'sofia-estrategista', key: 'modo' } as const, 'ligada' as ModoDoInterruptor, {
  shape: 'modo-1',
})

// ---------- interruptor ----------

const ESTADO = 'estado.json'
const PREFIXO_DO_PLUGIN = 'sofia-estrategista:'
const ESTOU_DESLIGADA = 'Estou desligada aqui. Quer que eu ligue?'
const LINHA_DESLIGADA_CHAMADA = `A pessoa chamou a Sofia, mas ela está desligada aqui. Responda só: "${ESTOU_DESLIGADA}"`
const LINHA_ENSINAR =
  'A pessoa quer aprender a usar a Sofia. Mostre o tutorial de skills/sofia-estrategista/references/primeiro-uso.md, mesmo com a Sofia desligada.'
const COMO_TROCAR = 'Para trocar: /sofia-modo ligada, /sofia-modo so-quando-chamada ou /sofia-modo desligada.'
const linhaDoModo = (modo: Modo) => `Interruptor local: ${modo}.`

/** Minúsculas, sem acento, espaços e sublinhados viram hífen: "Só quando chamada" vira "so-quando-chamada". */
function modoDoTexto(texto: string): Modo | null {
  const t = texto.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().trim().replace(/[\s_]+/g, '-')
  return t === 'ligada' || t === 'so-quando-chamada' || t === 'desligada' ? t : null
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
  if (nome === 'ligar') return 'ligada'
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
    // Saiu de desligada: o painel volta a ler o quadro.
    if (antes.modo === 'desligada' && modo !== 'desligada') lerEmSegundoPlano($)
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
    return (await $.state.get({ plugin: 'sofia-estrategista', key: 'chamada', id: sessao })).value === true
  } catch {
    return false
  }
}

async function marcarChamada($: EngineInterface, sessao: string | null) {
  if (!sessao) return
  try {
    await $.state.set({ plugin: 'sofia-estrategista', key: 'chamada', id: sessao }, true)
  } catch {
    // sem o registro, o modo "só quando chamada" segue negando: a pessoa chama de novo
  }
}

/** As linhas que o modelo lê junto do que a pessoa digitou. Muda o modo quando a frase pede. */
async function linhasDoPrompt($: EngineInterface, texto: string, comando?: { name: string; args: string }): Promise<string[]> {
  const digitado = comandoDigitado(texto, comando)
  const pedido = digitado ? pedidoDoComando(digitado.nome, digitado.args) : pedidoDeModo(texto)
  let estado = await lerInterruptor($)
  if (pedido && pedido !== 'ensinar') estado = await gravarModo($, pedido)
  const sessao = await idDaSessao($)
  const chamou = digitado !== null || chamaSofia(texto)
  if (chamou) await marcarChamada($, sessao)

  const linhas = [linhaDoModo(estado.modo)]
  if (pedido === 'ensinar') linhas.push(LINHA_ENSINAR)
  // Um pedido de modo ou de "me ensina" nunca se nega.
  if (pedido) return linhas
  if (estado.modo === 'desligada') {
    linhas.push(AVISO_DESLIGADA)
    if (chamou) linhas.push(LINHA_DESLIGADA_CHAMADA)
  } else if (estado.modo === 'so-quando-chamada' && !(await foiChamada($, sessao))) {
    linhas.push(AVISO_SO_QUANDO_CHAMADA)
  }
  return linhas
}

/** A linha de negação para a ferramenta, ou null para liberar. Também grava o modo de um comando de modo. */
async function negacao($: EngineInterface, ferramenta: string, entrada: Record<string, unknown>): Promise<string | null> {
  let estado = await lerInterruptor($)
  if (ferramenta === 'Skill' && typeof entrada.skill === 'string') {
    const nome = entrada.skill.trim().toLowerCase()
    if (nome.startsWith(PREFIXO_DO_PLUGIN)) {
      const pedido = pedidoDoComando(nome.slice(PREFIXO_DO_PLUGIN.length), typeof entrada.args === 'string' ? entrada.args : '')
      if (pedido && pedido !== 'ensinar' && pedido !== estado.modo) estado = await gravarModo($, pedido)
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

// O conector: a chave dele no .mcp.json deste plugin (a primeira), e os nomes com que o /mcp lista o
// mesmo conector quando a pessoa o ligou pelo site do Claude em vez do plugin.
const CONECTORES = ['sofia-estrategista', 'claude.ai Sofia Estrategista', 'Sofia Estrategista']
// O nome com que o /mcp lista o conector deste plugin: é o que a pessoa procura na lista para entrar.
const NOME_NO_MCP = 'plugin:sofia-estrategista:sofia-estrategista'
const ETAPAS = ['Brainstorming', 'Estruturar', 'Revisar', 'Lapidar', 'Gravar']
const CORES_DAS_ETAPAS = ['magenta', 'blue', 'cyan', 'yellow', 'green']
const NOME_DA_JANELA: Record<string, string> = { five_hour: 'Sessão de 5 horas', seven_day: 'Semana (7 dias)' }
const RELER_A_CADA_MS = 5 * 60 * 1000

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

// O nome com que o conector respondeu da última vez, e se uma leitura já está em andamento.
let servidor: string | null = null
let lendo = false

/** Lê o quadro em segundo plano: uma falha na leitura nunca trava a ferramenta nem a sessão. */
function lerEmSegundoPlano($: EngineInterface) {
  lerQuadro($).catch(() => undefined)
}

/** Lê o quadro no conector e guarda as contagens por etapa (ou o motivo de não ter lido). */
async function lerQuadro($: EngineInterface) {
    if (lendo) return
    lendo = true
    try {
      // Desligada, a Sofia não toca no conector: o painel mostra só o uso do Claude.
      if ((await lerInterruptor($)).modo === 'desligada') return
      const agora = await $.clock.now()
      let motivo = `O conector Sofia Estrategista não está ligado. Digite /mcp, escolha ${NOME_NO_MCP} e entre com o e-mail do curso.`
      const candidatos = servidor ? [servidor] : CONECTORES
      for (const nome of candidatos) {
        const ligado = await $.mcp.connect(nome).catch(() => null)
        if (!ligado || !ligado.isConnected) continue
        try {
          const r = await $.mcp.call(ligado.server, 'planejamento_quadro', {})
          const texto = r.content.map((b) => (b.type === 'text' && typeof b.text === 'string' ? b.text : '')).join('\n')
          if (r.isError) {
            motivo = texto.slice(0, 160) || 'O conector não devolveu o quadro.'
            continue
          }
          const { perfil, etapas } = etapasDaResposta(r.structuredContent, texto)
          if (etapas.length === 0) continue
          servidor = ligado.server
          const lido: Quadro = { situacao: 'ok', perfil: perfil ?? 'sem perfil', etapas, lidoEm: agora }
          await update($, quadro, () => lido)
          atualizarStatus($)
          return
        } catch {
          motivo = `O conector Sofia Estrategista não respondeu. Digite /mcp, escolha ${ligado.server} e entre de novo com o e-mail do curso.`
        }
      }
      servidor = null
      const semConector: Quadro = { situacao: 'sem-conector', motivo, lidoEm: agora }
      await update($, quadro, () => semConector)
    } finally {
      lendo = false
    }
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
    lerEmSegundoPlano($)
    $.clock.every(RELER_A_CADA_MS, () => lerEmSegundoPlano($))
    $.ui.open({ id: PAINEL, title: TITULO }).catch(() => undefined)
    return next(e)
  })

  on('command.run', { command: 'sofia-painel' }, async ($) => {
    await $.ui.open({ id: PAINEL, title: TITULO })
    lerEmSegundoPlano($)
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

  // O interruptor nega a ferramenta da Sofia quando o modo manda. Depois de uma ferramenta do planejamento,
  // o quadro pode ter mudado: lê de novo. Se este hook falhar, a ferramenta segue: na dúvida, ligada.
  on('tool.call', async ($, e, next) => {
    const negar = await negacao($, e.tool, e as unknown as Record<string, unknown>)
    if (negar) return { deny: negar }
    const r = await next(e)
    if (/planejamento_|referencia_salvar/.test(e.tool) && !/planejamento_quadro$/.test(e.tool)) lerEmSegundoPlano($)
    return r
  }).catch(($, e, next) => next(e))

  // O que a pessoa digitou: muda o modo quando a frase ou o comando pede, marca o chamado da sessão e põe
  // para o modelo a linha do interruptor local (e a de negação quando o modo nega). Avisos de tarefa em
  // segundo plano e mensagens de outra sessão não são a pessoa: passam sem nada.
  on('prompt.submit', async ($, e, next) => {
    if (e.origin?.kind === 'task-notification' || e.origin?.kind === 'peer') return next(e)
    const linhas = await linhasDoPrompt($, e.text, e.command)
    return next({ ...e, context: [...(e.context ?? []), ...linhas] })
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

  on('command.run', { command: 'sofia-ensinar' }, async () => ({
    text: 'A Sofia vai mostrar como funciona.',
    context: [LINHA_ENSINAR],
  }))

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
          {q === null && <Text dimColor>Lendo o quadro no site…</Text>}
          {q?.situacao === 'sem-conector' && <Text color="yellow">{q.motivo}</Text>}
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
