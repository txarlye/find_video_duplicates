import { createBrowserRouter, Navigate } from 'react-router-dom'
import { App } from './App'
import { TrashPage } from './features/trash/TrashPage'
import { SettingsPage } from './features/settings/SettingsPage'
import { ProposalsPage } from './features/proposals/ProposalsPage'
import { OrphansPage } from './features/orphans/OrphansPage'
import { SeriesPage } from './features/series/SeriesPage'
import { TelegramPage } from './features/telegram/TelegramPage'
import { DuplicatesPage } from './features/duplicates/DuplicatesPage'
import { AboutPage } from './features/about/AboutPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/duplicados" replace /> },
      { path: 'duplicados', element: <DuplicatesPage /> },
      { path: 'basura', element: <TrashPage /> },
      { path: 'configuracion', element: <SettingsPage /> },
      { path: 'propuestas', element: <ProposalsPage /> },
      { path: 'huerfanos', element: <OrphansPage /> },
      { path: 'series', element: <SeriesPage /> },
      { path: 'telegram', element: <TelegramPage /> },
      { path: 'acerca-de', element: <AboutPage /> },
    ],
  },
])
