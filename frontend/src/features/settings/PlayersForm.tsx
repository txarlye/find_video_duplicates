import { useEffect, useState } from 'react'
import { Alert, Button, Checkbox, Group, Loader, NumberInput, Select, Stack, Text, TextInput, Title } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { usePlayersQuery, useSavePlayers } from './useSettings'
import type { PlayerSettings } from './types'

export function PlayersForm() {
  const { data, isLoading } = usePlayersQuery()
  const save = useSavePlayers()
  const [form, setForm] = useState<PlayerSettings | null>(null)

  useEffect(() => {
    if (data) setForm(data)
  }, [data])

  if (isLoading || !form) return <Loader />

  const minutos = Math.floor(form.video_start_time_seconds / 60)
  const segundos = form.video_start_time_seconds % 60

  const guardar = () => {
    save.mutate(form, { onSuccess: () => notifications.show({ color: 'green', message: '✅ Configuración guardada' }) })
  }

  return (
    <Stack gap="md">
      <Title order={5}>🎬 Reproductores de Video</Title>
      <Checkbox
        label="🎬 Mostrar Reproductores de Video"
        description="Mostrar reproductores embebidos para comparar duplicados"
        checked={form.show_video_players}
        onChange={(e) => setForm({ ...form, show_video_players: e.currentTarget.checked })}
      />
      <Checkbox
        label="📺 Mostrar Reproductores Embebidos"
        description="Mostrar reproductores embebidos (más lento pero integrado)"
        checked={form.show_embedded_players}
        onChange={(e) => setForm({ ...form, show_embedded_players: e.currentTarget.checked })}
      />
      <Select
        label="📏 Tamaño de Reproductores"
        data={[
          { value: 'small', label: 'Pequeño' },
          { value: 'medium', label: 'Mediano' },
          { value: 'large', label: 'Grande' },
        ]}
        value={form.video_player_size}
        onChange={(v) => v && setForm({ ...form, video_player_size: v as PlayerSettings['video_player_size'] })}
        w={220}
      />

      <div>
        <Text fw={500} mb={4}>
          ⏱️ Momento del fotograma para comparar
        </Text>
        <Text size="sm" c="dimmed" mb="xs">
          Evita ver los títulos de crédito
        </Text>
        <Group>
          <NumberInput
            label="Minuto"
            min={0}
            max={180}
            value={minutos}
            onChange={(v) => setForm({ ...form, video_start_time_seconds: Number(v) * 60 + segundos })}
            w={120}
          />
          <NumberInput
            label="Segundo"
            min={0}
            max={59}
            value={segundos}
            onChange={(v) => setForm({ ...form, video_start_time_seconds: minutos * 60 + Number(v) })}
            w={120}
          />
        </Group>
      </div>

      <Group>
        <Button loading={save.isPending} onClick={guardar}>
          💾 Guardar configuración reproductores
        </Button>
      </Group>

      <Title order={5} mt="md">
        🐛 Modo Debug
      </Title>
      <Alert color="blue">
        <strong>Modo debug siempre activo</strong> (de momento no se puede desactivar desde aquí): nada se
        borra nunca directamente, todo lo eliminado o renombrado se mueve primero a la carpeta de debug de
        abajo. Bórralo de verdad tú a mano desde el NAS cuando quieras.
      </Alert>
      <TextInput
        label="📁 Carpeta de Debug"
        description="Carpeta donde se mueven los archivos en vez de borrarse"
        value={form.debug_folder}
        onChange={(e) => setForm({ ...form, debug_folder: e.currentTarget.value })}
      />
      <Group>
        <Button loading={save.isPending} onClick={guardar}>
          💾 Guardar configuración debug
        </Button>
      </Group>
    </Stack>
  )
}
