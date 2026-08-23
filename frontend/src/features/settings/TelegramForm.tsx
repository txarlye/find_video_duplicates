import { Alert, Code, Loader, Stack, Text, Title } from '@mantine/core'
import { useTelegramStatusQuery } from './useSettings'

export function TelegramForm() {
  const { data, isLoading } = useTelegramStatusQuery()

  if (isLoading || !data) return <Loader />

  return (
    <Stack gap="md">
      <Title order={5}>📱 Telegram</Title>
      {data.configured ? (
        <Alert color="green">✅ Telegram configurado correctamente</Alert>
      ) : (
        <Alert color="yellow">⚠️ Telegram no está configurado</Alert>
      )}
      {data.channel_id && (
        <Text size="sm">
          Canal: <Code>{data.channel_id}</Code>
        </Text>
      )}
      <Text size="sm" c="dimmed">
        El bot token y el canal se configuran en el <Code>.env</Code> de la raíz del repo
        (<Code>TELEGRAM_BOT_TOKEN</Code>, <Code>TELEGRAM_CHANNEL_ID</Code>) — no aquí, para que el token
        nunca acabe guardado en <Code>config.json</Code>.
      </Text>
    </Stack>
  )
}
