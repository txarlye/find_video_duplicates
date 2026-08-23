import { useEffect, useState } from 'react'
import { Alert, Badge, Group, Loader, Select, Stack, Switch, Text, TextInput, Button } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useAiNamingQuery, useSaveAiNaming } from './useSettings'
import type { AiNamingSettings } from './types'

export function AiNamingForm() {
  const { data, isLoading } = useAiNamingQuery()
  const save = useSaveAiNaming()

  const [form, setForm] = useState<AiNamingSettings | null>(null)

  useEffect(() => {
    if (data) setForm(data)
  }, [data])

  if (isLoading || !form) return <Loader />

  const keyConfigured =
    form.provider === 'openai' ? form.openai_key_configured : form.provider === 'gemini' ? form.gemini_key_configured : true

  const guardar = () => {
    save.mutate(
      {
        enabled: form.enabled,
        provider: form.provider,
        mode: form.mode,
        ollama_url: form.ollama_url,
        ollama_model: form.ollama_model,
        openai_model: form.openai_model,
        gemini_model: form.gemini_model,
      },
      { onSuccess: () => notifications.show({ color: 'green', message: '✅ Guardado' }) },
    )
  }

  return (
    <Stack gap="md">
      <Text size="sm" c="dimmed">
        Sugerencia de nombre para huérfanos (aquí y en Propuestas) contra un proveedor de IA. Las
        claves de API (OpenAI, Gemini, TMDB, OMDb) viven solo en .env — aquí solo se elige el
        proveedor y el modelo.
      </Text>

      <Switch
        label="Activar sugerencia de nombres con IA"
        checked={form.enabled}
        onChange={(e) => setForm({ ...form, enabled: e.currentTarget.checked })}
      />

      {form.enabled && (
        <>
          <Select
            label="Proveedor"
            data={[
              { value: 'ollama', label: 'Ollama (local)' },
              { value: 'openai', label: 'OpenAI' },
              { value: 'gemini', label: 'Google Gemini' },
            ]}
            value={form.provider}
            onChange={(v) => v && setForm({ ...form, provider: v as AiNamingSettings['provider'] })}
          />

          <Select
            label="Modo"
            description="«Sugerir» pide confirmación manual; «automático» solo se usa en Propuestas"
            data={[
              { value: 'suggest', label: 'Sugerir (revisar antes de aplicar)' },
              { value: 'auto', label: 'Automático' },
            ]}
            value={form.mode}
            onChange={(v) => v && setForm({ ...form, mode: v as AiNamingSettings['mode'] })}
          />

          {form.provider === 'ollama' && (
            <Group grow>
              <TextInput
                label="URL de Ollama"
                value={form.ollama_url}
                onChange={(e) => setForm({ ...form, ollama_url: e.currentTarget.value })}
              />
              <TextInput
                label="Modelo"
                value={form.ollama_model}
                onChange={(e) => setForm({ ...form, ollama_model: e.currentTarget.value })}
              />
            </Group>
          )}

          {form.provider === 'openai' && (
            <TextInput
              label="Modelo"
              value={form.openai_model}
              onChange={(e) => setForm({ ...form, openai_model: e.currentTarget.value })}
            />
          )}

          {form.provider === 'gemini' && (
            <TextInput
              label="Modelo"
              value={form.gemini_model}
              onChange={(e) => setForm({ ...form, gemini_model: e.currentTarget.value })}
            />
          )}

          {form.provider !== 'ollama' && (
            <Group gap="xs">
              <Text size="sm">Clave de API:</Text>
              <Badge color={keyConfigured ? 'green' : 'red'} variant="light">
                {keyConfigured ? 'Configurada en .env' : 'Falta en .env'}
              </Badge>
            </Group>
          )}

          <Group gap="xs">
            <Text size="sm">TMDB:</Text>
            <Badge color={form.tmdb_configured ? 'green' : 'gray'} variant="light">
              {form.tmdb_configured ? 'Configurada' : 'No configurada'}
            </Badge>
            <Text size="sm">OMDb:</Text>
            <Badge color={form.omdb_configured ? 'green' : 'gray'} variant="light">
              {form.omdb_configured ? 'Configurada' : 'No configurada'}
            </Badge>
          </Group>

          {!keyConfigured && (
            <Alert color="yellow">
              Añade la clave correspondiente en .env (OPENAI_API_KEY / GEMINI_API_KEY) y reinicia el
              contenedor para que las sugerencias funcionen.
            </Alert>
          )}
        </>
      )}

      <Group>
        <Button loading={save.isPending} onClick={guardar}>
          💾 Guardar
        </Button>
      </Group>
    </Stack>
  )
}
