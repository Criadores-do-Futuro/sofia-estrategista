// A regra do interruptor da Sofia: funções puras, sem evento, sem arquivo e sem relógio.
// Quem lê o estado do disco, escuta o que a pessoa digita e nega a ferramenta usa estas funções (o mod em
// register.tsx e o gancho de comando); aqui só se decide. Nada aqui derruba: na dúvida, a Sofia fica ligada.

export type Modo = 'ligada' | 'so-quando-chamada' | 'desligada'
export type Estado = { modo: Modo; apresentada: boolean; mudouEm?: string }

const MODOS: readonly Modo[] = ['ligada', 'so-quando-chamada', 'desligada']

/** A linha para o modelo quando a Sofia está desligada. */
export const AVISO_DESLIGADA =
  'A Sofia está desligada neste lugar. Responda sem ela. Para ligar, a pessoa diz "liga a Sofia".'

/** A linha para o modelo quando a Sofia só age se for chamada e ninguém a chamou. */
export const AVISO_SO_QUANDO_CHAMADA =
  'A Sofia só age quando a pessoa a chama pelo nome. Ela não foi chamada nesta conversa: responda sem ela.'

const PREFIXO_DO_PLUGIN = 'sofia-estrategista:'
const PREFIXO_DO_CONECTOR_NO_PLUGIN = 'mcp__plugin_sofia-estrategista_sofia-estrategista__'
const PREFIXO_DO_CONECTOR_NO_SITE = 'mcp__claude_ai_Sofia_Estrategista__'

/**
 * Os nomes (sem prefixo) das skills e dos comandos do plugin: as pastas de plugin/skills e os arquivos de
 * plugin/commands. Com o prefixo `sofia-estrategista:` qualquer um deles é da Sofia. Sem o prefixo, só as
 * quatro skills de verdade (NOMES_SEM_PREFIXO): um comando solto como "plano" ou "painel" pode ser de outro
 * plugin. tests/test_interruptor.py confere a lista contra as pastas e roda no
 * `python3 -m unittest discover -s tests`.
 */
export const NOMES_DA_SOFIA: readonly string[] = [
  // skills
  'beditor',
  'motion-vox',
  'sofia-editora',
  'sofia-estrategista',
  // comandos
  'analisar',
  'aprender-edicao',
  'aprender-motion',
  'atualizar',
  'branding',
  'conectar',
  'cortar',
  'critica',
  'dirigir',
  'editar-analise',
  'editar',
  'estilos',
  'finalizar',
  'ideias',
  'montar',
  'motion-graficos',
  'motion',
  'painel',
  'pesquisa',
  'plano',
  'publicar',
  'qa',
  'roteiro',
  'setup',
  // comandos do interruptor
  'ligar',
  'desligar',
  'modo',
  'ensinar',
]

// As skills que valem como da Sofia mesmo chamadas sem o prefixo do plugin.
const NOMES_SEM_PREFIXO: readonly string[] = ['sofia-estrategista', 'sofia-editora', 'beditor', 'motion-vox']

// Os comandos que nunca se negam: o plugin (ligar, desligar, modo, ensinar) e os do mod (sofia-*).
const LIVRES_NO_PLUGIN: readonly string[] = ['ligar', 'desligar', 'modo', 'ensinar']
const LIVRES_NO_MOD: readonly string[] = ['sofia-ligar', 'sofia-desligar', 'sofia-modo', 'sofia-ensinar']

// ---------- texto ----------

/** Minúsculas, sem acento e com espaços simples: "Sofía?" vira "sofia?". */
function normalizar(texto: string): string {
  return texto.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/\s+/g, ' ').trim()
}

// "sofia" só vale como palavra inteira: nada de letra ou número colado antes ou depois.
const PALAVRA_SOFIA = /(?<![\p{L}\p{N}_])sofia(?![\p{L}\p{N}_])/u

/** A pessoa chamou a Sofia pelo nome, ou digitou um comando do plugin. */
export function chamaSofia(prompt: string): boolean {
  if (typeof prompt !== 'string') return false
  const texto = normalizar(prompt)
  return texto.startsWith('/' + PREFIXO_DO_PLUGIN) || PALAVRA_SOFIA.test(texto)
}

// Um pedido de modo é a frase inteira, não uma menção no meio de outra conversa: "desliga a Sofia" muda o
// modo; "o que acontece se eu desligar a Sofia?" e "a Sofia desligou o vídeo?" não. Por isso a frase é
// ancorada no começo e no fim, com só uma saudação e um "por favor" de enfeite.
const ABRE = '^(?:(?:oi|ola|ei|e ai|bom dia|boa tarde|boa noite)[ ,!.]+)?(?:por favor[ ,]+)?(?:pode )?'
const FECHA = '(?:[ ,]*(?:por favor|pf|agora|de novo|de volta))*[ ,.!?…]*$'
const COM_SOFIA = '(?:a )?sofia'
const ANTES_DA_SOFIA = 'sofia[ ,:]+(?:por favor[ ,]+)?(?:pode )?'
const SO_QUANDO = 'so quando (?:eu |for )?(?:te )?cham(?:ar|o|e|ada)'

function frase(...partes: string[]): RegExp {
  return new RegExp(ABRE + '(?:' + partes.join('|') + ')' + FECHA, 'u')
}

const DESLIGAR = frase('(?:desliga|desligar) ' + COM_SOFIA, ANTES_DA_SOFIA + '(?:desliga|desligar)')
const LIGAR = frase('(?:liga|ligar) ' + COM_SOFIA, ANTES_DA_SOFIA + '(?:liga|ligar)')
const SO_QUANDO_CHAMADA = frase(SO_QUANDO + ' a sofia', ANTES_DA_SOFIA + SO_QUANDO, SO_QUANDO + '[ ,]+sofia')
const ENSINAR = frase(
  ANTES_DA_SOFIA + 'me ensin[ae]',
  'me ensin[ae]( a)?( (?:como )?(?:usar|entender|mexer com|trabalhar com|conhecer))?( a)? sofia',
)

/** O que a pessoa pediu sobre o interruptor, ou null quando a frase é outra coisa. */
export function pedidoDeModo(prompt: string): Modo | 'ensinar' | null {
  if (typeof prompt !== 'string') return null
  const texto = normalizar(prompt)
  if (!PALAVRA_SOFIA.test(texto)) return null
  if (DESLIGAR.test(texto)) return 'desligada'
  if (LIGAR.test(texto)) return 'ligada'
  if (SO_QUANDO_CHAMADA.test(texto)) return 'so-quando-chamada'
  if (ENSINAR.test(texto)) return 'ensinar'
  return null
}

// ---------- estado ----------

/** O estado guardado em estado.json. O que falta, não abre ou está torto vale "ligada". Nunca lança. */
export function lerEstado(texto: string | null): Estado {
  const padrao: Estado = { modo: 'ligada', apresentada: false }
  if (typeof texto !== 'string') return padrao
  let dados: unknown
  try {
    dados = JSON.parse(texto)
  } catch {
    return padrao
  }
  if (typeof dados !== 'object' || dados === null || Array.isArray(dados)) return padrao
  const d = dados as Record<string, unknown>
  const modo = MODOS.find((m) => m === d.modo)
  if (!modo) return padrao
  const estado: Estado = { modo, apresentada: d.apresentada === true }
  if (typeof d.mudouEm === 'string') estado.mudouEm = d.mudouEm
  return estado
}

// ---------- ferramentas ----------

/** Um campo de texto da entrada da ferramenta. Aceita a entrada solta (mod) ou dentro de tool_input (gancho). */
function campo(entrada: unknown, nome: string): string | null {
  if (typeof entrada !== 'object' || entrada === null) return null
  const e = entrada as Record<string, unknown>
  const direto = e[nome]
  if (typeof direto === 'string') return direto
  const dentro = e.tool_input
  if (typeof dentro === 'object' && dentro !== null) {
    const valor = (dentro as Record<string, unknown>)[nome]
    if (typeof valor === 'string') return valor
  }
  return null
}

/** O nome da skill sem o prefixo do plugin, ou null se ela é de outro plugin. */
function nomeNoPlugin(skill: string | null): string | null {
  if (!skill) return null
  const nome = skill.trim().toLowerCase()
  if (nome.startsWith(PREFIXO_DO_PLUGIN)) return nome.slice(PREFIXO_DO_PLUGIN.length)
  return nome.includes(':') ? null : nome
}

/** A ferramenta é da Sofia: uma skill ou comando dela, um agente dela, ou uma ferramenta do conector. */
export function ehDaSofia(ferramenta: string, entrada: unknown): boolean {
  if (typeof ferramenta !== 'string') return false
  if (ferramenta.startsWith(PREFIXO_DO_CONECTOR_NO_PLUGIN) || ferramenta.startsWith(PREFIXO_DO_CONECTOR_NO_SITE)) return true
  if (ferramenta === 'Skill') {
    const skill = campo(entrada, 'skill')
    if (skill?.trim().toLowerCase().startsWith(PREFIXO_DO_PLUGIN)) return true
    // Sem prefixo: só as quatro skills. Comando solto ("plano", "painel"...) não é da Sofia.
    const nome = nomeNoPlugin(skill)
    return nome !== null && NOMES_SEM_PREFIXO.includes(nome)
  }
  if (ferramenta === 'Agent' || ferramenta === 'Task') {
    return (campo(entrada, 'subagent_type') ?? '').trim().toLowerCase().startsWith(PREFIXO_DO_PLUGIN)
  }
  return false
}

/** Nunca se nega: ligar, desligar, modo e ensinar (do plugin e do mod), com ou sem o prefixo do plugin. */
export function ehLivre(ferramenta: string, entrada: unknown): boolean {
  if (ferramenta !== 'Skill') return false
  const nome = nomeNoPlugin(campo(entrada, 'skill'))
  return nome !== null && (LIVRES_NO_PLUGIN.includes(nome) || LIVRES_NO_MOD.includes(nome))
}

/** Libera a ferramenta, ou nega com a linha que o modelo lê. */
export function decidir(estado: Estado, chamadaNaSessao: boolean, ferramenta: string, entrada: unknown): { negar?: string } {
  if (estado.modo === 'ligada') return {}
  if (ehLivre(ferramenta, entrada) || !ehDaSofia(ferramenta, entrada)) return {}
  if (estado.modo === 'desligada') return { negar: AVISO_DESLIGADA }
  if (estado.modo === 'so-quando-chamada' && !chamadaNaSessao) return { negar: AVISO_SO_QUANDO_CHAMADA }
  return {}
}
