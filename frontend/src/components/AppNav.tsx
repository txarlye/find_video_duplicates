import { NavLink, Stack } from '@mantine/core'
import {
  IconBrandTelegram,
  IconFileSearch,
  IconInfoCircle,
  IconMovie,
  IconRobot,
  IconSettings,
  IconTrash,
  IconVideo,
} from '@tabler/icons-react'
import { useLocation, useNavigate } from 'react-router-dom'

interface NavItem {
  label: string
  path: string
  icon: React.ReactNode
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Duplicados', path: '/duplicados', icon: <IconMovie size={18} /> },
  { label: 'Huérfanos', path: '/huerfanos', icon: <IconFileSearch size={18} /> },
  { label: 'Series', path: '/series', icon: <IconVideo size={18} /> },
  { label: 'Propuestas', path: '/propuestas', icon: <IconRobot size={18} /> },
  { label: 'Basura', path: '/basura', icon: <IconTrash size={18} /> },
  { label: 'Configuración', path: '/configuracion', icon: <IconSettings size={18} /> },
  { label: 'Telegram', path: '/telegram', icon: <IconBrandTelegram size={18} /> },
  { label: 'Acerca de', path: '/acerca-de', icon: <IconInfoCircle size={18} /> },
]

export function AppNav({ onNavigate }: { onNavigate?: () => void }) {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Stack gap={4}>
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.label}
          label={item.label}
          leftSection={item.icon}
          active={location.pathname === item.path}
          onClick={() => {
            navigate(item.path)
            onNavigate?.()
          }}
        />
      ))}
    </Stack>
  )
}
