import { useEffect, useState } from 'react'
import {
  Accordion,
  Alert,
  Badge,
  Button,
  Group,
  Loader,
  Paper,
  Progress,
  Select,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconInfoCircle, IconRobot } from '@tabler/icons-react'
import { RecentPathInput } from '../../components/RecentPathInput'
import { FramePreview } from '../../components/FramePreview'
import { useJobProgress } from '../../api/ws'
import { api } from '../../api/client'
import { useAiNamingQuery } from '../settings/useSettings'
import {
  useLoadOrphansScan,
  useRenameOrphan,
  useRenameOrphansBatch,
  useSaveOrphansScan,
  useSavedOrphanScans,
  useScanOrphans,
  useSuggestOrphanName,
  useSuggestOrphansBatch,
} from './useOrphans'
import type { OrphanItem, ScanResult, SuggestBatchResult } from './types'

const PAGE_SIZE = 15
const SCOPES = [20, 50, 100, 500]

function gb(bytes: number) {
  return (bytes / 1024 ** 3).toFixed(2)
}

function stem(nombre: string) {
  const i = nombre.lastIndexOf('.')
  return i > 0 ? nombre.slice(0, i) : nombre
}

interface RowUi {
  nuevoNombre: string
  showPlayer: boolean
}

export function OrphansPage() {
  const { data: aiNaming } = useAiNamingQuery()

  const [folder, setFolder] = useState('')
  const [items, setItems] = useState<OrphanItem[]>([])
  const [totalEscaneados, setTotalEscaneados] = useState<number | null>(null)
  const [sugeridos, setSugeridos] = useState<Record<string, string | null>>({})
  const [rowUi, setRowUi] = useState<Record<string, RowUi>>({})
  const [page, setPage] = useState(0)
  const [scope, setScope] = useState<number>(50)

  const [scanJobId, setScanJobId] = useState<string | null>(null)
  const [suggestJobId, setSuggestJobId] = useState<string | null>(null)

  const scan = useScanOrphans()
  const suggestSingle = useSuggestOrphanName()
  const suggestBatch = useSuggestOrphansBatch()
  const rename = useRenameOrphan()
  const renameBatch = useRenameOrphansBatch()
  const saveScan = useSaveOrphansScan()
  const loadScan = useLoadOrphansScan()

  const [showSaved, setShowSaved] = useState(false)
  const { data: savedScans, isLoading: loadingSaved } = useSavedOrphanScans(showSaved)

  const scanState = useJobProgress<ScanResult>(scanJobId)
  const suggestState = useJobProgress<SuggestBatchResult, { archivo: string; sugerido: string | null }>(
    suggestJobId,
    (item) => setSugeridos((prev) => ({ ...prev, [item.archivo]: item.sugerido })),
  )

  useEffect(() => {
    if (scanState?.status === 'done' && scanState.result) {
      setItems(scanState.result.items)
      setTotalEscaneados(scanState.result.total_escaneados)
      setPage(0)
      setScanJobId(null)
      notifications.show({
        color: 'green',
        message: `✅ ${scanState.result.items.length} huérfano(s) de ${scanState.result.total_escaneados} archivo(s) escaneados`,
      })
    } else if (scanState?.status === 'error') {
      notifications.show({ color: 'red', message: `⚠️ ${scanState.error}` })
      setScanJobId(null)
    }
  }, [scanState])

  useEffect(() => {
    if (suggestState?.status === 'done' && suggestState.result) {
      const r = suggestState.result
      notifications.show({ color: 'green', message: `✅ ${r.sugeridos} sugerencia(s), ${r.sin_sugerencia} sin sugerencia` })
      setSuggestJobId(null)
    } else if (suggestState?.status === 'cancelled') {
      notifications.show({ color: 'gray', message: '🛑 Sugerencia en lote detenida' })
      setSuggestJobId(null)
    } else if (suggestState?.status === 'error') {
      notifications.show({ color: 'red', message: `⚠️ ${suggestState.error}` })
      setSuggestJobId(null)
    }
  }, [suggestState])

  const getRowUi = (item: OrphanItem): RowUi => rowUi[item.archivo] ?? { nuevoNombre: stem(item.nombre), showPlayer: false }
  const setRow = (item: OrphanItem, patch: Partial<RowUi>) =>
    setRowUi((prev) => ({ ...prev, [item.archivo]: { ...getRowUi(item), ...patch } }))

  const onEscanear = () => {
    if (!folder) return
    scan.mutate(folder, {
      onSuccess: (data) => setScanJobId(data.job_id),
      onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }),
    })
  }

  const onSugerirLote = () => {
    const pendientes = items.filter((i) => !i.renombrado)
    suggestBatch.mutate(
      { items: pendientes.map((i) => ({ archivo: i.archivo, nombre: i.nombre })), scope },
      {
        onSuccess: (data) => setSuggestJobId(data.job_id),
        onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }),
      },
    )
  }

  const onDetenerLote = () => {
    if (suggestJobId) api.post(`/jobs/${suggestJobId}/cancel`)
  }

  const onRenombrar = (item: OrphanItem) => {
    const nuevoNombre = getRowUi(item).nuevoNombre.trim()
    if (!nuevoNombre) return
    rename.mutate(
      { archivo: item.archivo, nuevo_nombre: nuevoNombre },
      {
        onSuccess: (updated) => {
          setItems((prev) => prev.map((i) => (i.archivo === item.archivo ? updated : i)))
          notifications.show({ color: 'green', message: `✅ Renombrado a ${updated.nombre}` })
        },
        onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }),
      },
    )
  }

  const aplicarTodasLasSugerencias = () => {
    const candidatos = items.filter((i) => !i.renombrado && sugeridos[i.archivo])
    if (!candidatos.length) {
      notifications.show({ color: 'gray', message: 'No hay sugerencias pendientes de aplicar' })
      return
    }
    renameBatch.mutate(
      candidatos.map((i) => ({ archivo: i.archivo, nuevo_nombre: sugeridos[i.archivo] as string })),
      {
        onSuccess: (result) => {
          notifications.show({ color: 'green', message: `✅ ${result.renombrados} renombrado(s)` })
          if (result.errores.length) notifications.show({ color: 'red', message: result.errores.join('; ') })
          setItems((prev) =>
            prev.map((i) => {
              if (!sugeridos[i.archivo] || i.renombrado) return i
              const stemNuevo = sugeridos[i.archivo] as string
              return { ...i, renombrado: true, nombre: `${stemNuevo}${i.nombre.slice(i.nombre.lastIndexOf('.'))}` }
            }),
          )
        },
      },
    )
  }

  const onGuardar = () => {
    saveScan.mutate(
      { folder, items },
      { onSuccess: () => notifications.show({ color: 'green', message: '💾 Progreso guardado' }) },
    )
  }

  const onCargar = (file_path: string) => {
    loadScan.mutate(file_path, {
      onSuccess: (result) => {
        setItems(result.items)
        setTotalEscaneados(null)
        setPage(0)
        setShowSaved(false)
        notifications.show({
          color: 'green',
          message: `📂 ${result.items.length} cargado(s) (${result.no_existentes} ya no existen, ${result.ya_renombrados} ya renombrados)`,
        })
      },
    })
  }

  const scanRunning = !!scanJobId && scanState?.status === 'running'
  const suggestRunning = !!suggestJobId && suggestState?.status === 'running'
  const pendientes = items.filter((i) => !i.renombrado)
  const totalPaginas = Math.ceil(pendientes.length / PAGE_SIZE) || 1
  const pageItems = pendientes.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE)
  const renombrados = items.filter((i) => i.renombrado)

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>🔍 Huérfanos</Title>
        <Text c="dimmed">
          Archivos en disco que no aparecen en Plex. Escanea una carpeta, pídele nombre a la IA
          (uno a uno o en lote) y renombra — Plex se refresca solo al terminar.
        </Text>
      </div>

      <Paper withBorder p="md" radius="md">
        <Stack gap="sm">
          <RecentPathInput label="Carpeta a escanear" category="huerfanos" value={folder} onChange={setFolder} />
          <Group>
            <Button loading={scan.isPending || scanRunning} disabled={!folder} onClick={onEscanear}>
              🔍 Escanear
            </Button>
            <Button variant="default" onClick={() => setShowSaved((v) => !v)}>
              📂 Cargar guardado
            </Button>
          </Group>
          {scanJobId && (
            <div>
              <Progress value={scanState?.percent ?? 0} animated={scanRunning} />
              <Text size="sm" c="dimmed" mt={4}>
                {scanState?.message}
              </Text>
            </div>
          )}
          {showSaved && (
            <div>
              {loadingSaved ? (
                <Loader size="sm" />
              ) : !savedScans?.length ? (
                <Text size="sm" c="dimmed">
                  No hay escaneos guardados todavía.
                </Text>
              ) : (
                <Stack gap={4}>
                  {savedScans.map((s) => (
                    <Group key={s.file_path} justify="space-between">
                      <Text size="sm">
                        {s.scan_path} — {s.total_pairs} huérfano(s) — {s.scan_date}
                      </Text>
                      <Button size="xs" variant="light" loading={loadScan.isPending} onClick={() => onCargar(s.file_path)}>
                        Cargar
                      </Button>
                    </Group>
                  ))}
                </Stack>
              )}
            </div>
          )}
        </Stack>
      </Paper>

      {totalEscaneados !== null && items.length === 0 && (
        <Alert color="green" icon={<IconInfoCircle />}>
          ✅ Los {totalEscaneados} archivo(s) escaneados están indexados en Plex — ningún huérfano.
        </Alert>
      )}

      {items.length > 0 && (
        <>
          <Group justify="space-between">
            <Text size="sm" c="dimmed">
              {totalEscaneados !== null && `${totalEscaneados} archivo(s) escaneados — `}
              {pendientes.length} pendiente(s), {renombrados.length} ya renombrado(s)
            </Text>
            <Button size="xs" variant="default" onClick={onGuardar} loading={saveScan.isPending}>
              💾 Guardar progreso
            </Button>
          </Group>

          {!aiNaming?.enabled ? (
            <Alert color="blue" icon={<IconInfoCircle />}>
              La sugerencia de nombres con IA está desactivada — actívala en{' '}
              <strong>⚙️ Configuración → 🤖 IA</strong> para usarla aquí.
            </Alert>
          ) : (
            <Paper withBorder p="md" radius="md">
              <Group justify="space-between" wrap="wrap">
                <Group>
                  <Select
                    label="Cuántos"
                    data={[...SCOPES.map(String), 'Todos']}
                    value={scope === pendientes.length ? 'Todos' : String(scope)}
                    onChange={(v) => setScope(v === 'Todos' ? pendientes.length : Number(v))}
                    w={110}
                  />
                  <Button
                    mt={22}
                    leftSection={<IconRobot size={16} />}
                    loading={suggestBatch.isPending || suggestRunning}
                    disabled={!pendientes.length}
                    onClick={onSugerirLote}
                  >
                    Sugerir nombres en lote
                  </Button>
                  {suggestRunning && (
                    <Button mt={22} color="red" variant="light" onClick={onDetenerLote}>
                      🛑 Detener
                    </Button>
                  )}
                </Group>
                <Button mt={22} variant="light" color="blue" onClick={aplicarTodasLasSugerencias} disabled={renameBatch.isPending}>
                  ✅ Aplicar todas las sugerencias ({Object.values(sugeridos).filter(Boolean).length})
                </Button>
              </Group>
              {suggestJobId && (
                <div>
                  <Progress value={suggestState?.percent ?? 0} animated={suggestRunning} mt="sm" />
                  <Text size="sm" c="dimmed" mt={4}>
                    {suggestState?.message}
                  </Text>
                </div>
              )}
            </Paper>
          )}

          {totalPaginas > 1 && (
            <Text size="sm" c="dimmed">
              Mostrando {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, pendientes.length)} de {pendientes.length}
            </Text>
          )}

          <Stack gap="sm">
            {pageItems.map((item) => {
              const ui = getRowUi(item)
              const sugerido = sugeridos[item.archivo]
              return (
                <Paper key={item.archivo} withBorder p="md" radius="md">
                  <Stack gap="xs">
                    <Text fw={500}>{item.nombre}</Text>
                    <Text size="xs" c="dimmed">
                      {item.archivo}
                    </Text>
                    <Text size="sm">📊 {gb(item.tamaño)} GB</Text>
                    {sugerido && (
                      <Badge color="blue" variant="light" style={{ alignSelf: 'flex-start' }}>
                        🤖 {sugerido}
                      </Badge>
                    )}
                    <Group wrap="wrap">
                      <TextInput
                        label="Nuevo nombre (sin extensión)"
                        value={ui.nuevoNombre}
                        onChange={(e) => setRow(item,{ nuevoNombre: e.currentTarget.value })}
                        w={280}
                      />
                      <Stack gap={4} mt={22}>
                        <Group gap="xs">
                          <Button size="xs" loading={rename.isPending} onClick={() => onRenombrar(item)}>
                            ✏️ Renombrar
                          </Button>
                          <Button
                            size="xs"
                            variant="default"
                            loading={suggestSingle.isPending}
                            onClick={() =>
                              suggestSingle.mutate(item.nombre, {
                                onSuccess: (r) => {
                                  setSugeridos((prev) => ({ ...prev, [item.archivo]: r.sugerido }))
                                  if (r.sugerido) setRow(item,{ nuevoNombre: r.sugerido })
                                },
                              })
                            }
                          >
                            🤖 Sugerir
                          </Button>
                          <Button size="xs" variant="subtle" onClick={() => setRow(item,{ showPlayer: !ui.showPlayer })}>
                            {ui.showPlayer ? '🙈 Ocultar' : '🎥 Fotograma'}
                          </Button>
                        </Group>
                      </Stack>
                    </Group>
                    {ui.showPlayer && <FramePreview archivo={item.archivo} />}
                  </Stack>
                </Paper>
              )
            })}
          </Stack>

          {totalPaginas > 1 && (
            <Group justify="center">
              <Button size="xs" variant="default" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                ◀ Anterior
              </Button>
              <Text size="sm">
                {page + 1} / {totalPaginas}
              </Text>
              <Button size="xs" variant="default" disabled={page >= totalPaginas - 1} onClick={() => setPage((p) => p + 1)}>
                Siguiente ▶
              </Button>
            </Group>
          )}

          {renombrados.length > 0 && (
            <Accordion variant="contained">
              <Accordion.Item value="renombrados">
                <Accordion.Control>✅ Ya renombrados ({renombrados.length})</Accordion.Control>
                <Accordion.Panel>
                  <Stack gap={4}>
                    {renombrados.map((item) => (
                      <Text size="sm" key={item.archivo}>
                        {item.nombre}
                      </Text>
                    ))}
                  </Stack>
                </Accordion.Panel>
              </Accordion.Item>
            </Accordion>
          )}
        </>
      )}
    </Stack>
  )
}
