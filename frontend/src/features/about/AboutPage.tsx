import { Alert, Anchor, Code, Divider, List, Stack, Text, Title } from '@mantine/core'
import { IconAlertTriangle, IconInfoCircle } from '@tabler/icons-react'

export function AboutPage() {
  return (
    <Stack gap="xl" maw={860}>
      <div>
        <Title order={2}>ℹ️ Acerca de</Title>
        <Text c="dimmed">🗃️ Utilidades Synology &amp; Plex</Text>
      </div>

      <Stack gap="xs">
        <Text>
          Hecha por <strong>Txarlye</strong> para gestionar su propia biblioteca de vídeo en un
          Synology junto con Plex: detectar duplicados, encontrar archivos sin indexar, subirlos a
          Telegram y mantener todo ordenado sin tener que hacerlo a mano carpeta por carpeta.
        </Text>
        <Text size="sm" c="dimmed">
          Código abierto, pensada para uso personal en tu propia red (LAN o Tailscale) — no para
          exponerse a internet ni para gestionar la biblioteca de otra persona sin que lo sepa.
        </Text>
      </Stack>

      <Alert color="yellow" icon={<IconAlertTriangle />} title="Antes de usarla contra tu biblioteca real">
        <Text size="sm">
          La app <strong>nunca borra archivos directamente</strong>: todo lo que quitas de una
          carpeta se mueve primero a la carpeta de debug/papelera que configures (pantalla{' '}
          🗑️ Basura) — nada desaparece de verdad hasta que tú vacíes esa carpeta a mano. Aun así,
          es software personal, sin garantías: cada persona que la use es responsable de
          configurarla bien y de comprobar que se comporta como espera (rutas correctas, carpeta de
          debug activa, conexión de Plex apuntando donde toca) antes de soltarla sobre una
          biblioteca de verdad. Si es tu primera vez, pruébala antes contra una carpeta de prueba
          con un par de archivos sin valor.
        </Text>
      </Alert>

      <div>
        <Title order={3} mb="sm">
          🧭 Para qué sirve cada pantalla
        </Title>
        <List spacing="sm">
          <List.Item>
            <strong>🎬 Duplicados</strong> — escanea una carpeta, agrupa archivos por similitud de
            nombre + año, y te deja revisar cada par uno a uno (fotograma, duración/resolución
            reales, metadatos de Plex) para decidir cuál sobra y moverla a debug. Incluye una
            "cesta" para mover varios archivos sueltos a otra carpeta, y una lista con checkboxes
            para descartar de golpe pares que a simple vista no son duplicados de verdad.
          </List.Item>
          <List.Item>
            <strong>🧩 Huérfanos</strong> — archivos que ocupan espacio en disco pero no aparecen
            indexados en tu biblioteca de Plex. Puede sugerirles un nombre con IA (Ollama, OpenAI o
            Gemini) para que Plex los reconozca al renombrarlos.
          </List.Item>
          <List.Item>
            <strong>📺 Series</strong> — lo mismo que Duplicados/Huérfanos pero por episodios:
            capítulos duplicados, capítulos sueltos sin indexar, y series enteras de las que Plex no
            tiene ni el nombre.
          </List.Item>
          <List.Item>
            <strong>🤖 Propuestas</strong> — un resumen con nombres sugeridos y borrados
            recomendados, para revisar y aplicar/descartar en lote sin tener que entrar en cada
            pantalla. Puede programarse para ejecutarse solo y avisarte por email cuando haya algo
            nuevo.
          </List.Item>
          <List.Item>
            <strong>🗑️ Basura</strong> — la papelera: todo lo que la app ha movido aquí al eliminar
            duplicados o renombrar huérfanos. La app nunca la vacía por ti.
          </List.Item>
          <List.Item>
            <strong>⚙️ Configuración</strong> — rutas, umbral de similitud, conexión a Plex,
            reproductores, programación de Propuestas y proveedor de IA. Las claves de API y tokens
            no están aquí a propósito: viven solo en <Code>.env</Code>.
          </List.Item>
          <List.Item>
            <strong>📱 Telegram</strong> — sube vídeos de una carpeta a un canal de Telegram, con
            carátula y sinopsis si activas "Enriquecer" (busca la info en Plex/OMDb primero).
          </List.Item>
        </List>
      </div>

      <div>
        <Title order={3} mb="sm">
          ⚙️ Cómo configurarlo
        </Title>
        <Text size="sm" mb="xs">
          Dos ficheros, ninguno de los dos se sube nunca a git:
        </Text>
        <List spacing="xs" size="sm">
          <List.Item>
            <Code>config.json</Code> — rutas, ajustes de detección, series ignoradas... Se edita
            solo desde la propia pantalla ⚙️ Configuración, no hace falta tocarlo a mano.
          </List.Item>
          <List.Item>
            <Code>.env</Code> — todo lo que es un secreto: ruta a la base de datos de Plex si la
            quieres fija, <Code>TELEGRAM_BOT_TOKEN</Code>/<Code>TELEGRAM_API_ID</Code>/
            <Code>TELEGRAM_API_HASH</Code>, <Code>TMDB_API_KEY</Code>/<Code>OMDB_API_KEY</Code>,{' '}
            <Code>OPENAI_API_KEY</Code>/<Code>GEMINI_API_KEY</Code>, y{' '}
            <Code>SMTP_USER</Code>/<Code>SMTP_PASSWORD</Code> para el email de Propuestas (contraseña
            de aplicación de Gmail, no la contraseña normal). Copia{' '}
            <Code>.env.example</Code> a <Code>.env</Code> y rellénalo.
          </List.Item>
          <List.Item>
            Base de datos de Plex: en ⚙️ Configuración → 🎬 Plex, apunta a{' '}
            <Code>com.plexapp.plugins.library.db</Code> — en un Synology suele vivir bajo{' '}
            <Code>/volume1/PlexMediaServer/AppData/Plex Media Server/Plug-in Support/Databases/</Code>.
            La conexión es siempre de solo lectura.
          </List.Item>
          <List.Item>
            Acceso desde el móvil o desde otro equipo: instala{' '}
            <Anchor href="https://tailscale.com/" target="_blank" rel="noreferrer">
              Tailscale
            </Anchor>{' '}
            en el NAS (paquete oficial en Package Center) y en tus dispositivos, y usa la IP{' '}
            <Code>100.x.x.x</Code> que te da en vez de <Code>localhost</Code>. No hace falta
            configurar nada en <Code>docker/.env</Code> para esto: el contenedor publica el puerto
            en todas las interfaces y el propio Tailscale de Synology (corre en modo sin interfaz
            de red real) reenvía el tráfico del tailnet hacia ahí solo.
          </List.Item>
          <List.Item>
            Tarea programada en el Planificador de Synology (opcional): en{' '}
            <strong>📅 Programación</strong> ya hay un programador interno que no necesita nada de
            esto. Si además quieres el botón que la crea directamente en tu DSM, añade{' '}
            <Code>SYNOLOGY_HOST</Code>/<Code>SYNOLOGY_PORT</Code>/<Code>SYNOLOGY_USER</Code>/
            <Code>SYNOLOGY_PASSWORD</Code> — usa un usuario DSM dedicado y restringido, nunca tu
            cuenta de administrador principal.
          </List.Item>
        </List>
      </div>

      <div>
        <Title order={3} mb="sm">
          🛟 Si Plex deja de arrancar: restaurar la base de datos
        </Title>
        <Text size="sm" mb="xs">
          Esta app solo abre la base de datos de Plex <strong>en modo lectura</strong> (
          <Code>mode=ro</Code>) y, si esa conexión falla, nunca cae a una conexión editable como red
          de seguridad — así que, en condiciones normales, no debería poder tocarla. Pero ningún
          software está libre de bugs: si alguna vez ves en el log de Plex algo como{' '}
          <Code>database disk image is malformed</Code> y el contenedor de Plex entra en bucle de
          reinicio, esto es cómo se recupera (afecta a la base de datos en general, la causa más
          habitual es SQLite sobre una carpeta de red, no esta app en concreto — pero por si acaso):
        </Text>
        <List type="ordered" spacing="xs" size="sm">
          <List.Item>
            <strong>Para Plex</strong> (Panel de control / Container Manager → detén el contenedor
            o el paquete de Plex).
          </List.Item>
          <List.Item>
            <strong>No borres nada todavía</strong> — renombra los ficheros actuales añadiéndoles
            algo como <Code>.corrupto</Code>: <Code>com.plexapp.plugins.library.db</Code>, sus{' '}
            <Code>-wal</Code>/<Code>-shm</Code>, <Code>com.plexapp.plugins.library.blobs.db</Code> y
            los suyos si existen.
          </List.Item>
          <List.Item>
            <strong>Copia</strong> (no muevas) la copia de seguridad fechada más reciente de{' '}
            <Code>Plug-in Support/Databases/</Code> y quítale la fecha del nombre al copiarla:
            <br />
            <Code>com.plexapp.plugins.library.db-YYYY-MM-DD</Code> →{' '}
            <Code>com.plexapp.plugins.library.db</Code>
            <br />
            <Code>com.plexapp.plugins.library.blobs.db-YYYY-MM-DD</Code> →{' '}
            <Code>com.plexapp.plugins.library.blobs.db</Code>
          </List.Item>
          <List.Item>Arranca Plex de nuevo.</List.Item>
        </List>
        <Text size="sm" mt="xs" c="dimmed">
          Perderás la actividad (visto/no visto, añadidos recientes) desde la fecha de esa copia
          hasta ahora, pero el resto de la biblioteca se recupera intacta. Plex genera estas copias
          de seguridad solo, con fecha en el nombre, en esa misma carpeta.
        </Text>
      </div>

      <Divider />
      <Text size="xs" c="dimmed">
        <IconInfoCircle size={14} style={{ verticalAlign: 'text-bottom' }} /> Encontrarás más
        detalle técnico (arquitectura, variables de entorno, Docker) en el <Code>README.md</Code> y{' '}
        <Code>SETUP.md</Code> del propio repositorio. en  {' '}
            <Anchor href="https://github.com/txarlye/find_video_duplicates" target="_blank" rel="noreferrer">
              Este repositorio de GitHub
            </Anchor>{' '}
      </Text>
    </Stack>
  )
}
