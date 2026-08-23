import { Stack, Tabs, Text, Title } from '@mantine/core'
import { DetectionForm } from './DetectionForm'
import { PlayersForm } from './PlayersForm'
import { PlexForm } from './PlexForm'
import { TelegramForm } from './TelegramForm'
import { AutomationForm } from './AutomationForm'

export function SettingsPage() {
  return (
    <Stack gap="md">
      <div>
        <Title order={2}>⚙️ Configuración</Title>
        <Text c="dimmed">
          Rutas, comportamiento de detección y conexión con Plex. Las claves de API y tokens
          (Telegram, TMDB, OMDb, IA...) se configuran aparte, en el archivo .env — no aquí, para no
          acabar guardándolas en config.json.
        </Text>
      </div>

      <Tabs defaultValue="deteccion">
        <Tabs.List>
          <Tabs.Tab value="deteccion">🔍 Detección</Tabs.Tab>
          <Tabs.Tab value="reproductores">🎬 Reproductores y Debug</Tabs.Tab>
          <Tabs.Tab value="plex">🎬 Plex</Tabs.Tab>
          <Tabs.Tab value="telegram">📱 Telegram</Tabs.Tab>
          <Tabs.Tab value="programacion">📅 Programación</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="deteccion" pt="md">
          <DetectionForm />
        </Tabs.Panel>
        <Tabs.Panel value="reproductores" pt="md">
          <PlayersForm />
        </Tabs.Panel>
        <Tabs.Panel value="plex" pt="md">
          <PlexForm />
        </Tabs.Panel>
        <Tabs.Panel value="telegram" pt="md">
          <TelegramForm />
        </Tabs.Panel>
        <Tabs.Panel value="programacion" pt="md">
          <AutomationForm />
        </Tabs.Panel>
      </Tabs>
    </Stack>
  )
}
