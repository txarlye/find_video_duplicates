import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type {
  BulkMoveResult,
  CheckHashResult,
  CreateEditionResult,
  DeleteResult,
  DuplicatePair,
  EditionSuggestionsResponse,
  LoadResult,
  PlexMetadataResponse,
  SavedScan,
  VideoInfo,
} from './types'

export function useScanDuplicates() {
  return useMutation({ mutationFn: (folder: string) => api.post<{ job_id: string }>('/duplicates/scan', { folder }) })
}

export function usePlexMetadataForPair() {
  return useMutation({
    mutationFn: (body: { ruta1: string; ruta2: string }) => api.post<PlexMetadataResponse>('/duplicates/plex-metadata', body),
  })
}

export function useDeleteDuplicates() {
  return useMutation({ mutationFn: (archivos: string[]) => api.post<DeleteResult>('/duplicates/delete', { archivos }) })
}

export function useBulkMoveDuplicates() {
  return useMutation({
    mutationFn: (body: { archivos: string[]; destino: string }) => api.post<BulkMoveResult>('/duplicates/bulk-move', body),
  })
}

export function useSaveDuplicatesScan() {
  return useMutation({
    mutationFn: (body: { folder: string; pares: DuplicatePair[] }) => api.post<{ file_path: string }>('/duplicates/save', body),
  })
}

export function useSavedDuplicatesScans(enabled: boolean) {
  return useQuery({
    queryKey: ['duplicates', 'saved'],
    queryFn: () => api.get<SavedScan[]>('/duplicates/saved'),
    enabled,
  })
}

export function useLoadDuplicatesScan() {
  return useMutation({ mutationFn: (file_path: string) => api.post<LoadResult>('/duplicates/load', { file_path }) })
}

export function useEditionSuggestions(movieTitle: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ['duplicates', 'edition-suggestions', movieTitle],
    queryFn: () => api.get<EditionSuggestionsResponse>(`/duplicates/edition-suggestions?movie_title=${encodeURIComponent(movieTitle as string)}`),
    enabled: enabled && !!movieTitle,
  })
}

export function useCreateEdition() {
  return useMutation({
    mutationFn: (body: { archivo: string; movie_title: string; edition_name: string }) =>
      api.post<CreateEditionResult>('/duplicates/create-edition', body),
  })
}

// Bajo demanda solo (nunca automático en el escaneo) — hash MD5 en
// streaming de los dos archivos, puede tardar varios minutos en
// archivos grandes: el cuello de botella es leerlos enteros, no la CPU.
export function useCheckHash() {
  return useMutation({
    mutationFn: (body: { ruta1: string; ruta2: string }) => api.post<CheckHashResult>('/duplicates/check-hash', body),
  })
}

/**
 * Duración/resolución/códec "en vivo" (ffprobe) para un archivo — el
 * dato del escaneo (mutagen) puede fallar/quedarse en 0 para según qué
 * MKV, así que el detalle del par siempre pide esto en vez de fiarse
 * del valor precalculado.
 */
export function useVideoInfo(ruta: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ['duplicates', 'video-info', ruta],
    queryFn: () => api.get<VideoInfo>(`/video/info?path=${encodeURIComponent(ruta as string)}`),
    enabled: enabled && !!ruta,
    retry: false,
  })
}
