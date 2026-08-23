import { useState } from 'react'
import { Alert, Button, Group, Image, Stack, Text, TextInput } from '@mantine/core'

function parseTiempo(texto: string): number | null {
  const t = texto.trim()
  if (!t) return null
  if (/^\d+$/.test(t)) return parseInt(t, 10)
  const partes = t.split(':').map((p) => parseInt(p, 10))
  if (partes.some((p) => Number.isNaN(p))) return null
  if (partes.length === 2) return partes[0] * 60 + partes[1]
  if (partes.length === 3) return partes[0] * 3600 + partes[1] * 60 + partes[2]
  return null
}

function formatear(segundos: number) {
  const m = Math.floor(segundos / 60)
  const s = segundos % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

/**
 * Fotograma de comparación con navegación ◀/▶ ±10s — puerto de
 * _render_frame_preview de streamlit_manager.py. Mucho más rápido que
 * un reproductor completo para "hojear" un vídeo en busca de una
 * escena reconocible, incluso sobre carpetas en red.
 */
export function FramePreview({ archivo, startSeconds = 0 }: { archivo: string; startSeconds?: number }) {
  const [seconds, setSeconds] = useState(startSeconds)
  const [gotoText, setGotoText] = useState(formatear(startSeconds))
  const [error, setError] = useState(false)

  const src = `/api/video/frame?path=${encodeURIComponent(archivo)}&seconds=${seconds}`

  const irA = () => {
    const nuevo = parseTiempo(gotoText)
    if (nuevo === null) {
      setError(true)
      return
    }
    setError(false)
    setSeconds(Math.max(0, nuevo))
  }

  return (
    <Stack gap={4} maw={320}>
      <Image
        key={src}
        src={src}
        alt={`Fotograma en ${formatear(seconds)}`}
        radius="sm"
        fallbackSrc="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='170'%3E%3Crect width='300' height='170' fill='%23eee'/%3E%3C/svg%3E"
      />
      <Text size="xs" c="dimmed">
        ⏱️ Fotograma en {formatear(seconds)}
      </Text>
      <Group grow gap="xs">
        <Button
          size="xs"
          variant="default"
          disabled={seconds <= 0}
          onClick={() => {
            const nuevo = Math.max(0, seconds - 10)
            setSeconds(nuevo)
            setGotoText(formatear(nuevo))
          }}
        >
          ◀ -10s
        </Button>
        <Button
          size="xs"
          variant="default"
          onClick={() => {
            const nuevo = seconds + 10
            setSeconds(nuevo)
            setGotoText(formatear(nuevo))
          }}
        >
          +10s ▶
        </Button>
      </Group>
      <Group gap="xs" wrap="nowrap">
        <TextInput
          size="xs"
          placeholder="mm:ss"
          value={gotoText}
          onChange={(e) => setGotoText(e.currentTarget.value)}
          style={{ flex: 1 }}
        />
        <Button size="xs" onClick={irA}>
          ⏩ Ir
        </Button>
      </Group>
      {error && (
        <Alert color="red" p={4}>
          Formato no válido — usa mm:ss o hh:mm:ss
        </Alert>
      )}
    </Stack>
  )
}
