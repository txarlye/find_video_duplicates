export interface DetectionSettings {
  similarity_threshold: number
  excluded_directories: string[]
  duration_filter_enabled: boolean
  duration_tolerance_minutes: number
}

export interface DetectionUpdate {
  similarity_threshold: number
  duration_filter_enabled: boolean
  duration_tolerance_minutes: number
}

export interface PlayerSettings {
  show_video_players: boolean
  show_embedded_players: boolean
  video_player_size: 'small' | 'medium' | 'large'
  video_start_time_seconds: number
  debug_folder: string
}

export interface PlexSettings {
  database_path: string
  movies_library: string
  tv_shows_library: string
  fetch_metadata: boolean
  duration_filter_enabled: boolean
  duration_tolerance_minutes: number
  is_configured: boolean
}

export type PlexUpdate = Omit<PlexSettings, 'is_configured'>

export interface PlexLibrary {
  name: string
}

export interface ActionResult {
  ok: boolean
  detail: string | null
}

export interface TelegramStatus {
  configured: boolean
  channel_id: string | null
}

export interface AutomationSettings {
  enabled: boolean
  movie_folders: string[]
  schedule_time: string
  email_to: string
  app_url: string
  email_message: string
  size_premium_tolerance_pct: number
  size_premium_max_gb: number
  smtp_configured: boolean
  smtp_user: string | null
  last_run_date: string | null
  synology_configured: boolean
}

export type AutomationUpdate = Omit<
  AutomationSettings,
  'movie_folders' | 'smtp_configured' | 'smtp_user' | 'last_run_date' | 'synology_configured'
>

export interface AiNamingSettings {
  enabled: boolean
  provider: 'ollama' | 'openai' | 'gemini'
  mode: 'suggest' | 'auto'
  ollama_url: string
  ollama_model: string
  openai_model: string
  gemini_model: string
  openai_key_configured: boolean
  gemini_key_configured: boolean
  tmdb_configured: boolean
  omdb_configured: boolean
}

export type AiNamingUpdate = Omit<
  AiNamingSettings,
  'openai_key_configured' | 'gemini_key_configured' | 'tmdb_configured' | 'omdb_configured'
>
