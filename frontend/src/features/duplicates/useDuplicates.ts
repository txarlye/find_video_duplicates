import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { BulkMoveResult, DeleteResult, DuplicatePair, LoadResult, PlexMetadataResponse, SavedScan } from './types'

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
