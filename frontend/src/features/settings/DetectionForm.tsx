import { useEffect, useState } from 'react'
import { Button, Checkbox, Group, List, Loader, Slider, Stack, Text, TextInput, Title } from '@mantine/core'
import { IconTrash } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import {
  useAddExcludedDirectory,
  useDetectionQuery,
  useRemoveExcludedDirectory,
  useSaveDetection,
} from './useSettings'

export function DetectionForm() {
  const { data, isLoading } = useDetectionQuery()
  const save = useSaveDetection()
  const addDir = useAddExcludedDirectory()
  const removeDir = useRemoveExcludedDirectory()

  const [threshold, setThreshold] = useState(0.8)
  const [durationFilter, setDurationFilter] = useState(true)
  const [tolerance, setTolerance] = useState(1)
  const [newDir, setNewDir] = useState('')

  useEffect(() => {
    if (!data) return
    setThreshold(data.similarity_threshold)
    setDurationFilter(data.duration_filter_enabled)
    setTolerance(data.duration_tolerance_minutes)
  }, [data])

  if (isLoading || !data) return <Loader />

  const guardar = () => {
    save.mutate(
      { similarity_threshold: threshold, duration_filter_enabled: durationFilter, duration_tolerance_minutes: tolerance },
      { onSuccess: () => notifications.show({ color: 'green', message: '✅ Guardado' }) },
    )
  }

  return (
    <Stack gap="md">
      <div>
        <Text fw={500} mb="xs">
          Umbral de similitud
        </Text>
        <Slider min={0.1} max={1} step={0.1} value={threshold} onChange={setThreshold} label={(v) => v.toFixed(1)} />
        <Text size="sm" c="dimmed" mt={4}>
          Umbral para considerar películas como duplicadas — configurado: {threshold.toFixed(1)}
        </Text>
      </div>

      <div>
        <Title order={5} mb="xs">
          🚫 Directorios Excluidos
        </Title>
        <Text size="sm" c="dimmed" mb="xs">
          Estos directorios se excluirán automáticamente del escaneo
        </Text>
        <List spacing={4} mb="sm">
          {data.excluded_directories.map((dir) => (
            <List.Item
              key={dir}
              icon={
                <IconTrash
                  size={16}
                  style={{ cursor: 'pointer' }}
                  onClick={() => removeDir.mutate(dir)}
                />
              }
            >
              {dir}
            </List.Item>
          ))}
        </List>
        <Group>
          <TextInput
            placeholder="ej: test"
            value={newDir}
            onChange={(e) => setNewDir(e.currentTarget.value)}
            w={240}
          />
          <Button
            variant="light"
            loading={addDir.isPending}
            onClick={() => {
              if (!newDir) return
              addDir.mutate(newDir, { onSuccess: () => setNewDir('') })
            }}
          >
            ➕ Agregar
          </Button>
        </Group>
      </div>

      <div>
        <Title order={5} mb="xs">
          🎬 Filtro por Duración
        </Title>
        <Checkbox
          label="Filtrar por duración"
          description="Descartar duplicados si la diferencia de duración es muy grande"
          checked={durationFilter}
          onChange={(e) => setDurationFilter(e.currentTarget.checked)}
          mb="sm"
        />
        {durationFilter && (
          <>
            <Slider
              min={1}
              max={30}
              value={tolerance}
              onChange={setTolerance}
              label={(v) => `${v} min`}
              mb={4}
            />
            <Text size="sm" c="dimmed">
              Tolerancia: {tolerance} minutos
            </Text>
          </>
        )}
      </div>

      <Group>
        <Button loading={save.isPending} onClick={guardar}>
          💾 Guardar
        </Button>
      </Group>
    </Stack>
  )
}
