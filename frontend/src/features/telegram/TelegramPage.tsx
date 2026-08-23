import { useEffect, useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  Checkbox,
  Group,
  Loader,
  Paper,
  Progress,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconInfoCircle } from '@tabler/icons-react'
import { RecentPathInput } from '../../components/RecentPathInput'
import { useJobProgress } from '../../api/ws'
import {
  useScanTelegramFolder,
  useTelegramStatusQuery,
  useTelegramTestConnection,
  useTelegramTestMessage,
  useUploadToTelegram,
} from './useTelegram'
import type { UploadItemResult, UploadResult, VideoItem } from './types'

const TELETHON_MAX_MB = 1500

export function TelegramPage() {
  const { data: status, isLoading: loadingStatus } = useTelegramStatusQuery()
  const testConnection = useTelegramTestConnection()
  const testMessage = useTelegramTestMessage()
  const scan = useScanTelegramFolder()
  const upload = useUploadToTelegram()

  const [folder, setFolder] = useState('')
  const [videos, setVideos] = useState<VideoItem[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [enrich, setEnrich] = useState(true)
  const [uploadJobId, setUploadJobId] = useState<string | null>(null)
  const [itemResults, setItemResults] = useState<UploadItemResult[]>([])

  const uploadState = useJobProgress<UploadResult, UploadItemResult>(uploadJobId, (item) =>
    setItemResults((prev) => [...prev, item]),
  )

  useEffect(() => {
    if (uploadState?.status === 'done' && uploadState.result) {
      const r = uploadState.result
      notifications.show({ color: 'green', message: `✅ ${r.subidos} subido(s), ${r.fallidos} fallido(s)` })
      setUploadJobId(null)
    } else if (uploadState?.status === 'error') {
      notifications.show({ color: 'red', message: `⚠️ ${uploadState.error}` })
      setUploadJobId(null)
    }
  }, [uploadState])

  const uploading = !!uploadJobId && uploadState?.status === 'running'

  const onEscanear = () => {
    if (!folder) return
    scan.mutate(folder, {
      onSuccess: (data) => {
        setVideos(data.videos)
        setSelected(new Set())
        notifications.show({ color: 'green', message: `✅ ${data.videos.length} vídeo(s) encontrado(s)` })
      },
      onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }),
    })
  }

  const onSubir = () => {
    const elegidos = videos.filter((v) => selected.has(v.path))
    if (!elegidos.length) return
    setItemResults([])
    upload.mutate(
      { videos: elegidos, enrich },
      {
        onSuccess: (data) => setUploadJobId(data.job_id),
        onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }),
      },
    )
  }

  if (loadingStatus) return <Loader />

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>📱 Telegram</Title>
        <Text c="dimmed">
          Sube vídeos de una carpeta al canal de Telegram configurado. Con "Enriquecer" activado,
          busca título, póster y sinopsis (Plex + OMDb) y los manda antes de cada vídeo.
        </Text>
      </div>

      <Paper withBorder p="md" radius="md">
        <Stack gap="sm">
          <Group>
            <Text size="sm">Bot API:</Text>
            <Badge color={status?.bot_configured ? 'green' : 'red'} variant="light">
              {status?.bot_configured ? 'Configurado' : 'No configurado'}
            </Badge>
            <Text size="sm">Telethon (subida de vídeo):</Text>
            <Badge color={status?.telethon_configured ? 'green' : 'red'} variant="light">
              {status?.telethon_configured ? 'Configurado' : 'No configurado'}
            </Badge>
            <Text size="sm">Info de películas:</Text>
            <Badge color={status?.movie_info_available ? 'green' : 'gray'} variant="light">
              {status?.movie_info_available ? 'Disponible (Plex)' : 'No disponible'}
            </Badge>
          </Group>
          {(!status?.bot_configured || !status?.telethon_configured) && (
            <Alert color="yellow" icon={<IconInfoCircle />}>
              Configura TELEGRAM_BOT_TOKEN/TELEGRAM_CHANNEL_ID (mensajes) y
              TELEGRAM_API_ID/API_HASH/PHONE (subida de vídeo) en .env.
            </Alert>
          )}
          <Group>
            <Button
              size="xs"
              variant="default"
              loading={testConnection.isPending}
              onClick={() =>
                testConnection.mutate(undefined, {
                  onSuccess: (r) => notifications.show({ color: r.ok ? 'green' : 'red', message: r.ok ? '✅ Conexión OK' : `❌ ${r.detail}` }),
                })
              }
            >
              🔍 Probar conexión
            </Button>
            <Button
              size="xs"
              variant="default"
              disabled={!status?.bot_configured}
              loading={testMessage.isPending}
              onClick={() =>
                testMessage.mutate(undefined, {
                  onSuccess: (r) => notifications.show({ color: r.ok ? 'green' : 'red', message: r.ok ? '✅ Mensaje enviado' : `❌ ${r.detail}` }),
                })
              }
            >
              📤 Enviar mensaje de prueba
            </Button>
          </Group>
        </Stack>
      </Paper>

      <Paper withBorder p="md" radius="md">
        <Stack gap="sm">
          <RecentPathInput label="Carpeta con vídeos a subir" category="telegram" value={folder} onChange={setFolder} />
          <Group>
            <Button loading={scan.isPending} disabled={!folder} onClick={onEscanear}>
              🔍 Escanear carpeta
            </Button>
          </Group>
        </Stack>
      </Paper>

      {videos.length > 0 && (
        <Paper withBorder p="md" radius="md">
          <Stack gap="sm">
            <Group justify="space-between">
              <Title order={4}>🎬 {videos.length} vídeo(s) encontrado(s)</Title>
              <Group gap="xs">
                <Button size="xs" variant="default" onClick={() => setSelected(new Set(videos.map((v) => v.path)))}>
                  ✅ Seleccionar todos
                </Button>
                <Button size="xs" variant="default" onClick={() => setSelected(new Set())}>
                  ❌ Deseleccionar todos
                </Button>
              </Group>
            </Group>

            <div style={{ overflowX: 'auto' }}>
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th></Table.Th>
                    <Table.Th>Nombre</Table.Th>
                    <Table.Th>Tamaño</Table.Th>
                    <Table.Th></Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {videos.map((v) => (
                    <Table.Tr key={v.path}>
                      <Table.Td>
                        <Checkbox
                          checked={selected.has(v.path)}
                          onChange={(e) => {
                            setSelected((prev) => {
                              const next = new Set(prev)
                              if (e.currentTarget.checked) next.add(v.path)
                              else next.delete(v.path)
                              return next
                            })
                          }}
                        />
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{v.name}</Text>
                        <Text size="xs" c="dimmed">
                          {v.path}
                        </Text>
                      </Table.Td>
                      <Table.Td>{v.size_mb.toFixed(2)} MB</Table.Td>
                      <Table.Td>
                        {v.size_mb > TELETHON_MAX_MB ? (
                          <Badge color="red" variant="light">
                            Demasiado grande
                          </Badge>
                        ) : (
                          <Badge color="green" variant="light">
                            OK
                          </Badge>
                        )}
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </div>

            {selected.size > 0 && (
              <Stack gap="sm">
                <Checkbox
                  label="Enriquecer con información de película (título, póster, sinopsis) antes de cada vídeo"
                  checked={enrich}
                  onChange={(e) => setEnrich(e.currentTarget.checked)}
                  disabled={!status?.movie_info_available}
                />
                <Group>
                  <Button
                    loading={upload.isPending || uploading}
                    disabled={!status?.telethon_configured}
                    onClick={onSubir}
                  >
                    🚀 Subir {selected.size} vídeo(s) a Telegram
                  </Button>
                </Group>
              </Stack>
            )}

            {uploadJobId && (
              <div>
                <Progress value={uploadState?.percent ?? 0} animated={uploading} />
                <Text size="sm" c="dimmed" mt={4}>
                  {uploadState?.message}
                </Text>
              </div>
            )}

            {itemResults.length > 0 && (
              <Stack gap={4}>
                {itemResults.map((r) => (
                  <Group key={r.name} justify="space-between">
                    <Text size="sm">{r.success ? '✅' : '❌'} {r.name}</Text>
                    <Text size="xs" c="dimmed">
                      {r.info_found && '🎬 info '}
                      {r.poster_sent && '🖼️ póster '}
                      {r.error}
                    </Text>
                  </Group>
                ))}
              </Stack>
            )}
          </Stack>
        </Paper>
      )}
    </Stack>
  )
}
