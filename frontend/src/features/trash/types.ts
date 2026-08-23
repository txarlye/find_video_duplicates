export interface TrashItem {
  nombre: string
  gb: number
  ruta: string
  origen: string | null
}

export interface TrashListResponse {
  debug_folder: string
  exists: boolean
  total_files: number
  total_gb: number
  library_size_gb: number
  percent_used: number | null
  peliculas: TrashItem[]
  episodios: TrashItem[]
}

export interface RestoreResult {
  restaurados: string[]
  sin_origen: string[]
  fallidos: string[]
}
