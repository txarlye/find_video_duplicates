import { createBrowserRouter, Navigate } from 'react-router-dom'
import { App } from './App'
import { TrashPage } from './features/trash/TrashPage'
import { SettingsPage } from './features/settings/SettingsPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/basura" replace /> },
      { path: 'basura', element: <TrashPage /> },
      { path: 'configuracion', element: <SettingsPage /> },
    ],
  },
])
