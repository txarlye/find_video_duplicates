import { createBrowserRouter, Navigate } from 'react-router-dom'
import { App } from './App'
import { TrashPage } from './features/trash/TrashPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/basura" replace /> },
      { path: 'basura', element: <TrashPage /> },
    ],
  },
])
