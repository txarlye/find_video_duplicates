import { NavLink, Stack, Tooltip } from '@mantine/core'
import {
  IconBrandTelegram,
  IconCopy,
  IconFileSearch,
  IconMovie,
  IconRobot,
  IconSettings,
  IconTrash,
  IconVideo,
} from '@tabler/icons-react'
import { useLocation, useNavigate } from 'react-router-dom'

interface NavItem {
  label: string
  path?: string
  icon: React.ReactNode
  legacyStreamlitView?: string
}

// Pantallas todavía no migradas: enlazan a la app de Streamlit (mismo
// host, puerto 8501) mientras dura la migración pantalla a pantalla.
const STREAMLIT_PORT = 8501

const NAV_ITEMS: NavItem[] = [
  { label: 'Duplicados', path: '/duplicados', icon: <IconMovie size={18} /> },
  { label: 'Huérfanos', path: '/huerfanos', icon: <IconFileSearch size={18} /> },
  { label: 'Series', path: '/series', icon: <IconVideo size={18} /> },
  { label: 'Propuestas', path: '/propuestas', icon: <IconRobot size={18} /> },
  { label: 'Basura', path: '/basura', icon: <IconTrash size={18} /> },
  { label: 'Configuración', path: '/configuracion', icon: <IconSettings size={18} /> },
  { label: 'Telegram', path: '/telegram', icon: <IconBrandTelegram size={18} /> },
]

function streamlitUrl(view: string) {
  return `${window.location.protocol}//${window.location.hostname}:${STREAMLIT_PORT}/?view=${view}`
}

export function AppNav({ onNavigate }: { onNavigate?: () => void }) {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Stack gap={4}>
      {NAV_ITEMS.map((item) => {
        if (item.legacyStreamlitView) {
          return (
            <Tooltip key={item.label} label="Todavía en la app antigua (Streamlit)" position="right">
              <NavLink
                component="a"
                href={streamlitUrl(item.legacyStreamlitView)}
                target="_blank"
                rel="noreferrer"
                label={item.label}
                leftSection={item.icon}
                rightSection={<IconCopy size={14} opacity={0.5} />}
              />
            </Tooltip>
          )
        }
        return (
          <NavLink
            key={item.label}
            label={item.label}
            leftSection={item.icon}
            active={location.pathname === item.path}
            onClick={() => {
              navigate(item.path!)
              onNavigate?.()
            }}
          />
        )
      })}
    </Stack>
  )
}
