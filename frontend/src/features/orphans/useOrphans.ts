import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type {
  LoadResult,
  RenameBatchResult,
  SavedScan,
  ScanResult,
  SuggestBatchResult,
} from './types'
import type { OrphanItem, RenameBatchItem, SuggestBatchItem } from './types'

export function useScanOrphans() {
  return useMutation({ mutationFn: (folder: string) => api.post<{ job_id: string }>('/orphans/scan', { folder }) })
}

export function useSuggestOrphanName() {
  return useMutation({
    mutationFn: (nombre: string) => api.post<{ sugerido: string | null }>('/orphans/suggest', { nombre }),
  })
}

export function useSuggestOrphansBatch() {
  return useMutation({
    mutationFn: (body: { items: SuggestBatchItem[]; scope: number | null }) =>
      api.post<{ job_id: string }>('/orphans/suggest-batch', body),
  })
}

export function useRenameOrphan() {
  return useMutation({
    mutationFn: (body: { archivo: string; nuevo_nombre: string }) => api.post<OrphanItem>('/orphans/rename', body),
  })
}

export function useRenameOrphansBatch() {
  return useMutation({
    mutationFn: (items: RenameBatchItem[]) => api.post<RenameBatchResult>('/orphans/rename-batch', { items }),
  })
}

export function useSaveOrphansScan() {
  return useMutation({
    mutationFn: (body: { folder: string; items: OrphanItem[] }) => api.post<{ file_path: string }>('/orphans/save', body),
  })
}

export function useSavedOrphanScans(enabled: boolean) {
  return useQuery({
    queryKey: ['orphans', 'saved'],
    queryFn: () => api.get<SavedScan[]>('/orphans/saved'),
    enabled,
  })
}

export function useLoadOrphansScan() {
  return useMutation({
    mutationFn: (file_path: string) => api.post<LoadResult>('/orphans/load', { file_path }),
  })
}

export type { ScanResult, SuggestBatchResult }
