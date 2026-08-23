import { useState } from 'react'
import { Button, Group } from '@mantine/core'
import { DataTable, type DataTableColumn } from 'mantine-datatable'

export interface BulkAction<T> {
  label: string
  color?: string
  loading?: boolean
  onClick: (selected: T[]) => void
}

/**
 * Tabla paginada + selección + acciones en lote, genérica — sustituye
 * las 3 implementaciones caseras distintas que había en Streamlit
 * (Series, Propuestas, el job de IA en lote de Huérfanos) por un único
 * componente reutilizado en cada pantalla que lo necesite.
 */
export function ScanResultsShell<T extends Record<string, unknown>>({
  records,
  idAccessor,
  columns,
  bulkActions,
  emptyMessage = 'Ninguna propuesta pendiente.',
}: {
  records: T[]
  idAccessor: string
  columns: DataTableColumn<T>[]
  bulkActions: BulkAction<T>[]
  emptyMessage?: string
}) {
  const [selected, setSelected] = useState<T[]>([])

  return (
    <div>
      <DataTable
        withTableBorder
        minHeight={records.length ? undefined : 100}
        noRecordsText={emptyMessage}
        records={records}
        idAccessor={idAccessor}
        selectedRecords={selected}
        onSelectedRecordsChange={setSelected}
        columns={columns}
      />
      {selected.length > 0 && (
        <Group justify="flex-end" mt="sm">
          {bulkActions.map((action) => (
            <Button
              key={action.label}
              color={action.color}
              loading={action.loading}
              onClick={() => {
                action.onClick(selected)
                setSelected([])
              }}
            >
              {action.label} ({selected.length})
            </Button>
          ))}
        </Group>
      )}
    </div>
  )
}
