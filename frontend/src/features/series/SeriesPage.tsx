import { useEffect, useState } from 'react'
import {
  Accordion,
  Alert,
  Button,
  Checkbox,
  Group,
  Loader,
  Paper,
  Progress,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconInfoCircle } from '@tabler/icons-react'
import { RecentPathInput } from '../../components/RecentPathInput'
import { useJobProgress } from '../../api/ws'
import { usePlexAction, usePlexQuery } from '../settings/useSettings'
import {
  useIgnoreSeries,
  useIgnoredSeriesQuery,
  useLoadSeriesScan,
  useMoveEpisode,
  useMoveEpisodesBatch,
  useRenameSeriesOrphan,
  useSaveSeriesScan,
  useSavedSeriesScans,
  useScanSeries,
  useUnignoreSeries,
} from './useSeries'
import type { EpisodeItem, ScanResult, SeriesGroup } from './types'

const PAGE_SIZE = 20

function gb(bytes: number) {
  return (bytes / 1024 ** 3).toFixed(2)
}

function stem(nombre: string) {
  const i = nombre.lastIndexOf('.')
  return i > 0 ? nombre.slice(0, i) : nombre
}

export function SeriesPage() {
  const { data: plex } = usePlexQuery()

  const [folder, setFolder] = useState('')
  const [duplicados, setDuplicados] = useState<EpisodeItem[][]>([])
  const [huerfanos, setHuerfanos] = useState<EpisodeItem[]>([])
  const [seriesSinIndexar, setSeriesSinIndexar] = useState<SeriesGroup[]>([])
  const [totalEpisodios, setTotalEpisodios] = useState<number | null>(null)
  const [sinReconocer, setSinReconocer] = useState(0)

  const [selectedDup, setSelectedDup] = useState<Set<string>>(new Set())
  const [rowUi, setRowUi] = useState<Record<string, string>>({})
  const [page, setPage] = useState(0)

  const [scanJobId, setScanJobId] = useState<string | null>(null)
  const [showSaved, setShowSaved] = useState(false)

  const scan = useScanSeries()
  const moveEpisode = useMoveEpisode()
  const moveBatch = useMoveEpisodesBatch()
  const rename = useRenameSeriesOrphan()
  const saveScan = useSaveSeriesScan()
  const loadScan = useLoadSeriesScan()
  const { data: ignored } = useIgnoredSeriesQuery()
  const ignoreSeries = useIgnoreSeries()
  const unignoreSeries = useUnignoreSeries()
  const refreshTv = usePlexAction('refresh-tv')

  const { data: savedScans, isLoading: loadingSaved } = useSavedSeriesScans(showSaved)

  const scanState = useJobProgress<ScanResult>(scanJobId)

  useEffect(() => {
    if (scanState?.status === 'done' && scanState.result) {
      const r = scanState.result
      setDuplicados(r.duplicados)
      setHuerfanos(r.huerfanos)
      setSeriesSinIndexar(r.series_sin_indexar)
      setTotalEpisodios(r.total_episodios)
      setSinReconocer(r.sin_reconocer)
      setPage(0)
      setScanJobId(null)
      notifications.show({
        color: 'green',
        message: `✅ ${r.total_episodios} episodio(s) — ${r.duplicados.length} duplicados, ${r.huerfanos.length} sin indexar, ${r.series_sin_indexar.length} serie(s) sin indexar en absoluto`,
      })
    } else if (scanState?.status === 'error') {
      notifications.show({ color: 'red', message: `⚠️ ${scanState.error}` })
      setScanJobId(null)
    }
  }, [scanState])

  const scanRunning = !!scanJobId && scanState?.status === 'running'

  const onEscanear = () => {
    if (!folder) return
    scan.mutate(folder, {
      onSuccess: (data) => setScanJobId(data.job_id),
      onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }),
    })
  }

  const onMoverSeleccionados = () => {
    if (!selectedDup.size) return
    moveBatch.mutate([...selectedDup], {
      onSuccess: (result) => {
        notifications.show({ color: 'green', message: `✅ ${result.movidos} episodio(s) movido(s) a debug` })
        if (result.errores.length) notifications.show({ color: 'red', message: result.errores.join('; ') })
        setDuplicados((prev) =>
          prev.map((g) => g.filter((ep) => !selectedDup.has(ep.archivo))).filter((g) => g.length > 1),
        )
        setSelectedDup(new Set())
      },
    })
  }

  const onMoverUno = (archivo: string, gi: number) => {
    moveEpisode.mutate(archivo, {
      onSuccess: (result) => {
        if (result.movidos) {
          notifications.show({ color: 'green', message: '✅ Movido a debug' })
          setSelectedDup((prev) => {
            const next = new Set(prev)
            next.delete(archivo)
            return next
          })
          setDuplicados((prev) => {
            const next = [...prev]
            const nuevoGrupo = next[gi].filter((ep) => ep.archivo !== archivo)
            if (nuevoGrupo.length > 1) next[gi] = nuevoGrupo
            else next.splice(gi, 1)
            return next
          })
        } else {
          notifications.show({ color: 'red', message: result.errores.join('; ') })
        }
      },
    })
  }

  const onRenombrar = (ep: EpisodeItem) => {
    const nuevoNombre = (rowUi[ep.archivo] ?? stem(ep.nombre)).trim()
    if (!nuevoNombre) return
    rename.mutate(
      { archivo: ep.archivo, nuevo_nombre: nuevoNombre },
      {
        onSuccess: (updated) => {
          setHuerfanos((prev) => prev.map((e) => (e.archivo === ep.archivo ? { ...e, ...updated } : e)))
          notifications.show({ color: 'green', message: `✅ Renombrado a ${updated.nombre}` })
        },
        onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }),
      },
    )
  }

  const onIgnorar = (clave: string) => {
    ignoreSeries.mutate(clave, {
      onSuccess: () => setSeriesSinIndexar((prev) => prev.filter((s) => s.clave !== clave)),
    })
  }

  const onGuardar = () => {
    saveScan.mutate(
      { folder, duplicados, huerfanos, series_sin_indexar: seriesSinIndexar },
      { onSuccess: () => notifications.show({ color: 'green', message: '💾 Progreso guardado' }) },
    )
  }

  const onCargar = (file_path: string) => {
    loadScan.mutate(file_path, {
      onSuccess: (result) => {
        setDuplicados(result.duplicados)
        setHuerfanos(result.huerfanos)
        setSeriesSinIndexar(result.series_sin_indexar)
        setTotalEpisodios(null)
        setPage(0)
        setShowSaved(false)
        notifications.show({
          color: 'green',
          message: `📂 Cargado (${result.total_caidos} de ${result.total_guardado} ya no existen y se han quitado)`,
        })
      },
    })
  }

  const grupos = Object.entries(
    huerfanos.reduce<Record<string, EpisodeItem[]>>((acc, ep) => {
      ;(acc[ep.serie_normalizada] ??= []).push(ep)
      return acc
    }, {}),
  ).sort(([, a], [, b]) => b.reduce((s, e) => s + e.tamaño, 0) - a.reduce((s, e) => s + e.tamaño, 0))
  const totalPaginas = Math.ceil(grupos.length / PAGE_SIZE) || 1
  const gruposPagina = grupos.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE)

  const hayResultados = totalEpisodios !== null || duplicados.length > 0 || huerfanos.length > 0 || seriesSinIndexar.length > 0

  if (plex && !plex.is_configured) {
    return (
      <Stack gap="md">
        <Title order={2}>📺 Series</Title>
        <Alert color="yellow" icon={<IconInfoCircle />}>
          Plex no está configurado — configura la ruta de la base de datos en{' '}
          <strong>⚙️ Configuración → 🎬 Plex</strong> antes de buscar.
        </Alert>
      </Stack>
    )
  }

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>📺 Series</Title>
        <Text c="dimmed">
          Episodios duplicados (por temporada+número, no por título), capítulos sueltos sin indexar
          en Plex, y series enteras de las que Plex no tiene ni el nombre.
        </Text>
      </div>

      <Paper withBorder p="md" radius="md">
        <Stack gap="sm">
          <RecentPathInput label="Carpeta de series a analizar" category="series" value={folder} onChange={setFolder} />
          <Group>
            <Button loading={scan.isPending || scanRunning} disabled={!folder} onClick={onEscanear}>
              🔍 Buscar
            </Button>
            <Button variant="default" onClick={() => setShowSaved((v) => !v)}>
              📂 Cargar guardado
            </Button>
            {hayResultados && (
              <Button variant="default" onClick={onGuardar} loading={saveScan.isPending}>
                💾 Guardar
              </Button>
            )}
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
                  No hay series guardadas todavía.
                </Text>
              ) : (
                <Stack gap={4}>
                  {savedScans.map((s) => (
                    <Group key={s.file_path} justify="space-between">
                      <Text size="sm">
                        {s.scan_path} — {s.total_pairs} elemento(s) — {s.scan_date}
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

      {hayResultados && (
        <>
          {sinReconocer > 0 && (
            <Text size="sm" c="dimmed">
              ℹ️ {sinReconocer} archivo(s) de vídeo no tenían un patrón de episodio reconocible y se ignoraron
            </Text>
          )}

          {/* --- Episodios duplicados --- */}
          <div>
            <Title order={4} mb="xs">
              🔁 {duplicados.length} episodio(s) duplicado(s)
            </Title>
            {!duplicados.length ? (
              <Text c="dimmed" size="sm">
                Ninguno detectado.
              </Text>
            ) : (
              <Stack gap="sm">
                <Group>
                  <Button
                    size="xs"
                    color="red"
                    disabled={!selectedDup.size}
                    loading={moveBatch.isPending}
                    onClick={onMoverSeleccionados}
                  >
                    🗑️ Mover {selectedDup.size} seleccionado(s) a debug
                  </Button>
                </Group>
                {duplicados.map((grupo, gi) => (
                  <Paper key={gi} withBorder p="sm" radius="md">
                    <Text fw={500} mb="xs">
                      {grupo[0].serie} — T{String(grupo[0].temporada).padStart(2, '0')}E
                      {String(grupo[0].episodio).padStart(2, '0')} ({grupo.length} copias)
                    </Text>
                    <Stack gap={4}>
                      {grupo.map((ep) => (
                        <Group key={ep.archivo} justify="space-between" wrap="nowrap">
                          <Group wrap="nowrap" gap="xs">
                            <Checkbox
                              checked={selectedDup.has(ep.archivo)}
                              onChange={(e) => {
                                const checked = e.currentTarget.checked
                                setSelectedDup((prev) => {
                                  const next = new Set(prev)
                                  if (checked) next.add(ep.archivo)
                                  else next.delete(ep.archivo)
                                  return next
                                })
                              }}
                            />
                            <div>
                              <Text size="sm">📄 {ep.nombre}</Text>
                              <Text size="xs" c="dimmed">
                                {gb(ep.tamaño)} GB — {ep.carpeta}
                              </Text>
                            </div>
                          </Group>
                          <Button size="xs" variant="light" color="red" onClick={() => onMoverUno(ep.archivo, gi)}>
                            🗑️ Mover a debug
                          </Button>
                        </Group>
                      ))}
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            )}
          </div>

          {/* --- Capítulos sueltos sin indexar --- */}
          <div>
            <Title order={4} mb="xs">
              🧩 {huerfanos.length} capítulo(s) sin indexar en Plex
            </Title>
            {!huerfanos.length ? (
              <Text c="dimmed" size="sm">
                Ninguno detectado.
              </Text>
            ) : (
              <Stack gap="sm">
                {totalPaginas > 1 && (
                  <Text size="sm" c="dimmed">
                    Mostrando series {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, grupos.length)} de {grupos.length}
                  </Text>
                )}
                <Accordion variant="contained">
                  {gruposPagina.map(([clave, episodios]) => {
                    const tam = episodios.reduce((s, e) => s + e.tamaño, 0)
                    return (
                      <Accordion.Item key={clave} value={clave}>
                        <Accordion.Control>
                          📁 {episodios[0].serie} — {episodios.length} capítulo(s), {gb(tam)} GB
                        </Accordion.Control>
                        <Accordion.Panel>
                          <Stack gap="sm">
                            {episodios.map((ep) => (
                              <Paper key={ep.archivo} withBorder p="sm" radius="md">
                                <Group justify="space-between" wrap="wrap">
                                  <div>
                                    <Text fw={500} size="sm">
                                      {ep.nombre}
                                    </Text>
                                    <Text size="xs" c="dimmed">
                                      T{String(ep.temporada).padStart(2, '0')}E{String(ep.episodio).padStart(2, '0')} —{' '}
                                      {ep.archivo}
                                    </Text>
                                    <Text size="xs">📊 {gb(ep.tamaño)} GB</Text>
                                  </div>
                                  <Group gap="xs">
                                    <TextInput
                                      size="xs"
                                      placeholder="Nuevo nombre (sin extensión)"
                                      value={rowUi[ep.archivo] ?? stem(ep.nombre)}
                                      onChange={(e) => {
                                        const value = e.currentTarget.value
                                        setRowUi((prev) => ({ ...prev, [ep.archivo]: value }))
                                      }}
                                      w={220}
                                    />
                                    <Button size="xs" loading={rename.isPending} onClick={() => onRenombrar(ep)}>
                                      ✏️ Renombrar
                                    </Button>
                                  </Group>
                                </Group>
                              </Paper>
                            ))}
                          </Stack>
                        </Accordion.Panel>
                      </Accordion.Item>
                    )
                  })}
                </Accordion>
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
              </Stack>
            )}
          </div>

          {/* --- Series enteras sin indexar --- */}
          <div>
            <Title order={4} mb="xs">
              📭 {seriesSinIndexar.length} serie(s) sin indexar en absoluto
            </Title>
            {!seriesSinIndexar.length ? (
              <Text c="dimmed" size="sm">
                Ninguna detectada.
              </Text>
            ) : (
              <Stack gap="sm">
                <Text size="sm" c="dimmed">
                  Plex no tiene ni el nombre de estas series. Si sabes que alguna sí está bien (con
                  otro nombre que no reconocemos), puedes ignorarla.
                </Text>
                <Accordion variant="contained">
                  {seriesSinIndexar.map((s) => (
                    <Accordion.Item key={s.clave} value={s.clave}>
                      <Accordion.Control>
                        📁 {s.serie} — {s.episodios.length} episodio(s), {gb(s.tamaño)} GB
                      </Accordion.Control>
                      <Accordion.Panel>
                        <Stack gap={4}>
                          {s.episodios.map((ep) => (
                            <Text size="sm" key={ep.archivo}>
                              📄 T{String(ep.temporada).padStart(2, '0')}E{String(ep.episodio).padStart(2, '0')} —{' '}
                              {ep.nombre} ({gb(ep.tamaño)} GB)
                            </Text>
                          ))}
                          <Button size="xs" variant="light" mt="xs" onClick={() => onIgnorar(s.clave)} loading={ignoreSeries.isPending}>
                            🙈 Ignorar esta serie
                          </Button>
                        </Stack>
                      </Accordion.Panel>
                    </Accordion.Item>
                  ))}
                </Accordion>
                <Group>
                  <Button
                    size="xs"
                    variant="default"
                    loading={refreshTv.isPending}
                    onClick={() =>
                      refreshTv.mutate(undefined, {
                        onSuccess: () => notifications.show({ color: 'green', message: '🔄 Biblioteca de series refrescada' }),
                      })
                    }
                  >
                    🔄 Refrescar biblioteca de series en Plex
                  </Button>
                </Group>
              </Stack>
            )}
          </div>

          {!!ignored?.claves.length && (
            <Accordion variant="contained">
              <Accordion.Item value="ignoradas">
                <Accordion.Control>⚙️ Series ignoradas ({ignored.claves.length})</Accordion.Control>
                <Accordion.Panel>
                  <Stack gap={4}>
                    {ignored.claves.map((clave) => (
                      <Group key={clave} justify="space-between">
                        <Text size="sm">{clave}</Text>
                        <Button size="xs" variant="subtle" onClick={() => unignoreSeries.mutate(clave)}>
                          ↩️ Quitar
                        </Button>
                      </Group>
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
