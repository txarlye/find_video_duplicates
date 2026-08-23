export interface EpisodeItem {
  nombre: string
  archivo: string
  tamaño: number
  serie: string
  serie_normalizada: string
  temporada: number
  episodio: number
  carpeta: string
}

export interface SeriesGroup {
  clave: string
  serie: string
  episodios: EpisodeItem[]
  tamaño: number
}

export interface ScanResult {
  duplicados: EpisodeItem[][]
  huerfanos: EpisodeItem[]
  series_sin_indexar: SeriesGroup[]
  total_episodios: number
  sin_reconocer: number
}

export interface MoveBatchResult {
  movidos: number
  errores: string[]
}

export interface SavedScan {
  file_path: string
  scan_path: string
  scan_date: string
  total_pairs: number
}

export interface LoadResult {
  duplicados: EpisodeItem[][]
  huerfanos: EpisodeItem[]
  series_sin_indexar: SeriesGroup[]
  total_guardado: number
  total_caidos: number
}
