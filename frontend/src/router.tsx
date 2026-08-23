import { createBrowserRouter, Navigate } from 'react-router-dom'
import { App } from './App'
import { TrashPage } from './features/trash/TrashPage'
import { SettingsPage } from './features/settings/SettingsPage'
import { ProposalsPage } from './features/proposals/ProposalsPage'
import { OrphansPage } from './features/orphans/OrphansPage'
import { SeriesPage } from './features/series/SeriesPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/basura" replace /> },
      { path: 'basura', element: <TrashPage /> },
      { path: 'configuracion', element: <SettingsPage /> },
      { path: 'propuestas', element: <ProposalsPage /> },
      { path: 'huerfanos', element: <OrphansPage /> },
      { path: 'series', element: <SeriesPage /> },
    ],
  },
])
