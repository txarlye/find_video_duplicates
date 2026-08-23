import { useQuery } from '@tanstack/react-query'
import { Select, Stack, TextInput } from '@mantine/core'
import { api } from '../api/client'

/**
 * Campo de ruta de carpeta con desplegable de hasta 5 rutas usadas
 * recientemente para esa categoría (duplicados/huérfanos/series/...).
 * Puerto de _render_folder_path_input de streamlit_manager.py, ahora
 * como componente compartido — a diferencia del original, aquí también
 * lo usan Telegram/IMDB cuando se migren (antes tenían su propio campo
 * de texto suelto sin historial).
 */
export function RecentPathInput({
  label,
  category,
  value,
  onChange,
  helpText,
}: {
  label: string
  category: string
  value: string
  onChange: (value: string) => void
  helpText?: string
}) {
  const { data: recientes } = useQuery({
    queryKey: ['settings', 'recent-paths', category],
    queryFn: () => api.get<string[]>(`/settings/recent-paths/${category}`),
  })

  return (
    <Stack gap={4}>
      {recientes && recientes.length > 0 && (
        <Select
          label="📋 Rutas recientes"
          placeholder="— elegir de recientes —"
          data={recientes}
          value={null}
          onChange={(v) => v && onChange(v)}
          clearable={false}
        />
      )}
      <TextInput label={label} description={helpText} value={value} onChange={(e) => onChange(e.currentTarget.value)} />
    </Stack>
  )
}
