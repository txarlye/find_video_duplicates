import { useEffect, useState } from 'react'
import {
  Alert,
  Button,
  Checkbox,
  Code,
  Group,
  Loader,
  Select,
  SimpleGrid,
  Slider,
  Stack,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import {
  usePlexAction,
  usePlexLibrariesQuery,
  usePlexQuery,
  usePlexServerInfo,
  useSavePlex,
} from './useSettings'
import type { PlexUpdate } from './types'

export function PlexForm() {
  const { data, isLoading } = usePlexQuery()
  const save = useSavePlex()
  const [form, setForm] = useState<PlexUpdate | null>(null)
  const [loadLibraries, setLoadLibraries] = useState(false)
  const { data: libraries } = usePlexLibrariesQuery(loadLibraries)
  const testConnection = usePlexAction('test-connection')
  const refreshMovies = usePlexAction('refresh-movies')
  const refreshTv = usePlexAction('refresh-tv')
  const refreshAll = usePlexAction('refresh-all')
  const serverInfo = usePlexServerInfo()

  useEffect(() => {
    if (data) setForm(data)
  }, [data])

  if (isLoading || !form) return <Loader />

  const guardar = () => {
    save.mutate(form, { onSuccess: () => notifications.show({ color: 'green', message: '✅ Configuración de Plex guardada' }) })
  }

  const nombresBibliotecas = libraries?.map((l) => l.name) ?? []

  const runAction = (
    mutation: typeof testConnection,
    okMessage: string,
  ) => {
    mutation.mutate(undefined, {
      onSuccess: (result) =>
        notifications.show({
          color: result.ok ? 'green' : 'red',
          message: result.ok ? okMessage : `❌ ${result.detail}`,
        }),
    })
  }

  return (
    <Stack gap="md">
      <Title order={5}>🎬 Configuración de Plex</Title>
      {form.database_path && data?.is_configured ? (
        <Alert color="green">✅ Plex configurado</Alert>
      ) : (
        <Alert color="red">❌ Plex no configurado</Alert>
      )}

      <TextInput
        label="📁 Ruta de Base de Datos"
        description="Ruta completa al archivo com.plexapp.plugins.library.db"
        value={form.database_path}
        onChange={(e) => setForm({ ...form, database_path: e.currentTarget.value })}
      />

      <Group align="flex-end">
        <Button variant="light" onClick={() => setLoadLibraries(true)}>
          🔄 Cargar Bibliotecas
        </Button>
      </Group>

      <SimpleGrid cols={{ base: 1, sm: 2 }}>
        {nombresBibliotecas.length > 0 ? (
          <Select
            label="🎬 Biblioteca de películas"
            data={nombresBibliotecas}
            value={form.movies_library}
            onChange={(v) => v && setForm({ ...form, movies_library: v })}
          />
        ) : (
          <TextInput
            label="🎬 Biblioteca de películas"
            value={form.movies_library}
            onChange={(e) => setForm({ ...form, movies_library: e.currentTarget.value })}
          />
        )}
        {nombresBibliotecas.length > 0 ? (
          <Select
            label="📺 Biblioteca de series"
            data={nombresBibliotecas}
            value={form.tv_shows_library}
            onChange={(v) => v && setForm({ ...form, tv_shows_library: v })}
          />
        ) : (
          <TextInput
            label="📺 Biblioteca de series"
            value={form.tv_shows_library}
            onChange={(e) => setForm({ ...form, tv_shows_library: e.currentTarget.value })}
          />
        )}
      </SimpleGrid>

      <Title order={5} mt="sm">
        📊 Metadatos
      </Title>
      <Checkbox
        label="🔍 Traer metadatos de Plex"
        checked={form.fetch_metadata}
        onChange={(e) => setForm({ ...form, fetch_metadata: e.currentTarget.checked })}
      />
      <Checkbox
        label="⏱️ Filtro por duración"
        checked={form.duration_filter_enabled}
        onChange={(e) => setForm({ ...form, duration_filter_enabled: e.currentTarget.checked })}
      />
      {form.duration_filter_enabled && (
        <Slider
          min={1}
          max={30}
          value={form.duration_tolerance_minutes}
          onChange={(v) => setForm({ ...form, duration_tolerance_minutes: v })}
          label={(v) => `${v} min`}
        />
      )}

      <Group>
        <Button
          variant="light"
          loading={testConnection.isPending}
          onClick={() => runAction(testConnection, '✅ Conexión exitosa')}
        >
          🧪 Probar Conexión
        </Button>
        <Button loading={save.isPending} onClick={guardar}>
          💾 Guardar Configuración
        </Button>
      </Group>

      <Title order={5} mt="sm">
        🔄 Refrescar Bibliotecas
      </Title>
      <Group>
        <Button
          variant="light"
          loading={refreshMovies.isPending}
          onClick={() => runAction(refreshMovies, '✅ Biblioteca de películas refrescada')}
        >
          🔄 Refrescar Películas
        </Button>
        <Button
          variant="light"
          loading={refreshTv.isPending}
          onClick={() => runAction(refreshTv, '✅ Biblioteca de series refrescada')}
        >
          🔄 Refrescar Series
        </Button>
        <Button
          variant="light"
          loading={refreshAll.isPending}
          onClick={() => runAction(refreshAll, '✅ Todas las bibliotecas refrescadas vía API')}
        >
          🚀 Refrescar Todas (API)
        </Button>
        <Button
          variant="subtle"
          loading={serverInfo.isPending}
          onClick={() =>
            serverInfo.mutate(undefined, {
              onError: (e) => notifications.show({ color: 'red', message: `❌ ${(e as Error).message}` }),
            })
          }
        >
          ℹ️ Info del Servidor
        </Button>
      </Group>
      {serverInfo.data && <Code block>{JSON.stringify(serverInfo.data, null, 2)}</Code>}
    </Stack>
  )
}
