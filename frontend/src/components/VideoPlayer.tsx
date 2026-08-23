/**
 * Reproductor embebido nativo del navegador, contra /api/video/stream
 * (soporta Range requests) — a diferencia de st.video, que hacía su
 * propio streaming interno, aquí servimos el archivo nosotros mismos,
 * así que sí importaba dejar que el navegador pueda buscar (seek) sin
 * descargarse el archivo entero primero.
 */
export function VideoPlayer({ archivo }: { archivo: string }) {
  const src = `/api/video/stream?path=${encodeURIComponent(archivo)}`
  return (
    // eslint-disable-next-line jsx-a11y/media-has-caption
    <video controls preload="metadata" style={{ width: '100%', maxWidth: 480, borderRadius: 8 }} src={src} />
  )
}
