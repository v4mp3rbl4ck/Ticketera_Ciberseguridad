import { useEffect, useMemo, useState } from 'react'
import { Download, FileBarChart2, RefreshCw } from 'lucide-react'
import { API_URL, apiFetch, getToken } from '../api/client'
import { nowForDatetimeLocal } from '../utils/time'

const severities = ['', 'Crítica/SOS', 'Alta', 'Media', 'Baja']
const statuses = ['', 'Nuevo', 'Asignado', 'En Progreso', 'En Espera', 'Resuelto', 'Cerrado']
const technicalAreas = ['', 'Ciberseguridad', 'Networking']

function defaultDateFrom() {
  const date = new Date()
  date.setDate(date.getDate() - 30)
  return date.toISOString().slice(0, 10)
}

function defaultDateTo() {
  return nowForDatetimeLocal().slice(0, 10)
}

function formatMinutes(value) {
  if (value === null || value === undefined) return 'N/A'
  const minutes = Math.round(Number(value))
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours < 24) return `${hours}h ${mins}m`
  const days = Math.floor(hours / 24)
  return `${days}d ${hours % 24}h ${mins}m`
}

function pct(value) {
  if (value === null || value === undefined) return 'N/A'
  return `${Number(value).toFixed(1)}%`
}

export default function ReportsPage() {
  const [filters, setFilters] = useState({
    date_from: defaultDateFrom(),
    date_to: defaultDateTo(),
    area_destino: '',
    project_area: '',
    severity: '',
    status: '',
    assigned_to_id: '',
  })
  const [summary, setSummary] = useState(null)
  const [corporateAreas, setCorporateAreas] = useState([])
  const [assignees, setAssignees] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const params = useMemo(() => {
    const p = new URLSearchParams()
    if (filters.date_from) p.set('date_from', `${filters.date_from}T00:00:00`)
    if (filters.date_to) p.set('date_to', `${filters.date_to}T23:59:59`)
    if (filters.area_destino) p.set('area_destino', filters.area_destino)
    if (filters.project_area) p.set('project_area', filters.project_area)
    if (filters.severity) p.set('severity', filters.severity)
    if (filters.status) p.set('status', filters.status)
    if (filters.assigned_to_id !== '') p.set('assigned_to_id', filters.assigned_to_id)
    return p
  }, [filters])

  function updateFilter(key, value) {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  async function loadOptions() {
    try {
      const [areas, users] = await Promise.all([
        apiFetch('/admin/corporate-areas').catch(() => []),
        apiFetch('/tickets/assignees').catch(() => []),
      ])
      setCorporateAreas(areas)
      setAssignees(users)
    } catch (_) {}
  }

  async function loadSummary() {
    setError('')
    setLoading(true)
    try {
      const data = await apiFetch(`/reports/summary?${params.toString()}`)
      setSummary(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function download(format) {
    setError('')
    try {
      const response = await fetch(`${API_URL}/reports/monthly.${format}?${params.toString()}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (!response.ok) throw new Error('No se pudo generar el reporte')
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ticketera-reporte-avanzado.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message)
    }
  }

  function resetFilters() {
    setFilters({
      date_from: defaultDateFrom(),
      date_to: defaultDateTo(),
      area_destino: '',
      project_area: '',
      severity: '',
      status: '',
      assigned_to_id: '',
    })
  }

  useEffect(() => { loadOptions() }, [])
  useEffect(() => { loadSummary() }, [])

  const kpis = summary?.kpis || {}

  return (
    <section className="page reports-page">
      <div className="page-header">
        <div>
          <h1>Reportería avanzada</h1>
          <p>Exportación ejecutiva y operacional con filtros por fecha, área, severidad, estado y analista.</p>
        </div>
      </div>

      {error && <div className="alert error">{error}</div>}

      <div className="panel report-filter-panel">
        <div className="report-filter-grid">
          <label>Desde<input type="date" value={filters.date_from} onChange={e => updateFilter('date_from', e.target.value)} /></label>
          <label>Hasta<input type="date" value={filters.date_to} onChange={e => updateFilter('date_to', e.target.value)} /></label>
          <label>Área técnica<select value={filters.area_destino} onChange={e => updateFilter('area_destino', e.target.value)}>{technicalAreas.map(item => <option key={item || 'all'} value={item}>{item || 'Todas'}</option>)}</select></label>
          <label>Área corporativa<select value={filters.project_area} onChange={e => updateFilter('project_area', e.target.value)}><option value="">Todas</option>{corporateAreas.map(area => <option key={area.id} value={area.name}>{area.name}</option>)}</select></label>
          <label>Severidad<select value={filters.severity} onChange={e => updateFilter('severity', e.target.value)}>{severities.map(item => <option key={item || 'all'} value={item}>{item || 'Todas'}</option>)}</select></label>
          <label>Estado<select value={filters.status} onChange={e => updateFilter('status', e.target.value)}>{statuses.map(item => <option key={item || 'all'} value={item}>{item || 'Todos'}</option>)}</select></label>
          <label>Asignado<select value={filters.assigned_to_id} onChange={e => updateFilter('assigned_to_id', e.target.value)}><option value="">Todos</option><option value="0">Sin asignar</option>{assignees.map(user => <option key={user.id} value={user.id}>{user.full_name}</option>)}</select></label>
          <div className="report-filter-actions">
            <button className="button" onClick={loadSummary} disabled={loading}><RefreshCw size={16} /> {loading ? 'Cargando...' : 'Actualizar'}</button>
            <button className="ghost-button" onClick={resetFilters}>Limpiar</button>
          </div>
        </div>
      </div>

      <div className="kpi-grid report-kpis">
        <ReportKpi title="Total" value={kpis.total_tickets ?? 0} />
        <ReportKpi title="Abiertos" value={kpis.open_tickets ?? 0} />
        <ReportKpi title="Finalizados" value={kpis.finished_tickets ?? 0} />
        <ReportKpi title="SLA vencidos" value={kpis.breached_tickets ?? 0} danger={(kpis.breached_tickets ?? 0) > 0} />
        <ReportKpi title="Cumplimiento SLA" value={pct(kpis.sla_compliance_percent)} danger={(kpis.sla_compliance_percent ?? 100) < 85} />
        <ReportKpi title="Vida promedio" value={formatMinutes(kpis.average_ticket_life_minutes)} />
        <ReportKpi title="SLA promedio" value={formatMinutes(kpis.average_sla_consumed_minutes)} />
        <ReportKpi title="MTTR" value={formatMinutes(kpis.mttr_minutes)} />
      </div>

      <div className="panel report-download-panel">
        <div>
          <h2><FileBarChart2 size={20} /> Exportar reporte</h2>
          <p className="panel-help">Los archivos respetan los filtros aplicados y usan la zona horaria configurada del sistema.</p>
        </div>
        <div className="report-download-actions">
          <button className="button" onClick={() => download('pdf')}><Download size={16} /> PDF ejecutivo</button>
          <button className="button ghost" onClick={() => download('xlsx')}><Download size={16} /> Excel avanzado</button>
          <button className="button ghost" onClick={() => download('csv')}><Download size={16} /> CSV operacional</button>
        </div>
      </div>

      <div className="dashboard-grid">
        <DistributionPanel title="Por estado" data={summary?.by_status || {}} />
        <DistributionPanel title="Por severidad" data={summary?.by_severity || {}} />
        <DistributionPanel title="Por área técnica" data={summary?.by_area || {}} />
        <DistributionPanel title="Estado SLA" data={summary?.sla_states || {}} />

        <div className="panel wide">
          <h2>Top 10 áreas solicitantes</h2>
          <table><thead><tr><th>Área</th><th>Tickets</th></tr></thead><tbody>{(summary?.top_requester_areas || []).map(item => <tr key={item.area}><td>{item.area}</td><td>{item.count}</td></tr>)}</tbody></table>
        </div>

        <div className="panel wide">
          <h2>Top 10 casos de uso</h2>
          <table><thead><tr><th>Caso de uso</th><th>Tickets</th></tr></thead><tbody>{(summary?.top_categories || []).map(item => <tr key={item.category}><td>{item.category}</td><td>{item.count}</td></tr>)}</tbody></table>
        </div>

        <div className="panel wide">
          <h2>Muestra de tickets</h2>
          <p className="panel-help">Primeros 20 tickets del reporte, ordenados por creación descendente.</p>
          <table>
            <thead><tr><th>Ticket</th><th>Asunto</th><th>Estado</th><th>Severidad</th><th>Área</th><th>Asignado</th><th>SLA</th></tr></thead>
            <tbody>{(summary?.ticket_sample || []).map(ticket => <tr key={ticket.id}><td>{ticket.ticket_number}</td><td>{ticket.subject}</td><td>{ticket.status}</td><td>{ticket.severity}</td><td>{ticket.project_area}</td><td>{ticket.assigned_to || 'Sin asignar'}</td><td>{ticket.is_sla_breached ? 'Vencido' : 'OK'}</td></tr>)}</tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

function ReportKpi({ title, value, danger }) {
  return <div className={`kpi ${danger ? 'danger' : ''}`}><span>{title}</span><strong>{value}</strong></div>
}

function DistributionPanel({ title, data }) {
  const entries = Object.entries(data)
  return <div className="panel"><h2>{title}</h2>{entries.length === 0 && <p className="panel-help">Sin datos para este filtro.</p>}{entries.map(([key, value]) => <div className="row" key={key}><span>{key}</span><strong>{value}</strong></div>)}</div>
}
