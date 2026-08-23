export interface OrphanItem {
  nombre: string
  archivo: string
  tamaño: number
  renombrado: boolean
}

export interface ScanResult {
  items: OrphanItem[]
  total_escaneados: number
}

export interface SuggestBatchItem {
  archivo: string
  nombre: string
}

export interface SuggestBatchResult {
  resultados: { archivo: string; sugerido: string | null }[]
  sugeridos: number
  sin_sugerencia: number
  total: number
}

export interface RenameBatchItem {
  archivo: string
  nuevo_nombre: string
}

export interface RenameBatchResult {
  renombrados: number
  errores: string[]
}

export interface SavedScan {
  file_path: string
  scan_path: string
  scan_date: string
  total_pairs: number
}

export interface LoadResult {
  items: OrphanItem[]
  total_guardados: number
  no_existentes: number
  ya_renombrados: number
}
