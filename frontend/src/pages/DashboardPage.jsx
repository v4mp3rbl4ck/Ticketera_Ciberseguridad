import { useEffect, useMemo, useState } from 'react'
import { API_URL, apiFetch, getToken } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { APP_TIMEZONE, nowForDatetimeLocal } from '../utils/time'

function toInputDate(date) {
  const parts = new Intl.DateTimeFormat('sv-SE', { timeZone: APP_TIMEZONE, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(date)
  const obj = Object.fromEntries(parts.map(part => [part.type, part.value]))
  return `${obj.year}-${obj.month}-${obj.day}`
}

function pct(value) {
  if (value === null || value === undefined) return 'N/A'
  return `${Number(value).toFixed(1)}%`
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [dateFrom, setDateFrom] = useState(() => {
    const date = new Date()
    date.setDate(date.getDate() - 30)
    return toInputDate(date)
  })
  const [dateTo, setDateTo] = useState(() => nowForDatetimeLocal().slice(0, 10))

  async function load() {
    setError('')
    const params = new URLSearchParams()
    if (dateFrom) params.set('date_from', `${dateFrom}T00:00:00`)
    if (dateTo) params.set('date_to', `${dateTo}T23:59:59`)
    apiFetch(`/metrics/dashboard?${params.toString()}`).then(setData).catch(err => setError(err.message))
  }

  useEffect(() => { load() }, [])

  function reportUrl(format) {
    const params = new URLSearchParams()
    if (dateFrom) params.set('date_from', `${dateFrom}T00:00:00`)
    if (dateTo) params.set('date_to', `${dateTo}T23:59:59`)
    return `${API_URL}/reports/monthly.${format}?${params.toString()}`
  }

  async function downloadReport(format) {
    const res = await fetch(reportUrl(format), { headers: { Authorization: `Bearer ${getToken()}` } })
    if (!res.ok) throw new Error('No se pudo generar el reporte')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ticketera-reporte.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const statusEntries = useMemo(() => Object.entries(data?.by_status || {}), [data])
  const maxStatus = Math.max(1, ...statusEntries.map(([, value]) => value))

  if (error) return <section className="page"><h1>Dashboard</h1><div className="alert error">{error}</div></section>
  if (!data) return <section className="page"><h1>Dashboard</h1><p>Cargando métricas...</p></section>

  const k = data.kpis
  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>Dashboard Operativo</h1>
          <p>Vista por rango de fecha, estados, carga operacional y tickets propios.</p>
        </div>
        <div className="date-filter">
          <label>Desde<input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} /></label>
          <label>Hasta<input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} /></label>
          <button className="button" onClick={load}>Buscar</button>
          {['admin', 'supervisor', 'analyst'].includes(user.role) && (
            <div className="report-actions">
              <button className="button ghost" onClick={() => downloadReport('pdf')}>PDF</button>
              <button className="button ghost" onClick={() => downloadReport('xlsx')}>Excel</button>
              <button className="button ghost" onClick={() => downloadReport('csv')}>CSV</button>
            </div>
          )}
        </div>
      </div>

      <div className="kpi-grid wide-kpis">
        <Kpi title="Total de Tickets" subtitle="Todos los tickets registrados" value={k.total_tickets} />
        <Kpi title="Tickets Abiertos" value={k.open_tickets} />
        <Kpi title="Tickets Resueltos" value={k.resolved_tickets} />
        <Kpi title="Tickets Cerrados" value={k.closed_tickets} />
        <Kpi title="Tickets Finalizados" value={k.finished_tickets} />
        <Kpi title="Tickets Vencidos" value={k.breached_tickets} danger={k.breached_tickets > 0} />
      </div>

      <div className="kpi-grid sla-kpis">
        <Kpi title="Cumplimiento SLA" subtitle="Resoluciones dentro del objetivo" value={pct(k.sla_compliance_percent)} danger={k.sla_compliance_percent < 85} />
        <Kpi title="SLA 75%" subtitle="Tickets en advertencia" value={k.sla_warning_75 || 0} danger={(k.sla_warning_75 || 0) > 0} />
        <Kpi title="SLA 90%" subtitle="Tickets en riesgo alto" value={k.sla_warning_90 || 0} danger={(k.sla_warning_90 || 0) > 0} />
        <Kpi title="SLA Pausado" subtitle="Tickets en espera" value={k.sla_paused_tickets || 0} />
        <Kpi title="1ra respuesta vencida" subtitle="Atención inicial fuera de SLA" value={k.first_response_breached || 0} danger={(k.first_response_breached || 0) > 0} />
      </div>

      <div className="dashboard-grid">
        <div className="panel wide sla-overview-panel">
          <h2>Control SLA avanzado</h2>
          <p className="panel-help">Seguimiento de cumplimiento, advertencias 75/90%, tickets pausados y vencimiento de primera respuesta.</p>
          <div className="sla-overview-grid">
            <SlaMetric label="Cumplimiento" value={pct(k.sla_compliance_percent)} tone={k.sla_compliance_percent >= 90 ? 'success' : k.sla_compliance_percent >= 75 ? 'warning' : 'critical'} />
            <SlaMetric label="Vencidos" value={k.breached_tickets} tone={k.breached_tickets > 0 ? 'critical' : 'success'} />
            <SlaMetric label="Advertencia 75%" value={k.sla_warning_75 || 0} tone={(k.sla_warning_75 || 0) > 0 ? 'warning' : 'success'} />
            <SlaMetric label="Riesgo 90%" value={k.sla_warning_90 || 0} tone={(k.sla_warning_90 || 0) > 0 ? 'danger' : 'success'} />
            <SlaMetric label="Pausados" value={k.sla_paused_tickets || 0} tone="info" />
            <SlaMetric label="Primera respuesta vencida" value={k.first_response_breached || 0} tone={(k.first_response_breached || 0) > 0 ? 'critical' : 'success'} />
          </div>
        </div>

        <div className="panel wide">
          <h2>Estado de tickets</h2>
          <p className="panel-help">Distribución por estado dentro del rango seleccionado.</p>
          <div className="bar-chart">
            {statusEntries.length === 0 && <p>No hay tickets en este rango.</p>}
            {statusEntries.map(([status, count]) => (
              <div className="bar-row" key={status}>
                <span>{status}</span>
                <div className="bar-track"><div className="bar-fill" style={{ width: `${(count / maxStatus) * 100}%` }} /></div>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <h2>Mi dashboard</h2>
          <p className="panel-help">{user.role === 'requester' ? 'Tickets solicitados por tu cuenta.' : 'Tickets asignados a tu usuario.'}</p>
          <div className="mini-kpis">
            <Kpi title="Total" value={data.my_tickets.total} />
            <Kpi title="Pendientes" value={data.my_tickets.pending} />
            <Kpi title="En revisión" value={data.my_tickets.in_review} />
            <Kpi title="Completados" value={data.my_tickets.completed} />
          </div>
        </div>

        <Panel title="Por Severidad" data={data.by_severity} />
        <Panel title="Por Área Técnica" data={data.by_area} />

        <div className="panel wide">
          <h2>Top 10 Áreas Solicitantes</h2>
          <p className="panel-help">Cantidad de tickets solicitados por área corporativa.</p>
          <table>
            <thead><tr><th>Área corporativa</th><th>Tickets</th></tr></thead>
            <tbody>{data.top_requester_areas.map(item => <tr key={item.area}><td>{item.area}</td><td>{item.count}</td></tr>)}</tbody>
          </table>
        </div>

        <div className="panel">
          <h2>Top 10 Categorías</h2>
          {data.top_categories.map(item => <div className="row" key={item.category}><span>{item.category}</span><strong>{item.count}</strong></div>)}
        </div>

        <div className="panel wide">
          <h2>Carga por Analista</h2>
          <table>
            <thead><tr><th>Analista</th><th>Activos</th><th>Resueltos/Cerrados</th></tr></thead>
            <tbody>{data.analyst_workload.map(row => <tr key={row.analyst_id}><td>{row.analyst}</td><td>{row.active}</td><td>{row.resolved}</td></tr>)}</tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

function Kpi({ title, value, danger, subtitle }) {
  return <div className={`kpi ${danger ? 'danger' : ''}`}><span>{title}</span><strong>{value}</strong>{subtitle && <small>{subtitle}</small>}</div>
}

function SlaMetric({ label, value, tone }) {
  return <div className={`sla-metric ${tone || ''}`}><span>{label}</span><strong>{value}</strong></div>
}

function Panel({ title, data }) {
  return <div className="panel"><h2>{title}</h2>{Object.entries(data).map(([key, value]) => <div className="row" key={key}><span>{key}</span><strong>{value}</strong></div>)}</div>
}
