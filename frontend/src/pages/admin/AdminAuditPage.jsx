import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../../api/client'
import { formatDateTime } from '../../utils/time'

const entityTypes = ['', 'ticket', 'user', 'role', 'category', 'required_question', 'sla_policy', 'corporate_area', 'sos_event']

function toParamDate(value, end = false) {
  if (!value) return ''
  return `${value}${end ? 'T23:59:59' : 'T00:00:00'}`
}

export default function AdminAuditPage() {
  const [audit, setAudit] = useState([])
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({
    actor_user_id: '',
    action: '',
    entity_type: '',
    entity_id: '',
    date_from: '',
    date_to: '',
    limit: '500',
  })

  const queryString = useMemo(() => {
    const params = new URLSearchParams()
    if (filters.actor_user_id) params.set('actor_user_id', filters.actor_user_id)
    if (filters.action) params.set('action', filters.action)
    if (filters.entity_type) params.set('entity_type', filters.entity_type)
    if (filters.entity_id) params.set('entity_id', filters.entity_id)
    if (filters.date_from) params.set('date_from', toParamDate(filters.date_from))
    if (filters.date_to) params.set('date_to', toParamDate(filters.date_to, true))
    if (filters.limit) params.set('limit', filters.limit)
    return params.toString()
  }, [filters])

  async function load() {
    setError('')
    const data = await apiFetch(`/admin/audit?${queryString}`)
    setAudit(data)
  }

  useEffect(() => { load().catch(err => setError(err.message)) }, [])

  function updateFilter(key, value) {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  function clearFilters() {
    setFilters({ actor_user_id: '', action: '', entity_type: '', entity_id: '', date_from: '', date_to: '', limit: '500' })
  }

  return (
    <section className="page admin-module-page">
      <div className="page-header">
        <div><h1>Auditoría</h1><p>Registro inmutable de actividad: quién hizo qué, cuándo y sobre qué entidad.</p></div>
        <button className="ghost" onClick={() => load().catch(err => setError(err.message))}>Actualizar</button>
      </div>
      {error && <div className="alert error">{error}</div>}

      <div className="panel wide audit-filter-panel">
        <h2>Filtros de auditoría</h2>
        <div className="audit-filter-grid">
          <div><label>Usuario ID</label><input value={filters.actor_user_id} onChange={e => updateFilter('actor_user_id', e.target.value)} placeholder="Ej: 1" /></div>
          <div><label>Acción</label><input value={filters.action} onChange={e => updateFilter('action', e.target.value)} placeholder="create, update, status_change" /></div>
          <div><label>Entidad</label><select value={filters.entity_type} onChange={e => updateFilter('entity_type', e.target.value)}>{entityTypes.map(type => <option key={type} value={type}>{type || 'Todas'}</option>)}</select></div>
          <div><label>Entidad ID</label><input value={filters.entity_id} onChange={e => updateFilter('entity_id', e.target.value)} placeholder="Ej: 15" /></div>
          <div><label>Desde</label><input type="date" value={filters.date_from} onChange={e => updateFilter('date_from', e.target.value)} /></div>
          <div><label>Hasta</label><input type="date" value={filters.date_to} onChange={e => updateFilter('date_to', e.target.value)} /></div>
          <div><label>Límite</label><select value={filters.limit} onChange={e => updateFilter('limit', e.target.value)}><option>100</option><option>250</option><option>500</option><option>1000</option></select></div>
          <div className="audit-filter-actions"><button className="primary" onClick={() => load().catch(err => setError(err.message))}>Buscar</button><button className="ghost" onClick={clearFilters}>Limpiar</button></div>
        </div>
      </div>

      <div className="panel wide">
        <h2>Eventos recientes</h2>
        <table>
          <thead><tr><th>Fecha</th><th>Actor</th><th>Rol</th><th>Entidad</th><th>Acción</th><th>Valor</th><th>Hash</th></tr></thead>
          <tbody>
            {audit.map(a => <tr key={a.id}><td>{formatDateTime(a.timestamp)}</td><td>{a.actor_user_id || '-'}</td><td>{a.actor_role || '-'}</td><td>{a.entity_type}:{a.entity_id}</td><td>{a.action}</td><td>{a.new_value || a.old_value || '-'}</td><td><code>{String(a.current_hash).slice(0, 16)}...</code></td></tr>)}
            {audit.length === 0 && <tr><td colSpan="7">No hay eventos para los filtros seleccionados.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  )
}
