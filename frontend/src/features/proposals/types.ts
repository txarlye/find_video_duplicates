export interface HuerfanoProposal {
  clave: string
  archivo: string
  nombre_actual: string
  nombre_sugerido: string
  tamaño: number
}

export interface DuplicadoProposal {
  clave: string
  archivo_a_borrar: string
  archivo_a_conservar: string
  nombre_a_borrar: string
  nombre_a_conservar: string
  tamaño_a_borrar: number
  tamaño_a_conservar: number
  motivo: string
}

export interface ProposalsResponse {
  huerfanos: HuerfanoProposal[]
  duplicados: DuplicadoProposal[]
}

export interface BatchResult {
  aplicados: number
  errores: string[]
}

export interface DismissedProposals {
  huerfanos: string[]
  duplicados: string[]
}
