import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { RestoreResult, TrashListResponse } from './types'

const TRASH_KEY = ['trash'] as const

export function useTrashQuery() {
  return useQuery({
    queryKey: TRASH_KEY,
    queryFn: () => api.get<TrashListResponse>('/trash'),
  })
}

export function useUpdateLibrarySize() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (library_size_gb: number) =>
      api.put<{ library_size_gb: number }>('/trash/library-size', { library_size_gb }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TRASH_KEY }),
  })
}

export function useRestoreFromTrash() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (rutas: string[]) => api.post<RestoreResult>('/trash/restore', { rutas }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TRASH_KEY }),
  })
}
