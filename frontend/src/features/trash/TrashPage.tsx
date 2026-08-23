import { useState } from 'react'
import {
  Accordion,
  Alert,
  Button,
  Code,
  Group,
  Loader,
  NumberInput,
  Progress,
  SimpleGrid,
  Paper,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { IconInfoCircle, IconTrash } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import { useTrashQuery, useUpdateLibrarySize } from './useTrash'
import { TrashTable } from './TrashTable'

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Paper withBorder p="md" radius="md">
      <Text size="xs" c="dimmed" tt="uppercase" fw={700}>
        {label}
      </Text>
      <Text size="xl" fw={700}>
        {value}
      </Text>
    </Paper>
  )
}

export function TrashPage() {
  const { data, isLoading, isError, error } = useTrashQuery()
  const updateLibrarySize = useUpdateLibrarySize()
  const [librarySize, setLibrarySize] = useState<number | ''>('')

  if (isLoading) return <Loader />

  if (isError) {
    return (
      <Alert color="red" icon={<IconInfoCircle />}>
        {(error as Error).message}
      </Alert>
    )
  }

  if (!data) return null

  const guardarTamaño = () => {
    if (librarySize === '') return
    updateLibrarySize.mutate(Number(librarySize), {
      onSuccess: () => notifications.show({ color: 'green', message: '✅ Guardado' }),
    })
  }

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>🗑️ Basura / Purgatorio</Title>
        <Text c="dimmed">
          Todo lo que la app ha movido aquí al eliminar duplicados o renombrar huérfanos. La app
          nunca borra nada directamente — esto es la papelera, no el borrado final.
        </Text>
      </div>

      <Code block>{data.debug_folder}</Code>
      <Alert color="blue" icon={<IconInfoCircle />}>
        Esta app <strong>nunca vacía esta carpeta por ti</strong>. Cuando quieras recuperar el
        espacio de verdad, entra a tu NAS y bórrala tú a mano.
      </Alert>

      {!data.exists && (
        <Alert color="blue">📭 Esa carpeta todavía no existe — no se ha movido nada a la papelera todavía.</Alert>
      )}

      {data.exists && data.total_files === 0 && (
        <Alert color="green">✅ El purgatorio está vacío ahora mismo.</Alert>
      )}

      {data.exists && data.total_files > 0 && (
        <>
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <StatCard label="🗑️ Archivos" value={String(data.total_files)} />
            <StatCard label="💾 Espacio en purgatorio" value={`${data.total_gb.toFixed(2)} GB`} />
            <StatCard
              label="🎬 Películas / 📺 Capítulos"
              value={`${data.peliculas.length} / ${data.episodios.length}`}
            />
          </SimpleGrid>

          <Accordion variant="contained">
            <Accordion.Item value="library-size">
              <Accordion.Control icon={<IconTrash size={16} />}>
                📏 Tamaño de tu biblioteca (opcional, para ver qué % has liberado)
              </Accordion.Control>
              <Accordion.Panel>
                <Text size="sm" c="dimmed" mb="sm">
                  No lo calculamos recorriendo la red — para una biblioteca de varios TB tardaría
                  bastante y es un dato que ya conoces de un vistazo a tu NAS. Ponlo aquí una vez y
                  verás qué porcentaje representa lo que llevas purgado.
                </Text>
                <Group>
                  <NumberInput
                    placeholder="Tamaño total aproximado de tu biblioteca (GB)"
                    min={0}
                    step={100}
                    value={librarySize === '' ? data.library_size_gb : librarySize}
                    onChange={(v) => setLibrarySize(v === '' ? '' : Number(v))}
                    w={280}
                  />
                  <Button loading={updateLibrarySize.isPending} onClick={guardarTamaño}>
                    💾 Guardar tamaño de biblioteca
                  </Button>
                </Group>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>

          {data.percent_used !== null && (
            <div>
              <Progress value={data.percent_used * 100} />
              <Text size="sm" c="dimmed" mt={4}>
                📉 Con una biblioteca de ~{data.library_size_gb.toFixed(0)} GB, llevas{' '}
                {data.total_gb.toFixed(2)} GB ({(data.percent_used * 100).toFixed(1)}%) esperando en
                el purgatorio a que los vacíes en el NAS.
              </Text>
            </div>
          )}

          {data.peliculas.length > 0 && (
            <div>
              <Title order={4} mb="xs">
                🎬 Películas ({data.peliculas.length})
              </Title>
              <TrashTable items={data.peliculas} />
            </div>
          )}

          {data.episodios.length > 0 && (
            <div>
              <Title order={4} mb="xs">
                📺 Capítulos de serie ({data.episodios.length})
              </Title>
              <TrashTable items={data.episodios} />
            </div>
          )}
        </>
      )}
    </Stack>
  )
}
