import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { EpisodeItem, LoadResult, MoveBatchResult, SavedScan, SeriesGroup } from './types'

export function useScanSeries() {
  return useMutation({ mutationFn: (folder: string) => api.post<{ job_id: string }>('/series/scan', { folder }) })
}

export function useMoveEpisode() {
  return useMutation({ mutationFn: (archivo: string) => api.post<MoveBatchResult>('/series/move', { archivo }) })
}

export function useMoveEpisodesBatch() {
  return useMutation({ mutationFn: (archivos: string[]) => api.post<MoveBatchResult>('/series/move-batch', { archivos }) })
}

export function useRenameSeriesOrphan() {
  return useMutation({
    mutationFn: (body: { archivo: string; nuevo_nombre: string }) => api.post<EpisodeItem>('/series/rename', body),
  })
}

export function useIgnoredSeriesQuery() {
  return useQuery({ queryKey: ['series', 'ignored'], queryFn: () => api.get<{ claves: string[] }>('/series/ignored') })
}

export function useIgnoreSeries() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (clave: string) => api.post<{ claves: string[] }>('/series/ignore', { clave }),
    onSuccess: (data) => qc.setQueryData(['series', 'ignored'], data),
  })
}

export function useUnignoreSeries() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (clave: string) => api.delete<{ claves: string[] }>(`/series/ignore/${encodeURIComponent(clave)}`),
    onSuccess: (data) => qc.setQueryData(['series', 'ignored'], data),
  })
}

export function useSaveSeriesScan() {
  return useMutation({
    mutationFn: (body: { folder: string; duplicados: EpisodeItem[][]; huerfanos: EpisodeItem[]; series_sin_indexar: SeriesGroup[] }) =>
      api.post<{ file_path: string }>('/series/save', body),
  })
}

export function useSavedSeriesScans(enabled: boolean) {
  return useQuery({
    queryKey: ['series', 'saved'],
    queryFn: () => api.get<SavedScan[]>('/series/saved'),
    enabled,
  })
}

export function useLoadSeriesScan() {
  return useMutation({ mutationFn: (file_path: string) => api.post<LoadResult>('/series/load', { file_path }) })
}
