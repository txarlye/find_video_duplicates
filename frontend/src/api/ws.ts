import { useEffect, useRef, useState } from 'react'

export interface JobState<TResult = unknown> {
  id: string
  status: 'running' | 'done' | 'error' | 'cancelled'
  percent: number
  message: string
  result: TResult | null
  error: string | null
  item: Record<string, unknown> | null
}

/**
 * Se conecta a /ws/jobs/{jobId} y mantiene el último estado del job,
 * más la lista de eventos "item" recibidos según van llegando (para
 * pintar resultados parciales antes de que el job entero termine —
 * ej. cada sugerencia de nombre de la IA en cuanto está lista).
 */
export function useJobProgress<TResult = unknown, TItem = Record<string, unknown>>(
  jobId: string | null,
  onItem?: (item: TItem) => void,
) {
  const [state, setState] = useState<JobState<TResult> | null>(null)
  const onItemRef = useRef(onItem)
  onItemRef.current = onItem

  useEffect(() => {
    if (!jobId) {
      setState(null)
      return
    }

    setState(null)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/jobs/${jobId}`)

    ws.onmessage = (event) => {
      const data: JobState<TResult> = JSON.parse(event.data)
      setState(data)
      if (data.item && onItemRef.current) {
        onItemRef.current(data.item as TItem)
      }
    }

    return () => ws.close()
  }, [jobId])

  return state
}
