/** Uma etapa do quadro: o nome da coluna e quantos cards ela tem. */
export type Etapa = { rotulo: string; total: number }

/** O quadro lido do conector, ou o motivo de não ter lido. */
export type Quadro =
  | { situacao: 'ok'; perfil: string; etapas: Etapa[]; lidoEm: number }
  | { situacao: 'sem-conector'; motivo: string; lidoEm: number }

/** Uma janela de uso do Claude: 5 horas ou 7 dias. */
export type Janela = { tipo: string; usado: number; zeraEm?: number }

/** O modo do interruptor da Sofia neste computador (o mesmo `Modo` de hooks/interruptor.ts). */
export type ModoDoInterruptor = 'ligada' | 'so-quando-chamada' | 'desligada'

declare module 'claude-code' {
  interface PluginState {
    'sofia-estrategista': {
      quadro: Shaped<Quadro | null>
      janelas: Shaped<Janela[]>
      /** O modo lido de estado.json por último: o painel desenha a partir dele. */
      modo: Shaped<ModoDoInterruptor>
      /** Se a pessoa chamou a Sofia pelo nome nesta sessão, pelo id da sessão. */
      chamada: StateFamily<boolean>
    }
  }
}
