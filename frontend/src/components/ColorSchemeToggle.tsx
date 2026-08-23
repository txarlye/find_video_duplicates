import { ActionIcon, useComputedColorScheme, useMantineColorScheme } from '@mantine/core'
import { IconMoon, IconSun } from '@tabler/icons-react'

/**
 * Switch de modo claro/oscuro. Mantine persiste la elección en
 * localStorage sola (clave "mantine-color-scheme-value") — no hace
 * falta guardar nada a mano ni tocar el backend para esto.
 */
export function ColorSchemeToggle() {
  const { setColorScheme } = useMantineColorScheme()
  const computedColorScheme = useComputedColorScheme('light')

  return (
    <ActionIcon
      onClick={() => setColorScheme(computedColorScheme === 'dark' ? 'light' : 'dark')}
      variant="default"
      size="lg"
      aria-label="Cambiar modo claro/oscuro"
    >
      {computedColorScheme === 'dark' ? <IconSun size={18} /> : <IconMoon size={18} />}
    </ActionIcon>
  )
}
