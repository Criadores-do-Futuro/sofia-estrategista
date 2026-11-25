// Confere NOMES_DA_SOFIA contra as pastas do plugin. Precisa ler disco, e `claude plugin test` não deixa
// um teste importar "node:fs"; por isso esta conferência roda à parte, com o executor do Node:
//   node --test plugin/hooks/interruptor.pastas.check.mjs
// A lista pode ter nomes à frente das pastas (os comandos ligar, desligar, modo e ensinar), nunca atrás.
import assert from 'node:assert/strict'
import { readdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

import { NOMES_DA_SOFIA } from './interruptor.ts'

const plugin = join(dirname(fileURLToPath(import.meta.url)), '..')

test('toda pasta de plugin/skills está em NOMES_DA_SOFIA', () => {
  const pastas = readdirSync(join(plugin, 'skills'), { withFileTypes: true })
    .filter((e) => e.isDirectory())
    .map((e) => e.name)
  assert.ok(pastas.length > 0)
  for (const nome of pastas) assert.ok(NOMES_DA_SOFIA.includes(nome), `skill fora da lista: ${nome}`)
})

test('todo plugin/commands/*.md está em NOMES_DA_SOFIA', () => {
  const comandos = readdirSync(join(plugin, 'commands'))
    .filter((n) => n.endsWith('.md'))
    .map((n) => n.slice(0, -3))
  assert.ok(comandos.length > 0)
  for (const nome of comandos) assert.ok(NOMES_DA_SOFIA.includes(nome), `comando fora da lista: ${nome}`)
})
