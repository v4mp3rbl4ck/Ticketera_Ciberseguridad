export const APP_TIMEZONE = import.meta.env.VITE_APP_TIMEZONE || 'America/Santiago'

function normalizeApiDate(value) {
  if (!value || typeof value !== 'string') return value
  // La API almacena UTC naïve en BD y expone fechas ISO sin sufijo.
  // El frontend las interpreta explícitamente como UTC para mostrarlas en APP_TIMEZONE.
  if (/^\d{4}-\d{2}-\d{2}T/.test(value) && !/[zZ]|[+-]\d{2}:?\d{2}$/.test(value)) {
    return `${value}Z`
  }
  return value
}

export function formatDateTime(value) {
  const date = toDate(value)
  if (!date) return 'N/A'
  return new Intl.DateTimeFormat('es-CL', {
    timeZone: APP_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatDateOnly(value) {
  const date = toDate(value)
  if (!date) return 'N/A'
  return new Intl.DateTimeFormat('es-CL', {
    timeZone: APP_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date)
}

export function nowForDatetimeLocal() {
  const parts = new Intl.DateTimeFormat('sv-SE', {
    timeZone: APP_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(new Date())
  const obj = Object.fromEntries(parts.map(part => [part.type, part.value]))
  return `${obj.year}-${obj.month}-${obj.day}T${obj.hour}:${obj.minute}`
}

export function toDate(value) {
  if (!value) return null
  const date = new Date(normalizeApiDate(value))
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDurationHuman(seconds, options = {}) {
  if (seconds === null || seconds === undefined || Number.isNaN(Number(seconds))) return 'N/A'
  const { compact = false } = options
  const negative = Number(seconds) < 0
  let value = Math.max(0, Math.floor(Math.abs(Number(seconds))))
  const days = Math.floor(value / 86400)
  value %= 86400
  const hours = Math.floor(value / 3600)
  value %= 3600
  const minutes = Math.floor(value / 60)

  if (compact) {
    const parts = []
    if (days) parts.push(`${days}d`)
    if (hours) parts.push(`${hours}h`)
    if (minutes || parts.length === 0) parts.push(`${minutes}m`)
    return `${negative ? '-' : ''}${parts.join(' ')}`
  }

  const parts = []
  if (days) parts.push(`${days} día${days === 1 ? '' : 's'}`)
  if (hours) parts.push(`${hours} hora${hours === 1 ? '' : 's'}`)
  if (minutes || parts.length === 0) parts.push(`${minutes} minuto${minutes === 1 ? '' : 's'}`)
  return `${negative ? '-' : ''}${parts.join(', ')}`
}

export function getTicketEndDate(ticket, now = new Date()) {
  return toDate(ticket?.closed_at) || toDate(ticket?.resolved_at) || now
}

export function getTicketLifecycleSeconds(ticket, now = new Date()) {
  const createdAt = toDate(ticket?.created_at)
  if (!createdAt) return null
  const endAt = getTicketEndDate(ticket, now)
  return Math.max(0, Math.floor((endAt.getTime() - createdAt.getTime()) / 1000))
}

export function getTicketSlaElapsedSeconds(ticket, now = new Date()) {
  const lifecycleSeconds = getTicketLifecycleSeconds(ticket, now)
  if (lifecycleSeconds === null) return null
  const pausedSeconds = Number(ticket?.sla_paused_seconds || 0)
  return Math.max(0, lifecycleSeconds - pausedSeconds)
}

export function isTicketFinalized(ticket) {
  return ['Resuelto', 'Cerrado'].includes(ticket?.status) || !!ticket?.resolved_at || !!ticket?.closed_at
}

export function getTicketTiming(ticket, now = new Date()) {
  const lifecycleSeconds = getTicketLifecycleSeconds(ticket, now)
  const slaElapsedSeconds = getTicketSlaElapsedSeconds(ticket, now)
  const endAt = getTicketEndDate(ticket, now)
  const finalized = isTicketFinalized(ticket)
  return {
    lifecycleSeconds,
    slaElapsedSeconds,
    lifecycleLabel: formatDurationHuman(lifecycleSeconds),
    lifecycleCompact: formatDurationHuman(lifecycleSeconds, { compact: true }),
    slaElapsedLabel: formatDurationHuman(slaElapsedSeconds),
    slaElapsedCompact: formatDurationHuman(slaElapsedSeconds, { compact: true }),
    finalized,
    endAt,
    measurementLabel: finalized ? 'Tiempo total hasta cierre/resolución' : 'Tiempo transcurrido en curso',
  }
}
