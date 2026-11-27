/** Uma etapa do quadro: o nome da coluna e quantos cards ela tem. */
export type Etapa = { rotulo: string; total: number }

/**
 * O quadro que a Sofia leu por último com planejamento_quadro, ou o motivo de a leitura não ter dado certo.
 * `mudouDepois`: uma ferramenta do planejamento mudou o quadro depois desta leitura.
 */
export type Quadro =
  | { situacao: 'ok'; perfil: string; etapas: Etapa[]; lidoEm: number; mudouDepois: boolean }
  | { situacao: 'sem-leitura'; motivo: string; lidoEm: number }

/** Uma janela de uso do Claude: 5 horas ou 7 dias. */
export type Janela = { tipo: string; usado: number; zeraEm?: number }

/** O modo do interruptor da Sofia neste computador (o mesmo `Modo` de hooks/interruptor.ts). */
export type ModoDoInterruptor = 'ligada' | 'so-quando-chamada' | 'desligada'

declare module 'claude-code' {
  interface PluginState {
    'sofia-painel': {
      /** null até a Sofia ler o planejamento nesta sessão. */
      quadro: Shaped<Quadro | null>
      janelas: Shaped<Janela[]>
      /** O modo lido de estado.json por último: o painel desenha a partir dele. */
      modo: Shaped<ModoDoInterruptor>
      /** Se a pessoa chamou a Sofia pelo nome nesta sessão, pelo id da sessão. */
      chamada: StateFamily<boolean>
      /** Se o mod ofereceu ligar ("Estou desligada aqui. Quer que eu ligue?") no último prompt, pela sessão. */
      ofereceuLigar: StateFamily<boolean>
      /** Se o último prompt da pessoa deixa o modelo trocar o modo pela skill, pela sessão. */
      podeTrocarModo: StateFamily<boolean>
      /** Se o mod pôs a linha do primeiro uso no último prompt (a resposta curta do modo vale no seguinte), pela sessão. */
      perguntouModo: StateFamily<boolean>
      /** Se a linha do primeiro uso já veio nesta sessão (sem chamar a Sofia, ela não volta), pela sessão. */
      avisouPrimeiroUso: StateFamily<boolean>
    }
  }
}
