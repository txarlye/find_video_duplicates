export interface TelegramStatus {
  bot_configured: boolean
  telethon_configured: boolean
  movie_info_available: boolean
}

export interface ActionResult {
  ok: boolean
  detail: string | null
}

export interface VideoItem {
  name: string
  path: string
  size_mb: number
}

export interface ScanResult {
  videos: VideoItem[]
}

export interface UploadItemResult {
  name: string
  success: boolean
  info_found: boolean
  poster_sent: boolean
  error: string | null
}

export interface UploadResult {
  subidos: number
  fallidos: number
  resultados: UploadItemResult[]
}
