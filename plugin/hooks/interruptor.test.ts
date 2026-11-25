import { describe, expect, test } from 'claude-code/testing'

import {
  AVISO_DESLIGADA,
  AVISO_SO_QUANDO_CHAMADA,
  NOMES_DA_SOFIA,
  chamaSofia,
  decidir,
  ehDaSofia,
  ehLivre,
  lerEstado,
  pedidoDeModo,
} from './interruptor'
import type { Estado } from './interruptor'

// Só funções: nenhum evento, nenhum arquivo. A conferência da lista de nomes contra as pastas do plugin
// precisa ler disco, e este executor não deixa; ela mora em interruptor.pastas.check.mjs.

const PADRAO: Estado = { modo: 'ligada', apresentada: false }

describe('chamaSofia', () => {
  test('vale para o nome dito como palavra inteira', () => {
    expect(chamaSofia('Sofia, faz o roteiro')).toBe(true)
    expect(chamaSofia('oi SOFIA')).toBe(true)
    expect(chamaSofia('sofía?')).toBe(true)
    expect(chamaSofia('faz isso, Sofia.')).toBe(true)
  })

  test('vale para o comando digitado do plugin', () => {
    expect(chamaSofia('/sofia-estrategista:roteiro card 3')).toBe(true)
    expect(chamaSofia('  /sofia-estrategista:ideias')).toBe(true)
  })

  test('não vale dentro de outra palavra', () => {
    expect(chamaSofia('filosofia do vídeo')).toBe(false)
    expect(chamaSofia('Sofiane mandou')).toBe(false)
    expect(chamaSofia('sofisticado')).toBe(false)
  })

  test('não vale sem o nome, nem com texto vazio', () => {
    expect(chamaSofia('faz o roteiro do vídeo')).toBe(false)
    expect(chamaSofia('')).toBe(false)
    expect(chamaSofia('/outro-plugin:roteiro')).toBe(false)
  })
})

describe('pedidoDeModo', () => {
  test('desligar', () => {
    expect(pedidoDeModo('Sofia, desliga')).toBe('desligada')
    expect(pedidoDeModo('desliga a Sofia')).toBe('desligada')
    expect(pedidoDeModo('desligar a sofia')).toBe('desligada')
  })

  test('ligar', () => {
    expect(pedidoDeModo('liga a Sofia')).toBe('ligada')
    expect(pedidoDeModo('Sofia, liga')).toBe('ligada')
    expect(pedidoDeModo('ligar a sofia')).toBe('ligada')
  })

  test('só quando chamada', () => {
    expect(pedidoDeModo('Sofia, só quando eu te chamar')).toBe('so-quando-chamada')
    expect(pedidoDeModo('só quando eu chamar a Sofia')).toBe('so-quando-chamada')
  })

  test('ensinar', () => {
    expect(pedidoDeModo('Sofia, me ensina')).toBe('ensinar')
    expect(pedidoDeModo('me ensina a usar a Sofia')).toBe('ensinar')
  })

  test('o que não é pedido de modo vira null', () => {
    expect(pedidoDeModo('desliga o microfone')).toBe(null)
    expect(pedidoDeModo('liga pra mim amanhã')).toBe(null)
    expect(pedidoDeModo('a Sofia desligou o vídeo?')).toBe(null)
    expect(pedidoDeModo('o que acontece se eu desligar a Sofia?')).toBe(null)
    expect(pedidoDeModo('Sofia, faz o roteiro')).toBe(null)
    expect(pedidoDeModo('')).toBe(null)
  })
})

describe('lerEstado', () => {
  test('o que falta ou não abre vale ligada, sem derrubar', () => {
    expect(lerEstado(null)).toEqual(PADRAO)
    expect(lerEstado('')).toEqual(PADRAO)
    expect(lerEstado('{')).toEqual(PADRAO)
    expect(lerEstado('{"modo":"x"}')).toEqual(PADRAO)
    expect(lerEstado('null')).toEqual(PADRAO)
    expect(lerEstado('[]')).toEqual(PADRAO)
  })

  test('o que está certo passa como veio', () => {
    expect(lerEstado('{"modo":"desligada","apresentada":true}')).toEqual({ modo: 'desligada', apresentada: true })
    expect(lerEstado('{"modo":"so-quando-chamada","apresentada":false,"mudouEm":"2026-11-25T10:00:00.000Z"}')).toEqual({
      modo: 'so-quando-chamada',
      apresentada: false,
      mudouEm: '2026-11-25T10:00:00.000Z',
    })
  })

  test('modo certo sem "apresentada" vale não apresentada', () => {
    expect(lerEstado('{"modo":"desligada"}')).toEqual({ modo: 'desligada', apresentada: false })
  })
})

describe('ehDaSofia', () => {
  test('Skill com o prefixo do plugin', () => {
    expect(ehDaSofia('Skill', { skill: 'sofia-estrategista:roteiro' })).toBe(true)
    expect(ehDaSofia('Skill', { skill: 'sofia-estrategista:sofia-estrategista' })).toBe(true)
  })

  test('Skill com o nome sem prefixo de skill ou comando do plugin', () => {
    expect(ehDaSofia('Skill', { skill: 'sofia-estrategista' })).toBe(true)
    expect(ehDaSofia('Skill', { skill: 'sofia-editora' })).toBe(true)
    expect(ehDaSofia('Skill', { skill: 'beditor' })).toBe(true)
    expect(ehDaSofia('Skill', { skill: 'roteiro' })).toBe(true)
  })

  test('Skill de outro plugin ou desconhecida não é da Sofia', () => {
    expect(ehDaSofia('Skill', { skill: 'outro-plugin:roteiro' })).toBe(false)
    expect(ehDaSofia('Skill', { skill: 'superpowers:brainstorming' })).toBe(false)
    expect(ehDaSofia('Skill', { skill: 'nao-existe' })).toBe(false)
    expect(ehDaSofia('Skill', {})).toBe(false)
    expect(ehDaSofia('Skill', null)).toBe(false)
  })

  test('Agent com subagent_type do plugin', () => {
    expect(ehDaSofia('Agent', { subagent_type: 'sofia-estrategista:roteirista' })).toBe(true)
    expect(ehDaSofia('Agent', { subagent_type: 'general-purpose' })).toBe(false)
    expect(ehDaSofia('Agent', {})).toBe(false)
  })

  test('ferramentas do conector, do plugin e do site', () => {
    expect(ehDaSofia('mcp__plugin_sofia-estrategista_sofia-estrategista__sofia_perfil', {})).toBe(true)
    expect(ehDaSofia('mcp__claude_ai_Sofia_Estrategista__planejamento_criar_card', {})).toBe(true)
  })

  test('ferramenta de fora não é da Sofia', () => {
    expect(ehDaSofia('Bash', { command: 'ls' })).toBe(false)
    expect(ehDaSofia('mcp__outro__x', {})).toBe(false)
    expect(ehDaSofia('mcp__claude_ai_Sofia_Interna__x', {})).toBe(false)
  })

  test('aceita a entrada embrulhada em tool_input, como no gancho de comando', () => {
    expect(ehDaSofia('Skill', { tool_input: { skill: 'sofia-estrategista:roteiro' } })).toBe(true)
  })
})

describe('NOMES_DA_SOFIA', () => {
  test('traz as skills, os comandos de hoje e os quatro do interruptor', () => {
    for (const nome of ['sofia-estrategista', 'sofia-editora', 'beditor', 'motion-vox', 'roteiro', 'ideias', 'painel']) {
      expect(NOMES_DA_SOFIA.includes(nome)).toBe(true)
    }
    for (const nome of ['ligar', 'desligar', 'modo', 'ensinar']) {
      expect(NOMES_DA_SOFIA.includes(nome)).toBe(true)
    }
  })
})

describe('ehLivre', () => {
  test('os quatro comandos do plugin, com e sem prefixo', () => {
    for (const nome of ['ligar', 'desligar', 'modo', 'ensinar']) {
      expect(ehLivre('Skill', { skill: nome })).toBe(true)
      expect(ehLivre('Skill', { skill: `sofia-estrategista:${nome}` })).toBe(true)
    }
  })

  test('os comandos do mod', () => {
    for (const nome of ['sofia-ligar', 'sofia-desligar', 'sofia-modo', 'sofia-ensinar']) {
      expect(ehLivre('Skill', { skill: nome })).toBe(true)
    }
  })

  test('o resto da Sofia não é livre', () => {
    expect(ehLivre('Skill', { skill: 'sofia-estrategista:roteiro' })).toBe(false)
    expect(ehLivre('Skill', { skill: 'outro-plugin:ligar' })).toBe(false)
    expect(ehLivre('Agent', { subagent_type: 'sofia-estrategista:roteirista' })).toBe(false)
    expect(ehLivre('Bash', {})).toBe(false)
  })
})

describe('decidir', () => {
  const skill = { skill: 'sofia-estrategista:roteiro' }
  const agente = { subagent_type: 'sofia-estrategista:roteirista' }
  const conector = 'mcp__claude_ai_Sofia_Estrategista__sofia_perfil'

  test('ligada libera tudo', () => {
    const estado: Estado = { modo: 'ligada', apresentada: true }
    expect(decidir(estado, false, 'Skill', skill)).toEqual({})
    expect(decidir(estado, false, 'Agent', agente)).toEqual({})
    expect(decidir(estado, false, conector, {})).toEqual({})
    expect(decidir(estado, false, 'Bash', {})).toEqual({})
  })

  test('desligada nega o que é da Sofia, com a linha para o modelo', () => {
    const estado: Estado = { modo: 'desligada', apresentada: true }
    const linha = 'A Sofia está desligada neste lugar. Responda sem ela. Para ligar, a pessoa diz "liga a Sofia".'
    expect(AVISO_DESLIGADA).toBe(linha)
    expect(decidir(estado, false, 'Skill', skill)).toEqual({ negar: linha })
    expect(decidir(estado, true, 'Agent', agente)).toEqual({ negar: linha })
    expect(decidir(estado, true, conector, {})).toEqual({ negar: linha })
  })

  test('desligada libera ligar, desligar, modo, ensinar e as ferramentas de fora', () => {
    const estado: Estado = { modo: 'desligada', apresentada: true }
    expect(decidir(estado, false, 'Skill', { skill: 'sofia-estrategista:ligar' })).toEqual({})
    expect(decidir(estado, false, 'Skill', { skill: 'desligar' })).toEqual({})
    expect(decidir(estado, false, 'Skill', { skill: 'sofia-estrategista:modo' })).toEqual({})
    expect(decidir(estado, false, 'Skill', { skill: 'sofia-ensinar' })).toEqual({})
    expect(decidir(estado, false, 'Bash', { command: 'ls' })).toEqual({})
    expect(decidir(estado, false, 'mcp__outro__x', {})).toEqual({})
    expect(decidir(estado, false, 'Skill', { skill: 'superpowers:brainstorming' })).toEqual({})
  })

  test('só quando chamada: nega sem chamado, com a linha para o modelo', () => {
    const estado: Estado = { modo: 'so-quando-chamada', apresentada: true }
    const linha = 'A Sofia só age quando a pessoa a chama pelo nome. Ela não foi chamada nesta conversa: responda sem ela.'
    expect(AVISO_SO_QUANDO_CHAMADA).toBe(linha)
    expect(decidir(estado, false, 'Skill', skill)).toEqual({ negar: linha })
    expect(decidir(estado, false, 'Agent', agente)).toEqual({ negar: linha })
    expect(decidir(estado, false, conector, {})).toEqual({ negar: linha })
  })

  test('só quando chamada: libera com chamado, e sempre o que não é da Sofia e os quatro comandos', () => {
    const estado: Estado = { modo: 'so-quando-chamada', apresentada: true }
    expect(decidir(estado, true, 'Skill', skill)).toEqual({})
    expect(decidir(estado, true, conector, {})).toEqual({})
    expect(decidir(estado, false, 'Bash', {})).toEqual({})
    expect(decidir(estado, false, 'Skill', { skill: 'sofia-estrategista:ligar' })).toEqual({})
    expect(decidir(estado, false, 'Skill', { skill: 'modo' })).toEqual({})
  })

  test('entrada estranha não derruba', () => {
    const estado: Estado = { modo: 'desligada', apresentada: false }
    expect(decidir(estado, false, 'Skill', undefined)).toEqual({})
    expect(decidir(estado, false, 'Skill', 'texto')).toEqual({})
    expect(decidir(estado, false, 'Skill', { skill: 42 })).toEqual({})
  })
})
