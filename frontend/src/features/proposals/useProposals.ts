import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { BatchResult, DismissedProposals, DuplicadoProposal, HuerfanoProposal, ProposalsResponse } from './types'

export function useGenerateProposals() {
  return useMutation({ mutationFn: () => api.post<ProposalsResponse>('/proposals/generate') })
}

export function useApplyHuerfanos() {
  return useMutation({
    mutationFn: (items: HuerfanoProposal[]) => api.post<BatchResult>('/proposals/huerfanos/apply', { items }),
  })
}

export function useDismissHuerfanos() {
  return useMutation({
    mutationFn: (claves: string[]) => api.post('/proposals/huerfanos/dismiss', { claves }),
  })
}

export function useApplyDuplicados() {
  return useMutation({
    mutationFn: (items: DuplicadoProposal[]) => api.post<BatchResult>('/proposals/duplicados/apply', { items }),
  })
}

export function useDismissDuplicados() {
  return useMutation({
    mutationFn: (claves: string[]) => api.post('/proposals/duplicados/dismiss', { claves }),
  })
}

export function useDismissedProposalsQuery() {
  return useQuery({ queryKey: ['proposals', 'dismissed'], queryFn: () => api.get<DismissedProposals>('/proposals/dismissed') })
}

export function useUndismissHuerfano() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (archivo: string) => api.post('/proposals/dismissed/huerfanos/remove', { archivo }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['proposals', 'dismissed'] }),
  })
}

export function useUndismissDuplicado() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (clave: string) => api.post('/proposals/dismissed/duplicados/remove', { clave }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['proposals', 'dismissed'] }),
  })
}
