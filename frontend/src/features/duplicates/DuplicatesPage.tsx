import { useEffect, useState } from 'react'
import {
  Accordion,
  Alert,
  Badge,
  Button,
  Checkbox,
  Group,
  Loader,
  Paper,
  Progress,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconInfoCircle } from '@tabler/icons-react'
import { RecentPathInput } from '../../components/RecentPathInput'
import { FramePreview } from '../../components/FramePreview'
import { VideoPlayer } from '../../components/VideoPlayer'
import { useJobProgress } from '../../api/ws'
import { usePlayersQuery, usePlexQuery } from '../settings/useSettings'
import {
  useBulkMoveDuplicates,
  useCheckHash,
  useCreateEdition,
  useDeleteDuplicates,
  useEditionSuggestions,
  useLoadDuplicatesScan,
  usePlexMetadataForPair,
  useSaveDuplicatesScan,
  useSavedDuplicatesScans,
  useScanDuplicates,
  useVideoInfo,
} from './useDuplicates'
import type { CheckHashResult, DuplicatePair, FileInfo, PlexMetadataResponse, ScanResult, VideoInfo } from './types'

function gb(bytes: number) {
  return (bytes / 1024 ** 3).toFixed(2)
}

function duracionEscaneoFmt(segundos: number) {
  if (!segundos) return null
  const h = Math.floor(segundos / 3600)
  const m = Math.floor((segundos % 3600) / 60)
  const s = Math.floor(segundos % 60)
  return `${h}h ${m}m ${s}s`
}

function stem(nombre: string) {
  const i = nombre.lastIndexOf('.')
  return i > 0 ? nombre.slice(0, i) : nombre
}

function carpeta(ruta: string) {
  // Admite tanto rutas POSIX (contenedor) como con "\" (UNC/Windows,
  // si algún día se vuelve a correr fuera de Docker)
  const i = Math.max(ruta.lastIndexOf('/'), ruta.lastIndexOf('\\'))
  return i > 0 ? ruta.slice(0, i) : ruta
}

function FileCard({
  info,
  otherCreado,
  selected,
  onSelect,
  onAddBasket,
  inBasket,
  plex,
  videoInfo,
  loadingVideoInfo,
  onCreateEdition,
  creatingEdition,
}: {
  info: FileInfo
  otherCreado: string | null
  selected: boolean
  onSelect: () => void
  onAddBasket: () => void
  inBasket: boolean
  plex?: { encontrado: boolean; datos: Record<string, unknown> | null }
  videoInfo?: VideoInfo
  loadingVideoInfo?: boolean
  onCreateEdition: (editionName: string) => void
  creatingEdition?: boolean
}) {
  const esMasNuevo = info.creado && otherCreado && info.creado > otherCreado
  const esMasViejo = info.creado && otherCreado && info.creado < otherCreado

  const duracionEnVivo = videoInfo?.duration_formatted && videoInfo.duration_formatted !== 'N/A' ? videoInfo.duration_formatted : null
  const duracion = duracionEnVivo ?? duracionEscaneoFmt(info.duracion) ?? 'N/A'

  const [editionOpen, setEditionOpen] = useState(false)
  const [editionName, setEditionName] = useState('')
  const movieTitle = (plex?.datos?.title as string | undefined) ?? stem(info.nombre)
  const suggestions = useEditionSuggestions(movieTitle, editionOpen)

  return (
    <Stack gap={4}>
      <Text fw={600}>{info.nombre}</Text>
      {!info.existe && (
        <Alert color="red" p={4}>
          Archivo no encontrado
        </Alert>
      )}
      <Text size="sm">📊 {gb(info.tamaño)} GB</Text>
      <Text size="sm">⏱️ {loadingVideoInfo ? 'calculando…' : duracion}</Text>
      <Text size="sm">
        🎞️ {loadingVideoInfo ? 'calculando…' : `${videoInfo?.resolution ?? 'N/A'} — ${videoInfo?.video_codec ?? 'N/A'}`}
      </Text>
      {videoInfo && (
        <Text size="xs" c="dimmed">
          🔊 {videoInfo.audio} · 📦 {videoInfo.container}
          {videoInfo.fps ? ` · ${videoInfo.fps} fps` : ''}
        </Text>
      )}
      <Text size="xs" c="dimmed">
        {info.ruta}
      </Text>
      {info.creado && (
        <Text size="xs">
          📅 {new Date(info.creado).toLocaleString()} {esMasNuevo && '🆕 más nuevo'} {esMasViejo && '📜 más viejo'}
        </Text>
      )}
      {plex && (
        <Text size="xs" c={plex.encontrado ? undefined : 'dimmed'}>
          {plex.encontrado
            ? `🎬 Plex: ${plex.datos?.title ?? 'N/A'} (${plex.datos?.year ?? 'N/A'}) — ${plex.datos?.studio ?? 'N/A'}`
            : '🔍 No encontrada en Plex'}
        </Text>
      )}
      <Group gap="xs">
        <Checkbox label="Seleccionar" checked={selected} onChange={onSelect} />
        <Button size="xs" variant={inBasket ? 'filled' : 'default'} onClick={onAddBasket} disabled={!info.existe}>
          {inBasket ? '🧺 En la cesta' : '➕ Añadir a la cesta'}
        </Button>
        <Button size="xs" variant="subtle" onClick={() => setEditionOpen((v) => !v)} disabled={!info.existe}>
          {editionOpen ? '🙈 Cancelar' : '🎬 Convertir en edición de Plex'}
        </Button>
      </Group>
      {editionOpen && (
        <Stack gap={4}>
          <Text size="xs" c="dimmed">
            Para cuando esto no es un duplicado real, sino otra versión (extendida, de director...) —
            renombra el archivo a la convención de Plex en vez de moverlo a debug.
          </Text>
          {!!suggestions.data?.sugerencias.length && (
            <Group gap={4} wrap="wrap">
              {suggestions.data.sugerencias.map((s) => (
                <Badge
                  key={s}
                  variant={editionName === s ? 'filled' : 'light'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => setEditionName(s)}
                >
                  {s}
                </Badge>
              ))}
            </Group>
          )}
          <Group gap="xs" wrap="nowrap">
            <TextInput
              size="xs"
              placeholder="Nombre de la edición (ej. Extended Cut)"
              value={editionName}
              onChange={(e) => setEditionName(e.currentTarget.value)}
              style={{ flex: 1 }}
            />
            <Button
              size="xs"
              loading={creatingEdition}
              disabled={!editionName.trim()}
              onClick={() => onCreateEdition(editionName.trim())}
            >
              Crear
            </Button>
          </Group>
        </Stack>
      )}
    </Stack>
  )
}

export function DuplicatesPage() {
  const { data: plexSettings } = usePlexQuery()
  const { data: playerSettings } = usePlayersQuery()

  const [folder, setFolder] = useState('')
  const [pares, setPares] = useState<DuplicatePair[]>([])
  const [totalPeliculas, setTotalPeliculas] = useState<number | null>(null)
  const [index, setIndex] = useState(0)
  const [selection, setSelection] = useState<Record<string, 1 | 2 | null>>({})
  const [basket, setBasket] = useState<Set<string>>(new Set())
  const [destino, setDestino] = useState('')
  const [quitarSeleccion, setQuitarSeleccion] = useState<Set<string>>(new Set())
  const [showPlayers, setShowPlayers] = useState(false)
  const [plexMeta, setPlexMeta] = useState<PlexMetadataResponse | null>(null)
  const [hashResult, setHashResult] = useState<CheckHashResult | null>(null)

  const [scanJobId, setScanJobId] = useState<string | null>(null)
  const [showSaved, setShowSaved] = useState(false)

  const scan = useScanDuplicates()
  const plexMetadata = usePlexMetadataForPair()
  const deleteDup = useDeleteDuplicates()
  const bulkMove = useBulkMoveDuplicates()
  const saveScan = useSaveDuplicatesScan()
  const loadScan = useLoadDuplicatesScan()
  const createEdition = useCreateEdition()
  const checkHash = useCheckHash()
  const { data: savedScans, isLoading: loadingSaved } = useSavedDuplicatesScans(showSaved)

  const scanState = useJobProgress<ScanResult>(scanJobId)
  const scanRunning = !!scanJobId && scanState?.status === 'running'

  useEffect(() => {
    if (scanState?.status === 'done' && scanState.result) {
      setPares(scanState.result.pares)
      setTotalPeliculas(scanState.result.total_peliculas)
      setIndex(0)
      setScanJobId(null)
      notifications.show({
        color: 'green',
        message: `✅ ${scanState.result.total_peliculas} película(s) — ${scanState.result.pares.length} par(es) duplicado(s)`,
      })
    } else if (scanState?.status === 'error') {
      notifications.show({ color: 'red', message: `⚠️ ${scanState.error}` })
      setScanJobId(null)
    }
  }, [scanState])

  const par = pares[index]

  const videoInfo1 = useVideoInfo(par?.peli1.ruta, !!par?.peli1.existe)
  const videoInfo2 = useVideoInfo(par?.peli2.ruta, !!par?.peli2.existe)

  useEffect(() => {
    setShowPlayers(false)
    setPlexMeta(null)
    setHashResult(null)
    if (par && plexSettings?.fetch_metadata && plexSettings.is_configured) {
      plexMetadata.mutate(
        { ruta1: par.peli1.ruta, ruta2: par.peli2.ruta },
        { onSuccess: setPlexMeta },
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [par?.clave])

  const onEscanear = () => {
    if (!folder) return
    scan.mutate(folder, {
      onSuccess: (data) => setScanJobId(data.job_id),
      onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }),
    })
  }

  const avanzar = () => setIndex((i) => Math.min(i + 1, pares.length - 1))

  const onEliminarSeleccionada = () => {
    if (!par) return
    const sel = selection[par.clave]
    if (!sel) return
    const archivo = sel === 1 ? par.peli1.ruta : par.peli2.ruta
    deleteDup.mutate([archivo], {
      onSuccess: (result) => {
        if (result.movidos) {
          notifications.show({ color: 'green', message: '✅ Movido a debug' })
          setPares((prev) => {
            const nueva = prev.filter((p) => p.clave !== par.clave)
            setIndex((i) => Math.min(i, Math.max(0, nueva.length - 1)))
            return nueva
          })
          setBasket((prev) => {
            const next = new Set(prev)
            next.delete(archivo)
            return next
          })
        } else {
          notifications.show({ color: 'red', message: result.errores.join('; ') })
        }
      },
    })
  }

  const onCrearEdicion = (archivo: string, movieTitle: string, editionName: string) => {
    if (!par) return
    createEdition.mutate(
      { archivo, movie_title: movieTitle, edition_name: editionName },
      {
        onSuccess: (result) => {
          if (result.ok) {
            notifications.show({ color: 'green', message: `✅ Edición creada: ${result.nueva_ruta}` })
            setPares((prev) => {
              const nueva = prev.filter((p) => p.clave !== par.clave)
              setIndex((i) => Math.min(i, Math.max(0, nueva.length - 1)))
              return nueva
            })
          } else {
            notifications.show({ color: 'red', message: `⚠️ ${result.detail}` })
          }
        },
        onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }),
      },
    )
  }

  const onQuitarSeleccionados = () => {
    if (!quitarSeleccion.size) return
    const n = quitarSeleccion.size
    setPares((prev) => {
      const nueva = prev.filter((p) => !quitarSeleccion.has(p.clave))
      setIndex((i) => Math.min(i, Math.max(0, nueva.length - 1)))
      return nueva
    })
    setQuitarSeleccion(new Set())
    notifications.show({ color: 'gray', message: `🙈 ${n} par(es) quitado(s) de la lista (no se ha tocado ningún archivo)` })
  }

  const toggleBasket = (ruta: string) => {
    setBasket((prev) => {
      const next = new Set(prev)
      if (next.has(ruta)) next.delete(ruta)
      else next.add(ruta)
      return next
    })
  }

  const onMoverCesta = () => {
    if (!basket.size || !destino) return
    bulkMove.mutate(
      { archivos: [...basket], destino },
      {
        onSuccess: (result) => {
          notifications.show({ color: 'green', message: `✅ ${result.movidos} archivo(s) movido(s) a ${destino}` })
          if (result.errores.length) notifications.show({ color: 'red', message: result.errores.join('; ') })
          setBasket(new Set())
        },
      },
    )
  }

  const onGuardar = () => {
    saveScan.mutate(
      { folder, pares },
      { onSuccess: () => notifications.show({ color: 'green', message: '💾 Progreso guardado' }) },
    )
  }

  const onCargar = (file_path: string) => {
    loadScan.mutate(file_path, {
      onSuccess: (result) => {
        setPares(result.pares)
        setTotalPeliculas(null)
        setIndex(0)
        setShowSaved(false)
        notifications.show({
          color: 'green',
          message: `📂 ${result.pares.length} par(es) cargado(s) (${result.no_existentes} ya no válidos)`,
        })
      },
    })
  }

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>🎬 Duplicados</Title>
        <Text c="dimmed">
          Revisa cada par uno a uno: nombre, tamaño, duración, fotograma de comparación y, si Plex
          está configurado, sus metadatos — luego marca cuál sobra y muévela a debug.
        </Text>
      </div>

      <Paper withBorder p="md" radius="md">
        <Stack gap="sm">
          <RecentPathInput label="Carpeta a analizar" category="duplicados" value={folder} onChange={setFolder} />
          <Group>
            <Button loading={scan.isPending || scanRunning} disabled={!folder} onClick={onEscanear}>
              🔍 Escanear
            </Button>
            <Button variant="default" onClick={() => setShowSaved((v) => !v)}>
              📂 Cargar guardado
            </Button>
            {pares.length > 0 && (
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
                  No hay escaneos de duplicados guardados todavía.
                </Text>
              ) : (
                <Stack gap={4}>
                  {savedScans.map((s) => (
                    <Group key={s.file_path} justify="space-between">
                      <Text size="sm">
                        {s.scan_path} — {s.total_pairs} par(es) — {s.scan_date}
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

      {basket.size > 0 && (
        <Paper withBorder p="md" radius="md">
          <Group justify="space-between" wrap="wrap">
            <Text size="sm">🧺 {basket.size} archivo(s) en la cesta para mover en lote</Text>
            <Group gap="xs">
              <TextInput
                placeholder="Carpeta de destino"
                value={destino}
                onChange={(e) => setDestino(e.currentTarget.value)}
                w={280}
              />
              <Button size="xs" loading={bulkMove.isPending} disabled={!destino} onClick={onMoverCesta}>
                📁 Mover cesta
              </Button>
            </Group>
          </Group>
        </Paper>
      )}

      {pares.length > 0 && (
        <Accordion variant="contained">
          <Accordion.Item value="quitar-varios">
            <Accordion.Control>
              ☑️ Quitar varios pares de la lista de golpe ({pares.length} en total)
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="sm">
                <Text size="sm" c="dimmed">
                  Esto solo saca el par de esta lista de revisión, no toca ningún archivo en disco.
                  Para borrar/mover archivos usa "Mover seleccionada a debug" en cada par.
                </Text>
                <div style={{ overflowX: 'auto' }}>
                  <Table>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th></Table.Th>
                        <Table.Th>Par</Table.Th>
                        <Table.Th>Película 1</Table.Th>
                        <Table.Th>Película 2</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {pares.map((p, i) => (
                        <Table.Tr key={p.clave}>
                          <Table.Td>
                            <Checkbox
                              checked={quitarSeleccion.has(p.clave)}
                              onChange={(e) => {
                                const checked = e.currentTarget.checked
                                setQuitarSeleccion((prev) => {
                                  const next = new Set(prev)
                                  if (checked) next.add(p.clave)
                                  else next.delete(p.clave)
                                  return next
                                })
                              }}
                            />
                          </Table.Td>
                          <Table.Td>{i + 1}</Table.Td>
                          <Table.Td>{p.peli1.nombre}</Table.Td>
                          <Table.Td>{p.peli2.nombre}</Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </div>
                <Group>
                  <Button size="xs" color="red" disabled={!quitarSeleccion.size} onClick={onQuitarSeleccionados}>
                    🗑️ Quitar {quitarSeleccion.size} par(es) de la lista
                  </Button>
                </Group>
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      )}

      {pares.length > 0 && par && (
        <Paper withBorder p="md" radius="md">
          <Stack gap="md">
            <Group justify="space-between">
              <Text fw={500}>
                Par {index + 1} de {pares.length}
                {totalPeliculas !== null && ` — ${totalPeliculas} película(s) escaneadas en total`}
              </Text>
              <Group gap="xs">
                <Button size="xs" variant="default" disabled={index === 0} onClick={() => setIndex((i) => i - 1)}>
                  ◀ Anterior
                </Button>
                <Button size="xs" variant="default" disabled={index >= pares.length - 1} onClick={avanzar}>
                  Siguiente ▶
                </Button>
              </Group>
            </Group>

            <SimpleGrid cols={{ base: 1, sm: 2 }}>
              <FileCard
                info={par.peli1}
                otherCreado={par.peli2.creado}
                selected={selection[par.clave] === 1}
                onSelect={() => setSelection((prev) => ({ ...prev, [par.clave]: prev[par.clave] === 1 ? null : 1 }))}
                onAddBasket={() => toggleBasket(par.peli1.ruta)}
                inBasket={basket.has(par.peli1.ruta)}
                plex={plexMeta?.file1}
                videoInfo={videoInfo1.data}
                loadingVideoInfo={videoInfo1.isLoading}
                onCreateEdition={(editionName) => {
                  const title = (plexMeta?.file1.datos?.title as string | undefined) ?? stem(par.peli1.nombre)
                  onCrearEdicion(par.peli1.ruta, title, editionName)
                }}
                creatingEdition={createEdition.isPending}
              />
              <FileCard
                info={par.peli2}
                otherCreado={par.peli1.creado}
                selected={selection[par.clave] === 2}
                onSelect={() => setSelection((prev) => ({ ...prev, [par.clave]: prev[par.clave] === 2 ? null : 2 }))}
                onAddBasket={() => toggleBasket(par.peli2.ruta)}
                inBasket={basket.has(par.peli2.ruta)}
                plex={plexMeta?.file2}
                videoInfo={videoInfo2.data}
                loadingVideoInfo={videoInfo2.isLoading}
                onCreateEdition={(editionName) => {
                  const title = (plexMeta?.file2.datos?.title as string | undefined) ?? stem(par.peli2.nombre)
                  onCrearEdicion(par.peli2.ruta, title, editionName)
                }}
                creatingEdition={createEdition.isPending}
              />
            </SimpleGrid>

            <Group gap="xs">
              {plexMeta?.es_duplicado_plex && (
                <Badge color="red" variant="light">
                  🔴 Plex las reconoce como la misma película
                </Badge>
              )}
              {carpeta(par.peli1.ruta) !== carpeta(par.peli2.ruta) && (
                <Badge color="blue" variant="light">
                  📁 Están en carpetas distintas
                </Badge>
              )}
            </Group>
            {plexMeta?.duracion_mensaje && (
              <Text size="sm" c={plexMeta.duracion_compatible ? 'green' : 'orange'}>
                {plexMeta.duracion_compatible ? '✅' : '⚠️'} {plexMeta.duracion_mensaje}
              </Text>
            )}

            <Group gap="xs" align="center">
              <Button
                size="xs"
                variant="default"
                loading={checkHash.isPending}
                disabled={!par.peli1.existe || !par.peli2.existe}
                onClick={() => {
                  setHashResult(null)
                  checkHash.mutate(
                    { ruta1: par.peli1.ruta, ruta2: par.peli2.ruta },
                    { onSuccess: setHashResult, onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }) },
                  )
                }}
              >
                🔍 Comprobar si son bit a bit idénticos
              </Button>
              {checkHash.isPending && (
                <Text size="xs" c="dimmed">
                  Leyendo los dos archivos enteros — con archivos grandes puede tardar varios minutos...
                </Text>
              )}
              {hashResult && !checkHash.isPending && (
                <Text size="sm" c={!hashResult.ok ? 'red' : hashResult.identical ? 'green' : 'dimmed'}>
                  {!hashResult.ok
                    ? `⚠️ ${hashResult.detail}`
                    : hashResult.identical
                      ? '✅ Idénticos byte a byte — mismo archivo con otro nombre'
                      : '↔️ Diferentes — no es el mismo archivo'}
                </Text>
              )}
            </Group>

            <SimpleGrid cols={{ base: 1, sm: 2 }}>
              {par.peli1.existe && <FramePreview archivo={par.peli1.ruta} />}
              {par.peli2.existe && <FramePreview archivo={par.peli2.ruta} />}
            </SimpleGrid>

            <Group>
              <Button size="xs" variant="subtle" onClick={() => setShowPlayers((v) => !v)}>
                {showPlayers ? '🙈 Ocultar reproductor' : '🎥 Mostrar reproductor completo'}
              </Button>
            </Group>
            {showPlayers && playerSettings?.show_embedded_players && (
              <SimpleGrid cols={{ base: 1, sm: 2 }}>
                {par.peli1.existe && <VideoPlayer archivo={par.peli1.ruta} />}
                {par.peli2.existe && <VideoPlayer archivo={par.peli2.ruta} />}
              </SimpleGrid>
            )}

            <Group>
              <Button
                color="red"
                loading={deleteDup.isPending}
                disabled={!selection[par.clave]}
                onClick={onEliminarSeleccionada}
              >
                🗑️ Mover seleccionada a debug
              </Button>
            </Group>
          </Stack>
        </Paper>
      )}

      {pares.length === 0 && scanState?.status === 'done' && (
        <Alert color="green" icon={<IconInfoCircle />}>
          No se encontraron duplicados en esa carpeta.
        </Alert>
      )}
    </Stack>
  )
}
