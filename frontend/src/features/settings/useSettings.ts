import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import type {
  ActionResult,
  AiNamingSettings,
  AiNamingUpdate,
  AutomationSettings,
  AutomationUpdate,
  DetectionSettings,
  DetectionUpdate,
  PlayerSettings,
  PlexLibrary,
  PlexSettings,
  PlexUpdate,
  TelegramStatus,
} from './types'

// ---------- Detección ----------

export function useDetectionQuery() {
  return useQuery({ queryKey: ['settings', 'detection'], queryFn: () => api.get<DetectionSettings>('/settings/detection') })
}

export function useSaveDetection() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: DetectionUpdate) => api.put<DetectionSettings>('/settings/detection', body),
    onSuccess: (data) => qc.setQueryData(['settings', 'detection'], data),
  })
}

export function useAddExcludedDirectory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (directory: string) => api.post<DetectionSettings>('/settings/detection/excluded-directories', { directory }),
    onSuccess: (data) => qc.setQueryData(['settings', 'detection'], data),
  })
}

export function useRemoveExcludedDirectory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (directory: string) =>
      api.delete<DetectionSettings>(`/settings/detection/excluded-directories/${encodeURIComponent(directory)}`),
    onSuccess: (data) => qc.setQueryData(['settings', 'detection'], data),
  })
}

// ---------- Reproductores y Debug ----------

export function usePlayersQuery() {
  return useQuery({ queryKey: ['settings', 'players'], queryFn: () => api.get<PlayerSettings>('/settings/players') })
}

export function useSavePlayers() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: PlayerSettings) => api.put<PlayerSettings>('/settings/players', body),
    onSuccess: (data) => qc.setQueryData(['settings', 'players'], data),
  })
}

// ---------- Plex ----------

export function usePlexQuery() {
  return useQuery({ queryKey: ['settings', 'plex'], queryFn: () => api.get<PlexSettings>('/settings/plex') })
}

export function usePlexLibrariesQuery(enabled: boolean) {
  return useQuery({
    queryKey: ['settings', 'plex', 'libraries'],
    queryFn: () => api.get<PlexLibrary[]>('/settings/plex/libraries'),
    enabled,
  })
}

export function useSavePlex() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: PlexUpdate) => api.put<PlexSettings>('/settings/plex', body),
    onSuccess: (data) => qc.setQueryData(['settings', 'plex'], data),
  })
}

export function usePlexAction(action: 'test-connection' | 'refresh-movies' | 'refresh-tv' | 'refresh-all') {
  return useMutation({ mutationFn: () => api.post<ActionResult>(`/settings/plex/${action}`) })
}

export function usePlexServerInfo() {
  return useMutation({ mutationFn: () => api.get<Record<string, unknown>>('/settings/plex/server-info') })
}

// ---------- Telegram ----------

export function useTelegramStatusQuery() {
  return useQuery({ queryKey: ['settings', 'telegram'], queryFn: () => api.get<TelegramStatus>('/settings/telegram') })
}

// ---------- Automatización ----------

export function useAutomationQuery() {
  return useQuery({ queryKey: ['settings', 'automation'], queryFn: () => api.get<AutomationSettings>('/settings/automation') })
}

export function useSaveAutomation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: AutomationUpdate) => api.put<AutomationSettings>('/settings/automation', body),
    onSuccess: (data) => qc.setQueryData(['settings', 'automation'], data),
  })
}

export function useSaveAutomationFolders() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (folders: string[]) => api.put<AutomationSettings>('/settings/automation/folders', { folders }),
    onSuccess: (data) => qc.setQueryData(['settings', 'automation'], data),
  })
}

export function useTestAutomationEmail() {
  return useMutation({ mutationFn: () => api.post<ActionResult>('/settings/automation/test-email') })
}

// ---------- IA para sugerencia de nombres (Huérfanos/Propuestas) ----------

export function useAiNamingQuery() {
  return useQuery({ queryKey: ['settings', 'ai-naming'], queryFn: () => api.get<AiNamingSettings>('/settings/ai-naming') })
}

export function useSaveAiNaming() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: AiNamingUpdate) => api.put<AiNamingSettings>('/settings/ai-naming', body),
    onSuccess: (data) => qc.setQueryData(['settings', 'ai-naming'], data),
  })
}
