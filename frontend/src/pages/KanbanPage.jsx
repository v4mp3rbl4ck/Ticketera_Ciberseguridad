import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, ArrowRight, CalendarClock, Filter, RefreshCcw, Search, UserCheck } from 'lucide-react'
import { apiFetch } from '../api/client'
import Badge, { severityTone, statusTone } from '../components/Badge'
import { useAuth } from '../contexts/AuthContext'
import { formatDateOnly, formatDateTime, getTicketTiming } from '../utils/time'

const STATUSES = ['Nuevo', 'Asignado', 'En Progreso', 'En Espera', 'Resuelto', 'Cerrado']
const NEXT_STATUS = {
  Nuevo: 'Asignado',
  Asignado: 'En Progreso',
  'En Progreso': 'En Espera',
  'En Espera': 'En Progreso',
  Resuelto: 'Cerrado',
}

function fmt(value) {
  return formatDateTime(value)
}

function compactDate(value) {
  return formatDateOnly(value)
}

function slaLabel(ticket) {
  if (ticket.sla_state_label) return ticket.sla_state_label
  if (ticket.is_sla_breached) return 'SLA vencido'
  if (ticket.sla_due_at) return 'SLA activo'
  return 'Sin SLA'
}

function slaTone(ticket) {
  if (ticket.sla_state_tone) return ticket.sla_state_tone
  if (ticket.is_sla_breached) return 'critical'
  return 'info'
}

function normalize(value) {
  return String(value || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

function statusSummary(tickets) {
  return STATUSES.reduce((acc, status) => {
    acc[status] = tickets.filter(ticket => ticket.status === status).length
    return acc
  }, {})
}

function KanbanCard({ ticket, onOpenTicket, onMoveNext, onTake, canManage, now }) {
  const next = NEXT_STATUS[ticket.status]
  const timing = getTicketTiming(ticket, now)
  return (
    <article className={`kanban-card severity-${normalize(ticket.severity).replace(/[^a-z0-9]/g, '-')}`}>
      <div className="kanban-card-top">
        <strong>{ticket.ticket_number}</strong>
        <Badge tone={severityTone(ticket.severity)}>{ticket.severity}</Badge>
      </div>

      <button className="kanban-card-title" onClick={() => onOpenTicket(ticket.id)}>
        {ticket.subject || ticket.category}
      </button>

      <div className="kanban-card-meta">
        <span>{ticket.category}</span>
        <span>{ticket.area_destino} · {ticket.project_area}</span>
      </div>

      <div className="kanban-card-footer">
        <div>
          <small>Solicitante</small>
          <span>{ticket.created_by_name || ticket.created_by_email || `#${ticket.created_by_id}`}</span>
        </div>
        <div>
          <small>Asignado</small>
          <span>{ticket.assigned_to_name || 'Sin asignar'}</span>
        </div>
      </div>

      <div className="kanban-card-dates">
        <span><CalendarClock size={14} /> Creado: {compactDate(ticket.created_at)}</span>
        <span><CalendarClock size={14} /> Tiempo: {timing.lifecycleCompact}</span>
        {ticket.sla_due_at && <span><AlertTriangle size={14} /> SLA: {compactDate(ticket.sla_due_at)}</span>}
        {ticket.sla_due_at && <span><AlertTriangle size={14} /> SLA transcurrido: {timing.slaElapsedCompact}</span>}
      </div>

      {ticket.sla_due_at && (
        <div className="kanban-sla-mini">
          <div className={`sla-progress-track mini ${ticket.sla_state || ''}`}><div style={{ width: `${Math.min(100, Number(ticket.sla_elapsed_percent || 0))}%` }} /></div>
          <Badge tone={slaTone(ticket)}>{slaLabel(ticket)}</Badge>
        </div>
      )}

      <div className="kanban-actions">
        <button className="ghost-button" onClick={() => onOpenTicket(ticket.id)}>Ver detalle</button>
        {canManage && !ticket.assigned_to_id && (
          <button className="ghost-button" onClick={() => onTake(ticket)}>
            Tomar ticket <UserCheck size={14} />
          </button>
        )}
        {canManage && next && (
          <button className="ghost-button primary-lite" onClick={() => onMoveNext(ticket, next)}>
            {next} <ArrowRight size={14} />
          </button>
        )}
      </div>
    </article>
  )
}

export default function KanbanPage({ onOpenTicket }) {
  const { user } = useAuth()
  const canManage = ['admin', 'supervisor', 'analyst'].includes(user.role) || user.permissions?.tickets?.edit
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [now, setNow] = useState(() => new Date())
  const [filters, setFilters] = useState({
    query: '',
    severity: '',
    area: '',
    assignee: '',
    corporateArea: '',
    onlyBreached: false,
  })

  async function load() {
    setLoading(true)
    setError('')
    try {
      const data = await apiFetch('/tickets')
      setTickets(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 60000)
    return () => window.clearInterval(timer)
  }, [])

  const filterOptions = useMemo(() => {
    const severities = Array.from(new Set(tickets.map(t => t.severity).filter(Boolean))).sort()
    const areas = Array.from(new Set(tickets.map(t => t.area_destino).filter(Boolean))).sort()
    const corporateAreas = Array.from(new Set(tickets.map(t => t.project_area).filter(Boolean))).sort()
    const assignees = Array.from(new Map(
      tickets
        .filter(t => t.assigned_to_id)
        .map(t => [t.assigned_to_id, { id: t.assigned_to_id, name: t.assigned_to_name || t.assigned_to_email || `Usuario #${t.assigned_to_id}` }])
    ).values()).sort((a, b) => a.name.localeCompare(b.name))
    return { severities, areas, corporateAreas, assignees }
  }, [tickets])

  const filteredTickets = useMemo(() => {
    const q = normalize(filters.query)
    return tickets.filter(ticket => {
      const text = normalize(`${ticket.ticket_number} ${ticket.subject} ${ticket.category} ${ticket.created_by_name} ${ticket.created_by_email} ${ticket.assigned_to_name} ${ticket.project_area}`)
      if (q && !text.includes(q)) return false
      if (filters.severity && ticket.severity !== filters.severity) return false
      if (filters.area && ticket.area_destino !== filters.area) return false
      if (filters.assignee && String(ticket.assigned_to_id || '') !== String(filters.assignee)) return false
      if (filters.corporateArea && ticket.project_area !== filters.corporateArea) return false
      if (filters.onlyBreached && !ticket.is_sla_breached) return false
      return true
    })
  }, [tickets, filters])

  const grouped = useMemo(() => {
    return STATUSES.reduce((acc, status) => {
      acc[status] = filteredTickets.filter(ticket => ticket.status === status)
      return acc
    }, {})
  }, [filteredTickets])

  const totals = statusSummary(filteredTickets)

  async function moveNext(ticket, nextStatus) {
    try {
      await apiFetch(`/tickets/${ticket.id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: nextStatus, reason: `Actualización rápida desde Kanban: ${ticket.status} → ${nextStatus}` }),
      })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function takeTicket(ticket) {
    try {
      await apiFetch(`/tickets/${ticket.id}/assign`, {
        method: 'PATCH',
        body: JSON.stringify({ assigned_to_id: user.id }),
      })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  function clearFilters() {
    setFilters({ query: '', severity: '', area: '', assignee: '', corporateArea: '', onlyBreached: false })
  }

  return (
    <section className="page kanban-page">
      <div className="page-header">
        <div>
          <span className="eyebrow-line">v1.0.0.20 · Kanban operativo con tiempo de ticket</span>
          <h1>Kanban de Tickets</h1>
          <p>Vista operativa por estado para seguimiento diario de analistas, supervisores y administradores.</p>
        </div>
        <div className="topbar-actions">
          <button className="ghost-button" onClick={clearFilters}>Limpiar filtros</button>
          <button className="button" onClick={load}><RefreshCcw size={16} /> Actualizar</button>
        </div>
      </div>

      {error && <div className="alert error">{error}</div>}

      <div className="kanban-toolbar panel">
        <label className="search-field">
          <Search size={16} />
          <input
            value={filters.query}
            onChange={event => setFilters(prev => ({ ...prev, query: event.target.value }))}
            placeholder="Buscar por ID, asunto, categoría, solicitante o asignado"
          />
        </label>
        <label>
          Severidad
          <select value={filters.severity} onChange={event => setFilters(prev => ({ ...prev, severity: event.target.value }))}>
            <option value="">Todas</option>
            {filterOptions.severities.map(value => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label>
          Área técnica
          <select value={filters.area} onChange={event => setFilters(prev => ({ ...prev, area: event.target.value }))}>
            <option value="">Todas</option>
            {filterOptions.areas.map(value => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label>
          Área corporativa
          <select value={filters.corporateArea} onChange={event => setFilters(prev => ({ ...prev, corporateArea: event.target.value }))}>
            <option value="">Todas</option>
            {filterOptions.corporateAreas.map(value => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label>
          Asignado
          <select value={filters.assignee} onChange={event => setFilters(prev => ({ ...prev, assignee: event.target.value }))}>
            <option value="">Todos</option>
            {filterOptions.assignees.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
        <label className="checkbox-filter">
          <input
            type="checkbox"
            checked={filters.onlyBreached}
            onChange={event => setFilters(prev => ({ ...prev, onlyBreached: event.target.checked }))}
          />
          Solo SLA vencido
        </label>
      </div>

      <div className="kanban-summary-grid">
        {STATUSES.map(status => (
          <div className="kanban-summary-card" key={status}>
            <span>{status}</span>
            <strong>{totals[status] || 0}</strong>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="panel">Cargando tablero...</div>
      ) : (
        <div className="kanban-board" role="list" aria-label="Tablero Kanban de tickets">
          {STATUSES.map(status => (
            <section className="kanban-column" key={status}>
              <div className="kanban-column-header">
                <div>
                  <Badge tone={statusTone(status)}>{status}</Badge>
                  <strong>{grouped[status]?.length || 0}</strong>
                </div>
                <Filter size={15} />
              </div>
              <div className="kanban-column-body">
                {(grouped[status] || []).map(ticket => (
                  <KanbanCard
                    key={ticket.id}
                    ticket={ticket}
                    onOpenTicket={onOpenTicket}
                    onMoveNext={moveNext}
                    onTake={takeTicket}
                    canManage={canManage}
                    now={now}
                  />
                ))}
                {grouped[status]?.length === 0 && (
                  <div className="kanban-empty">Sin tickets en este estado.</div>
                )}
              </div>
            </section>
          ))}
        </div>
      )}

      <div className="panel kanban-help-panel">
        <UserCheck size={18} />
        <div>
          <strong>Uso recomendado</strong>
          <p>Usa este tablero para la revisión diaria. Los cambios rápidos dejan trazabilidad en la línea de tiempo del ticket mediante una nota de sistema.</p>
        </div>
      </div>
    </section>
  )
}
