import { describe, expect, mock, test } from 'claude-code/testing'
import type { CommandRunInput, On, PromptOrigin, PromptSubmitInput } from 'claude-code'

import { AVISO_DESLIGADA, AVISO_SO_QUANDO_CHAMADA } from './interruptor'

// O mod do painel com o interruptor. Cada hook do teste faz o papel do engine: a pasta de dados, o id da
// sessão, os arquivos (em memória) e a ferramenta que roda de fato (inclusive as do conector).

const PASTA = '/dados/sofia-painel'
const ARQUIVO = `${PASTA}/estado.json`
const ESTOU_DESLIGADA = 'Estou desligada aqui. Quer que eu ligue?'
const NAO_TROQUEI = 'Não troquei o modo da Sofia.'
const DISSE_SIM = 'A pessoa disse sim: a Sofia está ligada. Confirme em uma linha e faça o pedido de antes.'

type Mundo = {
  arquivos: Map<string, string>
  sessao: { id: string }
  /** Quantas vezes o mod pediu ao engine para ligar ou chamar um servidor MCP: tem de ser zero. */
  chamadasAoMcp: () => number
  /** A resposta que cada ferramenta devolve ao rodar, pelo nome; as outras devolvem `{ result: {} }`. */
  respostas: Map<string, Record<string, unknown>>
  comandos: string[]
  relogio: { settle: () => Promise<void> }
  modoGravado: () => string | undefined
  /** Quantas vezes a ferramenta rodou de fato, e se ela lança erro ao rodar. */
  execucoes: () => number
  ferramenta: { falha: boolean }
}

/** Monta o engine de mentira. `estado` é o texto de estado.json (undefined: o arquivo não existe). */
function mundo(on: On, estado?: string): Mundo {
  const arquivos = new Map<string, string>()
  if (estado !== undefined) arquivos.set(ARQUIVO, estado)
  const sessao = { id: 'sessao-1' }
  let mcp = 0
  const respostas = new Map<string, Record<string, unknown>>()
  const comandos: string[] = []
  let execucoes = 0
  const ferramenta = { falha: false }

  on('process.hookEnv', () => ({ value: { CLAUDE_PLUGIN_DATA: PASTA } }))
  on('session.id', () => ({ value: sessao.id }))
  on('fs.read', (_, e) => (arquivos.has(e.path) ? { value: arquivos.get(e.path) as string } : { deny: `ENOENT: ${e.path}` }))
  on('fs.write', (_, e) => {
    arquivos.set(e.path, e.text)
    return { value: undefined }
  })
  on('fs.exists', (_, e) => ({ value: arquivos.has(e.path) }))
  on('tool.call', (_, e) => {
    execucoes++
    if (ferramenta.falha) throw new Error('a ferramenta quebrou')
    return (respostas.get(e.tool) ?? { result: {} }) as never
  })
  on('mcp.connect', () => {
    mcp++
    return { value: { server: 'sofia-estrategista', isConnected: true } } as never
  })
  on('mcp.call', () => {
    mcp++
    return { value: { content: [], isError: false } } as never
  })
  on('command.register', (_, e) => {
    comandos.push(e.name)
    return { value: { command: e.name } } as never
  })
  on('prompt.submit', (_, e) => ({ text: e.text, context: e.context }) as never)
  on('ui.open', () => ({ value: { isPlaced: true } }) as never)
  on('ui.status', () => ({ value: undefined }) as never)
  on('session.usage', () => ({ value: { startedAt: 0, context: { tokens: 0, window: 1 }, rateLimits: [] } }) as never)
  on('session.start', (_, e) => ({ cwd: e.cwd }) as never)
  const relogio = mock.clock(on, { now: Date.parse('2026-11-25T12:00:00Z') })

  return {
    arquivos,
    sessao,
    chamadasAoMcp: () => mcp,
    respostas,
    comandos,
    relogio,
    execucoes: () => execucoes,
    ferramenta,
    modoGravado: () => {
      const texto = arquivos.get(ARQUIVO)
      if (texto === undefined) return undefined
      try {
        return JSON.parse(texto).modo
      } catch {
        return undefined
      }
    },
  }
}

/** O que a pessoa digita no terminal, como o engine carimba. */
function digitado(text: string, origem: PromptOrigin = { kind: 'composer' }): PromptSubmitInput {
  return { text, wait: false, origin: origem }
}

/** Um comando do mod digitado no terminal. */
function comando(nome: string, args: string): CommandRunInput {
  return { command: nome, args, origin: { kind: 'composer' }, presentation: { isFullscreen: false, columns: 100 } }
}

const DESLIGADA = JSON.stringify({ modo: 'desligada', apresentada: true, mudouEm: '2026-11-20T10:00:00.000Z' })
const SO_QUANDO = JSON.stringify({ modo: 'so-quando-chamada', apresentada: true, mudouEm: '2026-11-20T10:00:00.000Z' })

const PAINEL = {
  plugin: 'sofia-painel',
  component: 'Pane',
  requestId: 'sofia-painel',
  props: {
    title: 'Sofia Estrategista',
    isFocused: false,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 30 },
    view: {},
  },
} as const

describe('desligada: o que nega e o que passa', () => {
  test('a skill da Sofia é negada com a linha de desligada', async ($, on) => {
    mundo(on, DESLIGADA)
    const r = await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)
    expect(r).toMatchObject({ deny: AVISO_DESLIGADA })
  })

  test('ferramenta que não é da Sofia passa', async ($, on) => {
    mundo(on, DESLIGADA)
    const r = await $.tool.call({ tool: 'Bash', command: 'ls' } as never)
    expect(r.deny).toBeUndefined()
  })

  test('os comandos de ligar passam, como ferramenta e como comando do mod', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    const pelaFerramenta = await $.tool.call({ tool: 'Skill', skill: 'sofia-ligar' } as never)
    expect(pelaFerramenta.deny).toBeUndefined()
    // A skill de ligar do plugin sem a pessoa ter pedido: o modo não muda e a Sofia não pode confirmar.
    const doPlugin = await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:ligar' } as never)
    expect(doPlugin.deny).toContain(NAO_TROQUEI)
    expect(m.modoGravado()).toBe('desligada')
    const r = await $.command.run(comando('sofia-ligar', ''))
    expect(r.text).toContain('ligada')
    expect(m.modoGravado()).toBe('ligada')
  })

  test('o agente da equipe é negado', async ($, on) => {
    mundo(on, DESLIGADA)
    const r = await $.tool.call({
      tool: 'Agent',
      subagent_type: 'sofia-estrategista:roteirista',
      description: 'roteiro',
      prompt: 'escreve',
    } as never)
    expect(r).toMatchObject({ deny: AVISO_DESLIGADA })
  })

  test('a skill sem o prefixo do plugin é negada', async ($, on) => {
    mundo(on, DESLIGADA)
    const r = await $.tool.call({ tool: 'Skill', skill: 'sofia-editora' } as never)
    expect(r).toMatchObject({ deny: AVISO_DESLIGADA })
  })

  test('a ferramenta do conector é negada', async ($, on) => {
    mundo(on, DESLIGADA)
    const r = await $.tool.call({ tool: 'mcp__claude_ai_Sofia_Estrategista__planejamento_quadro' } as never)
    expect(r).toMatchObject({ deny: AVISO_DESLIGADA })
  })
})

describe('o que a pessoa digita', () => {
  test('"Sofia, desliga" grava desligada e a skill seguinte é negada', async ($, on) => {
    const m = mundo(on)
    const p = await $.prompt.submit(digitado('Sofia, desliga'))
    expect(m.modoGravado()).toBe('desligada')
    expect(p.context).toContain('Interruptor local: desligada.')
    const gravado = JSON.parse(m.arquivos.get(ARQUIVO) as string)
    expect(gravado.mudouEm).toBe('2026-11-25T12:00:00.000Z')
    expect(gravado.apresentada).toBe(false)
    const r = await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)
    expect(r).toMatchObject({ deny: AVISO_DESLIGADA })
  })

  test('cada prompt leva a linha do interruptor local', async ($, on) => {
    mundo(on)
    const p = await $.prompt.submit(digitado('faz um resumo do arquivo'))
    expect(p.context).toContain('Interruptor local: ligada.')
  })

  test('desligada, "Sofia, faz o roteiro": responde só a frase de desligada e o modo não muda', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    const p = await $.prompt.submit(digitado('Sofia, faz o roteiro'))
    expect((p.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(true)
    expect(p.context).toContain('Interruptor local: desligada.')
    expect(p.context).toContain(AVISO_DESLIGADA)
    expect(m.modoGravado()).toBe('desligada')
  })

  test('desligada, comando digitado do plugin: responde só a frase de desligada', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    const p = await $.prompt.submit(digitado('/sofia-estrategista:roteiro card 3'))
    expect((p.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(true)
    expect(m.modoGravado()).toBe('desligada')
  })

  test('desligada, "liga a Sofia" liga e não leva a frase de desligada', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    const p = await $.prompt.submit(digitado('liga a Sofia'))
    expect(m.modoGravado()).toBe('ligada')
    expect((p.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(false)
    expect(p.context).toContain('Interruptor local: ligada.')
  })

  test('desligada, comando digitado de ligar grava ligada', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    const p = await $.prompt.submit(digitado('/sofia-estrategista:ligar'))
    expect(m.modoGravado()).toBe('ligada')
    expect((p.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(false)
  })

  test('comando digitado "ligar só quando chamada" grava so-quando-chamada', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.prompt.submit(digitado('/sofia-estrategista:ligar só quando chamada'))
    expect(m.modoGravado()).toBe('so-quando-chamada')
  })

  test('comando digitado "ligar so-quando-chamada" também', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.prompt.submit(digitado('/sofia-estrategista:ligar so-quando-chamada'))
    expect(m.modoGravado()).toBe('so-quando-chamada')
  })

  test('a skill de ligar com "só quando chamada" grava so-quando-chamada', async ($, on) => {
    const m = mundo(on)
    await $.prompt.submit(digitado('Sofia, aparece só quando eu pedir'))
    const r = await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:ligar', args: 'só quando chamada' } as never)
    expect(r.deny).toBeUndefined()
    expect(m.modoGravado()).toBe('so-quando-chamada')
  })

  test('desligada, prompt com caminho ou e-mail não vira a oferta', async ($, on) => {
    mundo(on, DESLIGADA)
    for (const t of ['corrige o teste em skills/sofia-estrategista/SKILL.md', 'sofia-estrategista', 'o e-mail sofia@x.com']) {
      const p = await $.prompt.submit(digitado(t))
      expect((p.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(false)
      expect(p.context).toContain(AVISO_DESLIGADA)
    }
    const p = await $.prompt.submit(digitado('Sofia, faz um roteiro'))
    const linha = (p.context ?? []).find((c) => c.includes(ESTOU_DESLIGADA))
    expect(linha).toContain('e não de um arquivo ou de outra pessoa chamada Sofia')
    expect(linha).toContain('senão, atenda o pedido sem a Sofia')
  })

  test('"Sofia, me ensina" pede o tutorial sem mudar o modo', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    const p = await $.prompt.submit(digitado('Sofia, me ensina'))
    expect((p.context ?? []).some((c) => c.includes('primeiro-uso.md'))).toBe(true)
    expect((p.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(false)
    expect(m.modoGravado()).toBe('desligada')
  })
})

describe('só quando chamada', () => {
  test('sem chamado, a skill é negada', async ($, on) => {
    mundo(on, SO_QUANDO)
    const p = await $.prompt.submit(digitado('faz um roteiro sobre pão'))
    expect(p.context).toContain(AVISO_SO_QUANDO_CHAMADA)
    const r = await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)
    expect(r).toMatchObject({ deny: AVISO_SO_QUANDO_CHAMADA })
  })

  test('chamada pelo nome, a skill e o agente passam a sessão inteira; outra sessão volta a negar', async ($, on) => {
    const m = mundo(on, SO_QUANDO)
    const p = await $.prompt.submit(digitado('Sofia, me ajuda'))
    expect(p.context).not.toContain(AVISO_SO_QUANDO_CHAMADA)
    expect((await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)).deny).toBeUndefined()
    const agente = await $.tool.call({
      tool: 'Agent',
      subagent_type: 'sofia-estrategista:roteirista',
      description: 'roteiro',
      prompt: 'escreve',
    } as never)
    expect(agente.deny).toBeUndefined()

    await $.prompt.submit(digitado('o segundo'))
    expect((await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)).deny).toBeUndefined()

    m.sessao.id = 'sessao-2'
    const r = await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)
    expect(r).toMatchObject({ deny: AVISO_SO_QUANDO_CHAMADA })
  })

  test('aviso de tarefa em segundo plano e mensagem de outra sessão não contam como chamado', async ($, on) => {
    mundo(on, SO_QUANDO)
    const tarefa = await $.prompt.submit(digitado('Sofia terminou a pesquisa', { kind: 'task-notification' }))
    expect(tarefa.context ?? []).not.toContain('Interruptor local: so-quando-chamada.')
    await $.prompt.submit(digitado('Sofia, o roteiro ficou assim', { kind: 'peer' }))
    const r = await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)
    expect(r.deny).toBe(AVISO_SO_QUANDO_CHAMADA)
  })

  test('um prompt sem o nome não libera', async ($, on) => {
    mundo(on, SO_QUANDO)
    await $.prompt.submit(digitado('continua'))
    const r = await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)
    expect(r.deny).toBe(AVISO_SO_QUANDO_CHAMADA)
  })
})

describe('estado.json torto ou ausente', () => {
  test('corrompido: tudo passa, como ligada', async ($, on) => {
    mundo(on, '{ isto não é json')
    const p = await $.prompt.submit(digitado('Sofia, faz o roteiro'))
    expect(p.context).toContain('Interruptor local: ligada.')
    expect((await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)).deny).toBeUndefined()
    expect((await $.tool.call({ tool: 'mcp__plugin_sofia-estrategista_sofia-estrategista__planejamento_quadro' } as never)).deny).toBeUndefined()
  })

  test('sem arquivo: ligada', async ($, on) => {
    mundo(on)
    expect((await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)).deny).toBeUndefined()
  })

  test('sem pasta de dados: ligada, e nada derruba', async ($, on) => {
    on('process.hookEnv', () => ({ value: {} }))
    on('session.id', () => ({ value: 'sessao-1' }))
    on('tool.call', () => ({ result: {} }) as never)
    on('prompt.submit', (_, e) => ({ text: e.text, context: e.context }) as never)
    expect((await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)).deny).toBeUndefined()
    const p = await $.prompt.submit(digitado('Sofia, desliga'))
    expect(p.context).toContain('Interruptor local: ligada.')
  })
})

describe('comandos do mod', () => {
  test('sofia-desligar e sofia-modo gravam o modo', async ($, on) => {
    const m = mundo(on)
    await $.command.run(comando('sofia-desligar', ''))
    expect(m.modoGravado()).toBe('desligada')
    await $.command.run(comando('sofia-modo', 'so-quando-chamada'))
    expect(m.modoGravado()).toBe('so-quando-chamada')
    await $.command.run(comando('sofia-modo', 'ligada'))
    expect(m.modoGravado()).toBe('ligada')
  })

  test('sofia-modo com valor desconhecido não muda nada', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    const r = await $.command.run(comando('sofia-modo', 'meio-ligada'))
    expect(m.modoGravado()).toBe('desligada')
    expect(r.text).toContain('so-quando-chamada')
  })

  test('sofia-modo sem valor diz o modo de agora', async ($, on) => {
    mundo(on, SO_QUANDO)
    const r = await $.command.run(comando('sofia-modo', ''))
    expect(r.text).toContain('so-quando-chamada')
  })

  test('sofia-ensinar pede o tutorial ao modelo', async ($, on) => {
    mundo(on, DESLIGADA)
    const r = await $.command.run(comando('sofia-ensinar', ''))
    expect((r.context ?? []).some((c) => c.includes('primeiro-uso.md'))).toBe(true)
    // O comando só põe a linha: o tutorial aparece na próxima resposta, não agora.
    expect(r.text).toBe('Diga qualquer coisa e a Sofia mostra como funciona.')
  })

  test('session.start registra os quatro comandos', async ($, on) => {
    const { comandos: nomes } = mundo(on)
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true } as never)
    for (const n of ['sofia-painel', 'sofia-ligar', 'sofia-desligar', 'sofia-modo', 'sofia-ensinar']) {
      expect(nomes).toContain(n)
    }
  })
})

describe('painel', () => {
  const QUADRO_NO_PLUGIN = 'mcp__plugin_sofia-estrategista_sofia-estrategista__planejamento_quadro'
  const QUADRO_NO_SITE = 'mcp__claude_ai_Sofia_Estrategista__planejamento_quadro'
  const CRIAR_CARD = 'mcp__plugin_sofia-estrategista_sofia-estrategista__planejamento_criar_card'
  const TEXTO_DO_QUADRO = [
    '## Quadro do perfil p1',
    '### Brainstorming (2)',
    '### Estruturar (0)',
    '### Gravar (1)',
    '- `p1`: Bento (@mechamedebento, Instagram)',
  ].join('\n')

  test('desligada: mostra Sofia desligada, com o uso do Claude, e nunca chama o MCP', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true } as never)
    await $.command.run(comando('sofia-painel', ''))
    await m.relogio.settle()
    expect(m.chamadasAoMcp()).toBe(0)
    for (const surface of ['terminal', 'desktop'] as const) {
      const ui = await $.ui.mount({ ...PAINEL, surface })
      expect((await ui.find({ type: 'Text', text: /Sofia desligada/ }))?.text).toContain('Sofia desligada')
      expect(await ui.find({ type: 'Text', text: /Uso do Claude/ })).toBeTruthy()
      expect(await ui.find({ type: 'Text', text: /quando a Sofia ler/ })).toBeFalsy()
      await ui.unmount()
    }
  })

  test('ligada, sem leitura ainda: a linha curta, e o mod não liga nem chama o conector', async ($, on) => {
    const m = mundo(on)
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true } as never)
    await $.command.run(comando('sofia-painel', ''))
    await m.relogio.settle()
    expect(m.chamadasAoMcp()).toBe(0)
    const ui = await $.ui.mount({ ...PAINEL, surface: 'terminal' })
    expect((await ui.find({ type: 'Text', text: /quando a Sofia ler/ }))?.text).toBe(
      'Os cards aparecem aqui quando a Sofia ler o seu planejamento.',
    )
    await ui.unmount()
  })

  test('a chamada da Sofia a planejamento_quadro enche o painel, e o resultado volta igual', async ($, on) => {
    const m = mundo(on)
    const resposta = { result: { content: [{ type: 'text', text: TEXTO_DO_QUADRO }] }, text: TEXTO_DO_QUADRO }
    m.respostas.set(QUADRO_NO_PLUGIN, resposta)
    const r = await $.tool.call({ tool: QUADRO_NO_PLUGIN } as never)
    expect(r.deny).toBeUndefined()
    expect(r.text).toBe(TEXTO_DO_QUADRO)
    expect(r.result).toEqual(resposta.result)
    expect(m.execucoes()).toBe(1)
    expect(m.chamadasAoMcp()).toBe(0)
    const ui = await $.ui.mount({ ...PAINEL, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /@mechamedebento · Instagram/ })).toBeTruthy()
    expect(await ui.find({ type: 'Text', text: /3 cards no quadro/ })).toBeTruthy()
    expect(await ui.find({ type: 'Text', text: /quando a Sofia ler/ })).toBeFalsy()
    await ui.unmount()
  })

  test('o conector ligado pelo site também conta, e os dados estruturados valem mais que o texto', async ($, on) => {
    const m = mundo(on)
    const estruturado = {
      perfilId: 'p1',
      perfis: [{ id: 'p1', arroba: 'outro', rede: 'TikTok' }],
      colunas: [
        { rotulo: 'Brainstorming', cards: [{}, {}, {}, {}] },
        { rotulo: 'Gravar', cards: [] },
      ],
    }
    m.respostas.set(QUADRO_NO_SITE, { result: { content: [], structuredContent: estruturado }, text: TEXTO_DO_QUADRO })
    await $.tool.call({ tool: QUADRO_NO_SITE } as never)
    const ui = await $.ui.mount({ ...PAINEL, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /@outro · TikTok/ })).toBeTruthy()
    expect(await ui.find({ type: 'Text', text: /4 cards no quadro/ })).toBeTruthy()
    await ui.unmount()
  })

  test('erro do conector sem leitura antes: o motivo aparece; com leitura antes, o quadro fica', async ($, on) => {
    const m = mundo(on)
    m.respostas.set(QUADRO_NO_PLUGIN, { result: { content: [] }, text: 'Faça login no conector.', isError: true })
    const r = await $.tool.call({ tool: QUADRO_NO_PLUGIN } as never)
    expect(r.isError).toBe(true)
    let ui = await $.ui.mount({ ...PAINEL, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /Faça login no conector/ })).toBeTruthy()
    await ui.unmount()

    m.respostas.set(QUADRO_NO_PLUGIN, { result: {}, text: TEXTO_DO_QUADRO })
    await $.tool.call({ tool: QUADRO_NO_PLUGIN } as never)
    m.respostas.set(QUADRO_NO_PLUGIN, { result: {}, text: 'O site não respondeu.', isError: true })
    await $.tool.call({ tool: QUADRO_NO_PLUGIN } as never)
    ui = await $.ui.mount({ ...PAINEL, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /3 cards no quadro/ })).toBeTruthy()
    expect(await ui.find({ type: 'Text', text: /O site não respondeu/ })).toBeFalsy()
    await ui.unmount()
  })

  test('uma ferramenta que grava no planejamento marca o quadro como mudado; uma de leitura não', async ($, on) => {
    const m = mundo(on)
    m.respostas.set(QUADRO_NO_PLUGIN, { result: {}, text: TEXTO_DO_QUADRO })
    await $.tool.call({ tool: QUADRO_NO_PLUGIN } as never)
    m.respostas.set('mcp__plugin_sofia-estrategista_sofia-estrategista__planejamento_gravar', {
      result: {},
      text: 'roteiro',
      isReadOnly: true,
    })
    await $.tool.call({ tool: 'mcp__plugin_sofia-estrategista_sofia-estrategista__planejamento_gravar' } as never)
    let ui = await $.ui.mount({ ...PAINEL, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /mudou depois desta leitura/ })).toBeFalsy()
    await ui.unmount()

    m.respostas.set(CRIAR_CARD, { result: {}, text: 'Card criado.' })
    const r = await $.tool.call({ tool: CRIAR_CARD } as never)
    expect(r.text).toBe('Card criado.')
    ui = await $.ui.mount({ ...PAINEL, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /mudou depois desta leitura/ })).toBeTruthy()
    await ui.unmount()

    // A leitura seguinte tira o aviso.
    await $.tool.call({ tool: QUADRO_NO_PLUGIN } as never)
    ui = await $.ui.mount({ ...PAINEL, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /mudou depois desta leitura/ })).toBeFalsy()
    await ui.unmount()
  })

  test('desligada, a chamada ao conector é negada e o painel não aprende nada com ela', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    m.respostas.set(QUADRO_NO_PLUGIN, { result: {}, text: TEXTO_DO_QUADRO })
    const r = await $.tool.call({ tool: QUADRO_NO_PLUGIN } as never)
    expect(r.deny).toBe(AVISO_DESLIGADA)
    expect(m.execucoes()).toBe(0)
    await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:ligar' } as never)
    await $.prompt.submit(digitado('liga a Sofia'))
    const ui = await $.ui.mount({ ...PAINEL, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /cards no quadro/ })).toBeFalsy()
    expect(await ui.find({ type: 'Text', text: /quando a Sofia ler/ })).toBeTruthy()
    await ui.unmount()
  })
})

describe('o modelo só troca o modo quando a pessoa pediu', () => {
  const LIGAR = { tool: 'Skill', skill: 'sofia-estrategista:ligar' } as never
  const DESLIGAR = { tool: 'Skill', skill: 'sofia-estrategista:desligar' } as never

  test('so-quando-chamada, sem chamado na sessão: a skill de ligar é negada e o modo não muda', async ($, on) => {
    const m = mundo(on, SO_QUANDO)
    const r = await $.tool.call(LIGAR)
    expect(r.deny).toContain(NAO_TROQUEI)
    expect(r.deny).toContain('/sofia-estrategista:')
    expect(m.modoGravado()).toBe('so-quando-chamada')
    await $.prompt.submit(digitado('faz um resumo do arquivo'))
    const r2 = await $.tool.call(LIGAR)
    expect(r2.deny).toContain(NAO_TROQUEI)
    expect(m.modoGravado()).toBe('so-quando-chamada')
  })

  test('sem pasta de dados, a skill de desligar é negada: a troca não foi gravada', async ($, on) => {
    on('process.hookEnv', () => ({ value: {} }))
    on('session.id', () => ({ value: 'sessao-1' }))
    on('tool.call', () => ({ result: {} }) as never)
    on('prompt.submit', (_, e) => ({ text: e.text, context: e.context }) as never)
    await $.prompt.submit(digitado('Sofia, para de aparecer'))
    const r = await $.tool.call(DESLIGAR)
    expect(r.deny).toContain(NAO_TROQUEI)
  })

  test('a skill de modo igual ao de agora passa', async ($, on) => {
    mundo(on, SO_QUANDO)
    const r = await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:modo', args: 'so-quando-chamada' } as never)
    expect(r.deny).toBeUndefined()
  })

  test('desligada, a pessoa responde "sim" à oferta: o gancho liga e pede a confirmação', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    const p = await $.prompt.submit(digitado('Sofia, faz o roteiro'))
    expect((p.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(true)
    const s = await $.prompt.submit(digitado('sim'))
    expect(m.modoGravado()).toBe('ligada')
    expect(s.context).toContain(DISSE_SIM)
    expect(s.context).toContain('Interruptor local: ligada.')
    expect(s.context).not.toContain(AVISO_DESLIGADA)
    expect((await $.tool.call(LIGAR)).deny).toBeUndefined()
  })

  test('desligada, "Sofia, sim" à oferta também liga', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.prompt.submit(digitado('Sofia, faz o roteiro'))
    const s = await $.prompt.submit(digitado('Sofia, sim'))
    expect(m.modoGravado()).toBe('ligada')
    expect(s.context).toContain(DISSE_SIM)
  })

  test('desligada, "não" à oferta: não liga e não repete a oferta', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.prompt.submit(digitado('Sofia, faz o roteiro'))
    const n = await $.prompt.submit(digitado('não'))
    expect(m.modoGravado()).toBe('desligada')
    expect((n.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(false)
    expect(n.context).not.toContain(DISSE_SIM)
    const n2 = await $.prompt.submit(digitado('não, Sofia'))
    expect((n2.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(true)
  })

  test('desligada, "não, Sofia" logo depois da oferta não repete a oferta', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.prompt.submit(digitado('Sofia, faz o roteiro'))
    const n = await $.prompt.submit(digitado('não, Sofia'))
    expect(m.modoGravado()).toBe('desligada')
    expect((n.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(false)
  })

  test('o "sim" sem oferta antes não liga', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.prompt.submit(digitado('Sofia, faz o roteiro'))
    await $.prompt.submit(digitado('e o tempo amanhã?'))
    const s = await $.prompt.submit(digitado('sim'))
    expect(m.modoGravado()).toBe('desligada')
    expect(s.context).not.toContain(DISSE_SIM)
  })

  test('a oferta de ligar vale só para a resposta seguinte', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.prompt.submit(digitado('Sofia, faz o roteiro'))
    await $.prompt.submit(digitado('e o tempo amanhã?'))
    await $.prompt.submit(digitado('outra coisa'))
    await $.tool.call(LIGAR)
    expect(m.modoGravado()).toBe('desligada')
  })

  test('desligada, "Sofia, volta a funcionar": só oferece; o modelo liga depois do "sim"', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    const p = await $.prompt.submit(digitado('Sofia, volta a funcionar'))
    expect((p.context ?? []).some((c) => c.includes(ESTOU_DESLIGADA))).toBe(true)
    await $.tool.call(LIGAR)
    expect(m.modoGravado()).toBe('desligada')
    await $.prompt.submit(digitado('sim'))
    await $.tool.call(LIGAR)
    expect(m.modoGravado()).toBe('ligada')
  })

  test('desligada, "Sofia, faz o roteiro": o modelo não liga no mesmo prompt', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.prompt.submit(digitado('Sofia, faz o roteiro'))
    await $.tool.call(LIGAR)
    expect(m.modoGravado()).toBe('desligada')
  })

  test('so-quando-chamada, chamada pelo nome: o modelo pode ligar no mesmo prompt', async ($, on) => {
    const m = mundo(on, SO_QUANDO)
    await $.prompt.submit(digitado('Sofia, fica sempre ligada'))
    await $.tool.call(LIGAR)
    expect(m.modoGravado()).toBe('ligada')
  })

  test('"Sofia, para de aparecer": o modelo desliga pela skill', async ($, on) => {
    const m = mundo(on)
    await $.prompt.submit(digitado('Sofia, para de aparecer'))
    // O chamado grava apresentada (primeiro uso), mas o modo segue ligada até a skill.
    expect(m.modoGravado() ?? 'ligada').toBe('ligada')
    await $.tool.call(DESLIGAR)
    expect(m.modoGravado()).toBe('desligada')
  })
})

describe('a ferramenta roda uma vez só', () => {
  test('quando a ferramenta lança erro, ela não roda de novo', async ($, on) => {
    const m = mundo(on)
    m.ferramenta.falha = true
    await $.tool.call({ tool: 'Bash', command: 'rm arquivo' } as never).catch(() => undefined)
    expect(m.execucoes()).toBe(1)
  })

  test('com a Sofia desligada e a ferramenta lançando erro, também roda uma vez', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    m.ferramenta.falha = true
    await $.tool.call({ tool: 'Bash', command: 'rm arquivo' } as never).catch(() => undefined)
    expect(m.execucoes()).toBe(1)
  })

  test('a ferramenta negada não roda', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:roteiro' } as never)
    expect(m.execucoes()).toBe(0)
  })
})

describe('primeiro uso neste computador', () => {
  const PRIMEIRO_USO =
    'Primeiro uso da Sofia neste lugar: só se você agir como Sofia nesta resposta, abra com o tutorial de primeiro-uso.md; senão, ignore esta linha.'
  const LIGADA_APRESENTADA = JSON.stringify({ modo: 'ligada', apresentada: true, mudouEm: '2026-11-20T10:00:00.000Z' })
  const SO_QUANDO_NOVA = JSON.stringify({ modo: 'so-quando-chamada', apresentada: false })
  const temPrimeiroUso = (p: { context?: readonly string[] }) => (p.context ?? []).includes(PRIMEIRO_USO)
  const apresentada = (m: Mundo) => JSON.parse(m.arquivos.get(ARQUIVO) ?? '{}').apresentada

  const SKILL = { tool: 'Skill', skill: 'sofia-estrategista' } as never
  const CONECTOR = { tool: 'mcp__plugin_sofia-estrategista_sofia-estrategista__planejamento_quadro' } as never

  test('ligada: a linha vem no primeiro prompt da sessão e quando a Sofia é chamada, até a primeira skill passar', async ($, on) => {
    const m = mundo(on)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('escreve um roteiro sobre pão')))).toBe(true)
    expect(m.arquivos.has(ARQUIVO)).toBe(false)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('faz um resumo do arquivo')))).toBe(false)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('Sofia, me ajuda com isso')))).toBe(true)
    m.sessao.id = 'sessao-3'
    expect(temPrimeiroUso(await $.prompt.submit(digitado('outra sessão, outro assunto')))).toBe(true)
    m.sessao.id = 'sessao-1'
    expect((await $.tool.call(SKILL)).deny).toBeUndefined()
    expect(apresentada(m)).toBe(true)
    expect(m.modoGravado()).toBe('ligada')
    expect(temPrimeiroUso(await $.prompt.submit(digitado('Sofia, outra ideia')))).toBe(false)
    m.sessao.id = 'sessao-2'
    expect(temPrimeiroUso(await $.prompt.submit(digitado('Sofia, mais uma')))).toBe(false)
  })

  test('a ferramenta do conector também marca; ligar e ferramenta de fora não marcam', async ($, on) => {
    const m = mundo(on)
    await $.prompt.submit(digitado('escreve um roteiro sobre pão'))
    await $.tool.call({ tool: 'Bash', command: 'ls' } as never)
    await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:ligar' } as never)
    expect(m.arquivos.has(ARQUIVO)).toBe(false)
    await $.tool.call(CONECTOR)
    expect(apresentada(m)).toBe(true)
  })

  test('sem pasta de dados, nunca a linha do primeiro uso', async ($, on) => {
    on('process.hookEnv', () => ({ value: {} }))
    on('session.id', () => ({ value: 'sessao-1' }))
    on('prompt.submit', (_, e) => ({ text: e.text, context: e.context }) as never)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('escreve um roteiro sobre pão')))).toBe(false)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('Sofia, me dá uma ideia')))).toBe(false)
  })

  test('com apresentada no arquivo, sem linha', async ($, on) => {
    mundo(on, LIGADA_APRESENTADA)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('Sofia, me dá uma ideia')))).toBe(false)
  })

  test('desligada: sem linha, e a ferramenta negada não marca', async ($, on) => {
    const m = mundo(on, JSON.stringify({ modo: 'desligada', apresentada: false }))
    expect(temPrimeiroUso(await $.prompt.submit(digitado('escreve um roteiro sobre pão')))).toBe(false)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('Sofia, faz o roteiro')))).toBe(false)
    expect((await $.tool.call(SKILL)).deny).toBe(AVISO_DESLIGADA)
    expect(apresentada(m)).toBe(false)
  })

  test('só quando chamada: sem linha até o chamado, com linha depois', async ($, on) => {
    mundo(on, SO_QUANDO_NOVA)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('escreve um roteiro sobre pão')))).toBe(false)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('Sofia, me dá uma ideia')))).toBe(true)
  })

  test('pedido de modo não leva a linha', async ($, on) => {
    mundo(on)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('Sofia, desliga')))).toBe(false)
  })

  test('depois da primeira skill, "só quando eu chamar" muda para so-quando-chamada', async ($, on) => {
    const m = mundo(on)
    await $.prompt.submit(digitado('escreve um roteiro sobre pão'))
    await $.tool.call(SKILL)
    const p = await $.prompt.submit(digitado('só quando eu te chamar pelo nome'))
    expect(m.modoGravado()).toBe('so-quando-chamada')
    expect(p.context).toContain('Interruptor local: so-quando-chamada.')
    expect(apresentada(m)).toBe(true)
  })

  test('depois da primeira skill, "sempre ligada" muda para ligada', async ($, on) => {
    const m = mundo(on, SO_QUANDO_NOVA)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('Sofia, me dá uma ideia')))).toBe(true)
    await $.tool.call(SKILL)
    const p = await $.prompt.submit(digitado('sempre ligada'))
    expect(m.modoGravado()).toBe('ligada')
    expect(p.context).toContain('Interruptor local: ligada.')
  })

  test('na janela, a skill de modo também troca (resposta com outras palavras)', async ($, on) => {
    const m = mundo(on)
    await $.prompt.submit(digitado('escreve um roteiro sobre pão'))
    await $.tool.call(SKILL)
    await $.prompt.submit(digitado('acho melhor você aparecer só quando eu pedir'))
    expect(m.modoGravado()).toBe('ligada')
    await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:modo', args: 'so-quando-chamada' } as never)
    expect(m.modoGravado()).toBe('so-quando-chamada')
  })

  test('sem a skill antes, "só quando eu chamar" não muda nada', async ($, on) => {
    const m = mundo(on)
    await $.prompt.submit(digitado('escreve um roteiro sobre pão'))
    await $.prompt.submit(digitado('só quando eu chamar'))
    expect(m.modoGravado() ?? 'ligada').toBe('ligada')
  })

  test('a janela da resposta dura um prompt só', async ($, on) => {
    const m = mundo(on)
    await $.prompt.submit(digitado('Sofia, me dá uma ideia'))
    await $.tool.call(SKILL)
    await $.prompt.submit(digitado('faz a segunda'))
    await $.prompt.submit(digitado('só quando eu chamar'))
    expect(m.modoGravado()).toBe('ligada')
  })

  test('"Sofia, me ensina" com a Sofia ativa marca apresentada e abre a janela', async ($, on) => {
    const m = mundo(on)
    expect(temPrimeiroUso(await $.prompt.submit(digitado('Sofia, me ensina')))).toBe(false)
    expect(apresentada(m)).toBe(true)
    await $.prompt.submit(digitado('só quando eu chamar'))
    expect(m.modoGravado()).toBe('so-quando-chamada')
  })

  test('"Sofia, me ensina" desligada não abre a janela nem marca', async ($, on) => {
    const m = mundo(on, JSON.stringify({ modo: 'desligada', apresentada: false }))
    await $.prompt.submit(digitado('Sofia, me ensina'))
    await $.prompt.submit(digitado('só quando eu chamar'))
    expect(m.modoGravado()).toBe('desligada')
    expect(apresentada(m)).toBe(false)
  })

  test('o comando /sofia-ensinar que também chega como prompt abre a janela', async ($, on) => {
    const m = mundo(on)
    await $.prompt.submit(digitado('/sofia-ensinar'))
    expect(apresentada(m)).toBe(true)
    await $.prompt.submit(digitado('só quando eu chamar'))
    expect(m.modoGravado()).toBe('so-quando-chamada')
  })

  test('o comando sofia-ensinar com a Sofia ativa marca apresentada e abre a janela', async ($, on) => {
    const m = mundo(on)
    await $.command.run(comando('sofia-ensinar', ''))
    expect(apresentada(m)).toBe(true)
    await $.prompt.submit(digitado('só quando eu chamar'))
    expect(m.modoGravado()).toBe('so-quando-chamada')
  })
})
