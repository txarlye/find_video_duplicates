import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { ActionResult, ScanResult, TelegramStatus, VideoItem } from './types'

export function useTelegramStatusQuery() {
  return useQuery({ queryKey: ['telegram', 'status'], queryFn: () => api.get<TelegramStatus>('/telegram/status') })
}

export function useTelegramTestConnection() {
  return useMutation({ mutationFn: () => api.post<ActionResult>('/telegram/test-connection') })
}

export function useTelegramTestMessage() {
  return useMutation({ mutationFn: () => api.post<ActionResult>('/telegram/test-message') })
}

export function useScanTelegramFolder() {
  return useMutation({ mutationFn: (folder: string) => api.post<ScanResult>('/telegram/scan', { folder }) })
}

export function useUploadToTelegram() {
  return useMutation({
    mutationFn: (body: { videos: VideoItem[]; enrich: boolean }) => api.post<{ job_id: string }>('/telegram/upload', body),
  })
}
