export interface FileInfo {
  nombre: string
  ruta: string
  tamaño: number
  duracion: number
  existe: boolean
  creado: string | null
}

export interface DuplicatePair {
  clave: string
  peli1: FileInfo
  peli2: FileInfo
}

export interface ScanResult {
  pares: DuplicatePair[]
  total_peliculas: number
}

export interface PlexMovieMetadata {
  encontrado: boolean
  datos: Record<string, unknown> | null
}

export interface PlexMetadataResponse {
  file1: PlexMovieMetadata
  file2: PlexMovieMetadata
  es_duplicado_plex: boolean
  duracion_compatible: boolean | null
  duracion_mensaje: string | null
}

export interface DeleteResult {
  movidos: number
  errores: string[]
}

export interface BulkMoveResult {
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
  pares: DuplicatePair[]
  total_guardado: number
  no_existentes: number
}

export interface VideoInfo {
  duration_seconds: number | null
  duration_formatted: string
  resolution: string
  video_codec: string
  audio: string
  container: string
  fps: number | null
}

export interface EditionSuggestionsResponse {
  sugerencias: string[]
}

export interface CreateEditionResult {
  ok: boolean
  nueva_ruta: string | null
  detail: string | null
}
