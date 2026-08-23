import { useState } from 'react'
import { Button, Group, Text } from '@mantine/core'
import { DataTable } from 'mantine-datatable'
import { notifications } from '@mantine/notifications'
import type { TrashItem } from './types'
import { useRestoreFromTrash } from './useTrash'

export function TrashTable({ items }: { items: TrashItem[] }) {
  const [selected, setSelected] = useState<TrashItem[]>([])
  const restore = useRestoreFromTrash()

  const onRestore = () => {
    restore.mutate(
      selected.map((s) => s.ruta),
      {
        onSuccess: (result) => {
          if (result.restaurados.length) {
            notifications.show({
              color: 'green',
              message: `✅ ${result.restaurados.length} archivo(s) restaurado(s)`,
            })
          }
          if (result.sin_origen.length) {
            notifications.show({
              color: 'yellow',
              message: `⚠️ Sin origen conocido, no se han movido: ${result.sin_origen.join(', ')}`,
            })
          }
          if (result.fallidos.length) {
            notifications.show({ color: 'red', message: `❌ ${result.fallidos.join('; ')}` })
          }
          setSelected([])
        },
      },
    )
  }

  return (
    <div>
      <DataTable
        withTableBorder
        minHeight={items.length ? undefined : 120}
        records={items}
        idAccessor="ruta"
        selectedRecords={selected}
        onSelectedRecordsChange={setSelected}
        columns={[
          { accessor: 'nombre', title: 'Nombre' },
          { accessor: 'gb', title: 'GB', width: 90, render: (r) => r.gb.toFixed(2) },
          {
            accessor: 'origen',
            title: 'Origen',
            render: (r) =>
              r.origen ?? <Text c="dimmed" size="sm">❓ Desconocido (movido antes de tener esta función)</Text>,
          },
        ]}
      />
      {selected.length > 0 && (
        <Group justify="flex-end" mt="sm">
          <Button loading={restore.isPending} onClick={onRestore}>
            ↩️ Restaurar {selected.length} archivo(s) a su carpeta original
          </Button>
        </Group>
      )}
    </div>
  )
}
