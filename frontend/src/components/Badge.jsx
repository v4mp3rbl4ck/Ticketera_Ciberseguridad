export default function Badge({ children, tone = 'neutral' }) {
  return <span className={`badge ${tone}`}>{children}</span>
}

export function severityTone(severity) {
  if (!severity) return 'neutral'
  if (severity.includes('Alta')) return 'danger'
  if (severity.includes('Media')) return 'warning'
  if (severity.includes('Baja')) return 'success'
  if (severity.includes('Crítica')) return 'critical'
  return 'neutral'
}

export function statusTone(status) {
  if (!status) return 'neutral'
  if (status === 'Nuevo') return 'warning'
  if (status === 'En Progreso') return 'info'
  if (status === 'En Espera') return 'muted'
  if (status === 'Resuelto' || status === 'Cerrado') return 'success'
  return 'neutral'
}
