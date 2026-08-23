import { useEffect, useState } from 'react'
import {
  Accordion,
  Alert,
  Button,
  Checkbox,
  Code,
  Group,
  List,
  Loader,
  NumberInput,
  Stack,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core'
import { TimeInput } from '@mantine/dates'
import { IconTrash } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import {
  useAutomationQuery,
  useCreateSynologyTask,
  useSaveAutomation,
  useSaveAutomationFolders,
  useTestAutomationEmail,
  useTestSynologyConnection,
} from './useSettings'
import type { AutomationUpdate } from './types'

export function AutomationForm() {
  const { data, isLoading } = useAutomationQuery()
  const save = useSaveAutomation()
  const saveFolders = useSaveAutomationFolders()
  const testEmail = useTestAutomationEmail()
  const testSynology = useTestSynologyConnection()
  const createSynologyTask = useCreateSynologyTask()

  const [form, setForm] = useState<AutomationUpdate | null>(null)
  const [newFolder, setNewFolder] = useState('')

  useEffect(() => {
    if (!data) return
    const {
      movie_folders: _movieFolders,
      smtp_configured: _smtpConfigured,
      smtp_user: _smtpUser,
      last_run_date: _lastRunDate,
      synology_configured: _synologyConfigured,
      ...rest
    } = data
    setForm(rest)
  }, [data])

  if (isLoading || !form || !data) return <Loader />

  const guardar = () => {
    save.mutate(form, { onSuccess: () => notifications.show({ color: 'green', message: '✅ Guardado' }) })
  }

  const puedeProbar = data.smtp_configured && !!data.email_to

  return (
    <Stack gap="md">
      <Title order={5}>📅 Programación</Title>
      <Checkbox
        label="Activar escaneo programado de propuestas"
        checked={form.enabled}
        onChange={(e) => setForm({ ...form, enabled: e.currentTarget.checked })}
      />
      {form.enabled && (
        <Text size="sm" c="dimmed">
          🟢 Programador interno activo — comprueba cada minuto si es la hora configurada. Última
          ejecución: {data.last_run_date ?? 'todavía ninguna'}.
        </Text>
      )}

      <div>
        <Text fw={500} mb="xs">
          Carpetas de películas a analizar (huérfanos + duplicados)
        </Text>
        <List spacing={4} mb="sm">
          {data.movie_folders.map((f) => (
            <List.Item
              key={f}
              icon={
                <IconTrash
                  size={16}
                  style={{ cursor: 'pointer' }}
                  onClick={() => saveFolders.mutate(data.movie_folders.filter((x) => x !== f))}
                />
              }
            >
              📁 {f}
            </List.Item>
          ))}
        </List>
        <Group>
          <TextInput
            placeholder="Añadir carpeta"
            value={newFolder}
            onChange={(e) => setNewFolder(e.currentTarget.value)}
            w={360}
          />
          <Button
            variant="light"
            loading={saveFolders.isPending}
            onClick={() => {
              if (!newFolder || data.movie_folders.includes(newFolder)) return
              saveFolders.mutate([...data.movie_folders, newFolder], { onSuccess: () => setNewFolder('') })
            }}
          >
            ➕ Añadir carpeta
          </Button>
        </Group>
      </div>

      <div>
        <Text fw={500} mb="xs">
          ¿A qué hora?
        </Text>
        <TimeInput
          w={160}
          value={form.schedule_time}
          onChange={(e) => setForm({ ...form, schedule_time: e.currentTarget.value })}
        />
        <Text size="sm" c="dimmed" mt={4}>
          Se comprueba cada minuto mientras la app esté encendida — si el contenedor está apagado justo a
          esa hora, ese día no se dispara.
        </Text>
      </div>

      <TextInput
        label="Email de aviso"
        value={form.email_to}
        onChange={(e) => setForm({ ...form, email_to: e.currentTarget.value })}
      />
      <TextInput
        label="URL de la app para el enlace del email"
        placeholder="http://100.x.x.x:8000"
        description="Normalmente tu IP de Tailscale — el email no puede adivinar por dónde vas a entrar."
        value={form.app_url}
        onChange={(e) => setForm({ ...form, app_url: e.currentTarget.value })}
      />
      <Textarea
        label="Mensaje personalizado (opcional, se antepone al cuerpo del email)"
        placeholder="Ej: Buenos días, esto es lo que encontré esta noche..."
        value={form.email_message}
        onChange={(e) => setForm({ ...form, email_message: e.currentTarget.value })}
      />

      {data.smtp_configured ? (
        <Text size="sm" c="green">
          ✅ SMTP configurado ({data.smtp_user})
        </Text>
      ) : (
        <Text size="sm" c="orange">
          ⚠️ Falta SMTP_USER/SMTP_PASSWORD en tu .env — sin esto no se puede enviar el email.
        </Text>
      )}
      <Text size="sm" c="dimmed">
        💡 Con Gmail, SMTP_PASSWORD tiene que ser una <strong>contraseña de aplicación</strong> de 16
        caracteres (myaccount.google.com/apppasswords) — tu contraseña normal de Gmail no funciona aquí.
      </Text>

      <div>
        <Text fw={500} mb="xs">
          ¿Cuándo compensa quedarse con la copia de mayor calidad?
        </Text>
        <Group>
          <NumberInput
            label="% máximo de más que puede pesar"
            min={0}
            step={5}
            value={form.size_premium_tolerance_pct}
            onChange={(v) => setForm({ ...form, size_premium_tolerance_pct: Number(v) })}
            w={220}
          />
          <NumberInput
            label="GB máximos de más"
            min={0}
            step={1}
            value={form.size_premium_max_gb}
            onChange={(v) => setForm({ ...form, size_premium_max_gb: Number(v) })}
            w={220}
          />
        </Group>
      </div>

      <Group>
        <Button loading={save.isPending} onClick={guardar}>
          💾 Guardar configuración de automatización
        </Button>
        <Button
          variant="light"
          disabled={!puedeProbar}
          loading={testEmail.isPending}
          onClick={() =>
            testEmail.mutate(undefined, {
              onSuccess: (r) =>
                notifications.show({
                  color: r.ok ? 'green' : 'red',
                  message: r.ok ? '✅ Email de prueba enviado' : `❌ ${r.detail}`,
                }),
            })
          }
        >
          📧 Enviar email de prueba
        </Button>
      </Group>
      {!puedeProbar && (
        <Text size="sm" c="dimmed">
          Guarda antes un email de aviso y ten SMTP_USER/SMTP_PASSWORD en .env para poder probar.
        </Text>
      )}

      <Accordion variant="contained">
        <Accordion.Item value="tarea-externa">
          <Accordion.Control>🕐 Prefiero una tarea programada externa (Synology, cron...)</Accordion.Control>
          <Accordion.Panel>
            <Text size="sm" c="dimmed" mb="sm">
              El programador interno de arriba ya dispara el escaneo solo, sin nada más que configurar.
              Esto es solo para quien prefiera controlar el "cuándo" desde fuera del contenedor.
            </Text>

            {data.synology_configured ? (
              <Stack gap="xs" mb="md">
                <Text size="sm">
                  🔧 Credenciales de Synology configuradas — puedo crear la tarea directamente en el
                  Planificador de tareas de tu DSM, a la hora de arriba.
                </Text>
                <Group>
                  <Button
                    size="xs"
                    variant="default"
                    loading={testSynology.isPending}
                    onClick={() =>
                      testSynology.mutate(undefined, {
                        onSuccess: (r) =>
                          notifications.show({
                            color: r.ok ? 'green' : 'red',
                            message: r.ok ? '✅ Conexión con DSM correcta' : `❌ ${r.detail}`,
                          }),
                      })
                    }
                  >
                    🔌 Probar conexión con el NAS
                  </Button>
                  <Button
                    size="xs"
                    loading={createSynologyTask.isPending}
                    onClick={() =>
                      createSynologyTask.mutate(undefined, {
                        onSuccess: (r) =>
                          notifications.show({
                            color: r.ok ? 'green' : 'red',
                            message: r.ok
                              ? '✅ Tarea creada/actualizada en el Planificador de DSM'
                              : `❌ ${r.detail}`,
                          }),
                      })
                    }
                  >
                    ➕ Crear/actualizar tarea en el Planificador de Synology
                  </Button>
                </Group>
                <Text size="xs" c="dimmed">
                  Usa la API interna del Planificador de tareas de DSM (no documentada oficialmente por
                  Synology) — si algo falla, el mensaje de arriba trae el detalle que devuelve DSM.
                </Text>
              </Stack>
            ) : (
              <Alert color="blue" variant="light" mb="md">
                <Text size="sm">
                  Para crear la tarea automáticamente desde aquí, añade{' '}
                  <Code>SYNOLOGY_HOST</Code>/<Code>SYNOLOGY_PORT</Code>/<Code>SYNOLOGY_USER</Code>/
                  <Code>SYNOLOGY_PASSWORD</Code> a tu <Code>.env</Code> — usa un usuario DSM{' '}
                  <strong>dedicado y restringido</strong> (grupo administrators, requisito de la propia
                  API), nunca tu cuenta de administrador principal: es la única credencial de esta app
                  con alcance de administrador sobre el NAS.
                </Text>
              </Alert>
            )}

            <Text size="sm" mb="xs">
              O crea la tarea tú mismo en{' '}
              <strong>Panel de control → Planificador de tareas → Tarea programada → Script definido por
              el usuario</strong>:
            </Text>
            <Code block>docker exec find-video-duplicates python scheduled_scan.py</Code>
            <Text size="sm" c="dimmed" mt="sm">
              Con la tarea externa puedes dejar desactivado el programador interno de arriba si quieres —
              scheduled_scan.py hace exactamente lo mismo, solo que disparado desde fuera.
            </Text>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
      <Alert color="gray" variant="light">
        No portado de la pantalla anterior: la sección de IMDB del sidebar de Streamlit era un
        formulario sin terminar (nunca llegó a guardar nada) — se ha omitido en vez de portarlo tal cual.
      </Alert>
    </Stack>
  )
}
