import { describe, expect, mock, test } from 'claude-code/testing'
import type { CommandRunInput, On, PromptOrigin, PromptSubmitInput } from 'claude-code'

import { AVISO_DESLIGADA, AVISO_SO_QUANDO_CHAMADA } from './interruptor'

// O mod do painel com o interruptor. Cada hook do teste faz o papel do engine: a pasta de dados, o id da
// sessão, os arquivos (em memória), o conector e a ferramenta que roda de fato.

const PASTA = '/dados/sofia-estrategista'
const ARQUIVO = `${PASTA}/estado.json`
const ESTOU_DESLIGADA = 'Estou desligada aqui. Quer que eu ligue?'

type Mundo = {
  arquivos: Map<string, string>
  sessao: { id: string }
  chamadasAoQuadro: () => number
  conexoes: () => number
  comandos: string[]
  relogio: { settle: () => Promise<void> }
  modoGravado: () => string | undefined
}

/** Monta o engine de mentira. `estado` é o texto de estado.json (undefined: o arquivo não existe). */
function mundo(on: On, estado?: string): Mundo {
  const arquivos = new Map<string, string>()
  if (estado !== undefined) arquivos.set(ARQUIVO, estado)
  const sessao = { id: 'sessao-1' }
  let quadro = 0
  let conexoes = 0
  const comandos: string[] = []

  on('process.hookEnv', () => ({ value: { CLAUDE_PLUGIN_DATA: PASTA } }))
  on('session.id', () => ({ value: sessao.id }))
  on('fs.read', (_, e) => (arquivos.has(e.path) ? { value: arquivos.get(e.path) as string } : { deny: `ENOENT: ${e.path}` }))
  on('fs.write', (_, e) => {
    arquivos.set(e.path, e.text)
    return { value: undefined }
  })
  on('fs.exists', (_, e) => ({ value: arquivos.has(e.path) }))
  on('tool.call', () => ({ result: {} }) as never)
  on('mcp.connect', () => {
    conexoes++
    return { value: { server: 'sofia-estrategista', isConnected: true } } as never
  })
  on('mcp.call', () => {
    quadro++
    return { value: { content: [{ type: 'text', text: '### Brainstorming (2)' }] } } as never
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
    chamadasAoQuadro: () => quadro,
    conexoes: () => conexoes,
    comandos,
    relogio,
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
  plugin: 'sofia-estrategista',
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
    const doPlugin = await $.tool.call({ tool: 'Skill', skill: 'sofia-estrategista:ligar' } as never)
    expect(doPlugin.deny).toBeUndefined()
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
  test('desligada: não lê o quadro e mostra Sofia desligada, com o uso do Claude', async ($, on) => {
    const m = mundo(on, DESLIGADA)
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true } as never)
    await $.command.run(comando('sofia-painel', ''))
    await m.relogio.settle()
    expect(m.chamadasAoQuadro()).toBe(0)
    expect(m.conexoes()).toBe(0)
    for (const surface of ['terminal', 'desktop'] as const) {
      const ui = await $.ui.mount({ ...PAINEL, surface })
      expect((await ui.find({ type: 'Text', text: /Sofia desligada/ }))?.text).toContain('Sofia desligada')
      expect(await ui.find({ type: 'Text', text: /Uso do Claude/ })).toBeTruthy()
      await ui.unmount()
    }
  })

  test('ligada: lê o quadro', async ($, on) => {
    const m = mundo(on)
    await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true } as never)
    await $.command.run(comando('sofia-painel', ''))
    await m.relogio.settle()
    expect(m.chamadasAoQuadro()).toBeGreaterThan(0)
  })
})
