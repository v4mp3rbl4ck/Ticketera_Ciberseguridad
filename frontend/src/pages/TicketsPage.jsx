import { useEffect, useState } from 'react'
import { API_URL, apiFetch, getToken } from '../api/client'
import Badge, { statusTone } from '../components/Badge'
import { formatDateTime, getTicketTiming } from '../utils/time'
import { useAuth } from '../contexts/AuthContext'

function fmt(value) {
  return formatDateTime(value)
}

function slaText(ticket) {
  if (ticket.sla_state_label) return ticket.sla_state_label
  if (ticket.is_sla_breached) return 'SLA vencido'
  if (ticket.sla_due_at) return 'SLA activo'
  return null
}

export default function TicketsPage({ onOpenTicket }) {
  const { user } = useAuth()
  const canExport = ['admin', 'supervisor', 'analyst'].includes(user.role)
  const [tickets, setTickets] = useState([])
  const [error, setError] = useState('')
  const [now, setNow] = useState(() => new Date())

  async function load() {
    try {
      setTickets(await apiFetch('/tickets'))
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => { load() }, [])
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 60000)
    return () => window.clearInterval(timer)
  }, [])

  async function exportCsv() {
    const res = await fetch(`${API_URL}/tickets/export.csv`, { headers: { Authorization: `Bearer ${getToken()}` } })
    if (!res.ok) {
      setError('No se pudo exportar el CSV')
      return
    }
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tickets.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Bandeja de Tickets</h1>
          <p>Listado operativo con trazabilidad de creación, actualización, asignación y resolución.</p>
        </div>
        {canExport && <button className="button" onClick={exportCsv}>Exportar CSV</button>}
      </div>
      {error && <div className="alert error">{error}</div>}
      <div className="ticket-table enterprise-ticket-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Categoría</th>
              <th>Creador / Solicitante</th>
              <th>Asignado</th>
              <th>Creación</th>
              <th>Última actualización</th>
              <th>Resolución</th>
              <th>Tiempo del ticket</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map(ticket => {
              const timing = getTicketTiming(ticket, now)
              return (
              <tr key={ticket.id} onClick={() => onOpenTicket(ticket.id)}>
                <td><strong>{ticket.ticket_number}</strong><br /><small>#{ticket.id}</small></td>
                <td>{ticket.category}<br /><small>{ticket.area_destino} · {ticket.severity}</small></td>
                <td>{ticket.created_by_name || ticket.created_by_email || ticket.created_by_id}<br /><small>{ticket.project_area}</small></td>
                <td>{ticket.assigned_to_name || 'Sin asignar'}<br /><small>{ticket.assigned_to_email || ''}</small></td>
                <td>{fmt(ticket.created_at)}</td>
                <td>{fmt(ticket.updated_at)}</td>
                <td>{fmt(ticket.resolved_at)}</td>
                <td>
                  <strong>{timing.lifecycleCompact}</strong>
                  <br />
                  <small>SLA: {timing.slaElapsedCompact}</small>
                  <br />
                  <small>{timing.finalized ? 'Finalizado' : 'En curso'}</small>
                </td>
                <td><Badge tone={statusTone(ticket.status)}>{ticket.status}</Badge>{slaText(ticket) && <><br /><Badge tone={ticket.sla_state_tone || (ticket.is_sla_breached ? "critical" : "info")}>{slaText(ticket)}</Badge></>}</td>
              </tr>
              )
            })}
            {tickets.length === 0 && <tr><td colSpan="9">No hay tickets para mostrar.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  )
}
