import { useState } from 'react'
import { Accordion, Alert, Button, Group, Stack, Text, Title } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconRobot } from '@tabler/icons-react'
import { ScanResultsShell } from '../../components/ScanResultsShell'
import {
  useApplyDuplicados,
  useApplyHuerfanos,
  useDismissDuplicados,
  useDismissHuerfanos,
  useDismissedProposalsQuery,
  useGenerateProposals,
  useUndismissDuplicado,
  useUndismissHuerfano,
} from './useProposals'
import type { DuplicadoProposal, HuerfanoProposal } from './types'

function gb(bytes: number) {
  return (bytes / 1024 ** 3).toFixed(2)
}

export function ProposalsPage() {
  const generate = useGenerateProposals()
  const applyHuerfanos = useApplyHuerfanos()
  const dismissHuerfanos = useDismissHuerfanos()
  const applyDuplicados = useApplyDuplicados()
  const dismissDuplicados = useDismissDuplicados()
  const { data: dismissed } = useDismissedProposalsQuery()
  const undismissHuerfano = useUndismissHuerfano()
  const undismissDuplicado = useUndismissDuplicado()

  const [huerfanos, setHuerfanos] = useState<HuerfanoProposal[]>([])
  const [duplicados, setDuplicados] = useState<DuplicadoProposal[]>([])
  const [generated, setGenerated] = useState(false)

  const onGenerate = () => {
    generate.mutate(undefined, {
      onSuccess: (data) => {
        setHuerfanos(data.huerfanos)
        setDuplicados(data.duplicados)
        setGenerated(true)
        notifications.show({
          color: 'green',
          message: `✅ ${data.huerfanos.length} propuesta(s) de nombre, ${data.duplicados.length} propuesta(s) de borrado`,
        })
      },
      onError: (e) => notifications.show({ color: 'red', message: `⚠️ ${(e as Error).message}` }),
    })
  }

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>🤖 Propuestas</Title>
        <Text c="dimmed">
          Nombres sugeridos para huérfanos y copias recomendadas a borrar en duplicados — revisa,
          aplica con un clic o descarta para siempre. La programación (carpetas, hora, email) se
          configura en <strong>⚙️ Configuración → 📅 Programación</strong>.
        </Text>
      </div>

      <Group>
        <Button leftSection={<IconRobot size={16} />} loading={generate.isPending} onClick={onGenerate}>
          🔄 Generar propuestas ahora
        </Button>
      </Group>

      {!generated ? (
        <Alert color="blue">
          💡 Pulsa "Generar propuestas ahora", o espera al próximo escaneo programado si ya lo has
          configurado.
        </Alert>
      ) : (
        <>
          <div>
            <Title order={4} mb="xs">
              🏷️ {huerfanos.length} nombre(s) sugerido(s)
            </Title>
            <ScanResultsShell
              records={huerfanos as unknown as Record<string, unknown>[]}
              idAccessor="clave"
              columns={[
                {
                  accessor: 'nombre_actual',
                  title: 'Archivo',
                  render: (r) => {
                    const p = r as unknown as HuerfanoProposal
                    return (
                      <div>
                        <Text size="sm">{p.nombre_actual}</Text>
                        <Text size="sm" c="blue">
                          ➡️ {p.nombre_sugerido}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {p.archivo} — {gb(p.tamaño)} GB
                        </Text>
                      </div>
                    )
                  },
                },
              ]}
              bulkActions={[
                {
                  label: '✅ Aplicar seleccionadas',
                  color: 'blue',
                  loading: applyHuerfanos.isPending,
                  onClick: (selected) => {
                    const items = selected as unknown as HuerfanoProposal[]
                    applyHuerfanos.mutate(items, {
                      onSuccess: (result) => {
                        notifications.show({ color: 'green', message: `✅ ${result.aplicados} renombrado(s)` })
                        if (result.errores.length) {
                          notifications.show({ color: 'red', message: result.errores.join('; ') })
                        }
                        const claves = new Set(items.map((i) => i.clave))
                        setHuerfanos((prev) => prev.filter((h) => !claves.has(h.clave)))
                      },
                    })
                  },
                },
                {
                  label: '❌ Descartar seleccionadas',
                  loading: dismissHuerfanos.isPending,
                  onClick: (selected) => {
                    const items = selected as unknown as HuerfanoProposal[]
                    const claves = items.map((i) => i.clave)
                    dismissHuerfanos.mutate(claves, {
                      onSuccess: () => {
                        notifications.show({ color: 'gray', message: `🙈 ${claves.length} descartada(s)` })
                        setHuerfanos((prev) => prev.filter((h) => !claves.includes(h.clave)))
                      },
                    })
                  },
                },
              ]}
            />
          </div>

          <div>
            <Title order={4} mb="xs">
              🗑️ {duplicados.length} propuesta(s) de borrado
            </Title>
            <ScanResultsShell
              records={duplicados as unknown as Record<string, unknown>[]}
              idAccessor="clave"
              columns={[
                {
                  accessor: 'motivo',
                  title: 'Propuesta',
                  render: (r) => {
                    const p = r as unknown as DuplicadoProposal
                    return (
                      <div>
                        <Text size="sm">
                          🗑️ Borrar: <strong>{p.nombre_a_borrar}</strong> ({gb(p.tamaño_a_borrar)} GB)
                        </Text>
                        <Text size="sm">
                          ✅ Conservar: <strong>{p.nombre_a_conservar}</strong> ({gb(p.tamaño_a_conservar)} GB)
                        </Text>
                        <Text size="xs" c="dimmed">
                          {p.motivo}
                        </Text>
                      </div>
                    )
                  },
                },
              ]}
              bulkActions={[
                {
                  label: '✅ Aplicar seleccionadas',
                  color: 'blue',
                  loading: applyDuplicados.isPending,
                  onClick: (selected) => {
                    const items = selected as unknown as DuplicadoProposal[]
                    applyDuplicados.mutate(items, {
                      onSuccess: (result) => {
                        notifications.show({ color: 'green', message: `✅ ${result.aplicados} movido(s) a debug` })
                        if (result.errores.length) {
                          notifications.show({ color: 'red', message: result.errores.join('; ') })
                        }
                        const claves = new Set(items.map((i) => i.clave))
                        setDuplicados((prev) => prev.filter((d) => !claves.has(d.clave)))
                      },
                    })
                  },
                },
                {
                  label: '❌ Descartar seleccionadas',
                  loading: dismissDuplicados.isPending,
                  onClick: (selected) => {
                    const items = selected as unknown as DuplicadoProposal[]
                    const claves = items.map((i) => i.clave)
                    dismissDuplicados.mutate(claves, {
                      onSuccess: () => {
                        notifications.show({ color: 'gray', message: `🙈 ${claves.length} descartada(s)` })
                        setDuplicados((prev) => prev.filter((d) => !claves.includes(d.clave)))
                      },
                    })
                  },
                },
              ]}
            />
          </div>
        </>
      )}

      {dismissed && (dismissed.huerfanos.length > 0 || dismissed.duplicados.length > 0) && (
        <Accordion variant="contained">
          <Accordion.Item value="descartadas">
            <Accordion.Control>
              🙈 Descartadas ({dismissed.huerfanos.length + dismissed.duplicados.length})
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="xs">
                {dismissed.huerfanos.map((archivo) => (
                  <Group key={archivo} justify="space-between">
                    <Text size="sm">🏷️ {archivo.split(/[\\/]/).pop()}</Text>
                    <Button size="xs" variant="subtle" onClick={() => undismissHuerfano.mutate(archivo)}>
                      ↩️ Quitar
                    </Button>
                  </Group>
                ))}
                {dismissed.duplicados.map((clave) => {
                  const [ruta1, ruta2] = clave.split('|')
                  return (
                    <Group key={clave} justify="space-between">
                      <Text size="sm">
                        🗑️ {ruta1.split(/[\\/]/).pop()} vs {ruta2.split(/[\\/]/).pop()}
                      </Text>
                      <Button size="xs" variant="subtle" onClick={() => undismissDuplicado.mutate(clave)}>
                        ↩️ Quitar
                      </Button>
                    </Group>
                  )
                })}
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      )}
    </Stack>
  )
}
