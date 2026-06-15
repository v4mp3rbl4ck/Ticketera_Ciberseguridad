import { useEffect, useState } from 'react'
import { apiFetch } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'
import { severities, technicalAreas } from './adminConstants'

export default function AdminSlaPage() {
  const { user } = useAuth()
  const isAdmin = user.role === 'admin'
  const [sla, setSla] = useState([])
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [slaForm, setSlaForm] = useState({ area: '', severity: 'Media', first_response_minutes: 240, resolution_minutes: 1440, business_hours_only: true, pause_allowed: true, active: true })

  async function load() {
    setError('')
    const data = await apiFetch('/admin/sla')
    setSla(data)
  }

  useEffect(() => { load().catch(err => setError(err.message)) }, [])

  async function createSla(e) {
    e.preventDefault(); setError(''); setOk('')
    try {
      await apiFetch('/admin/sla', { method: 'POST', body: JSON.stringify({ ...slaForm, area: slaForm.area || null }) })
      setOk('SLA creado correctamente')
      await load()
    } catch (err) { setError(err.message) }
  }

  async function updateSla(id, patch) {
    setError(''); setOk('')
    try {
      await apiFetch(`/admin/sla/${id}`, { method: 'PATCH', body: JSON.stringify(patch) })
      setOk('SLA actualizado')
      await load()
    } catch (err) { setError(err.message) }
  }

  return (
    <section className="page admin-module-page">
      <div className="page-header"><div><h1>SLA</h1><p>Configuración de primera respuesta, resolución objetivo, horario laboral y pausa de SLA.</p></div></div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert success">{ok}</div>}

      <div className="dashboard-grid">
        {isAdmin && (
        <div className="panel wide admin-card">
          <h2>Crear política SLA</h2>
          <form className="admin-form" onSubmit={createSla}>
            <select value={slaForm.area} onChange={e => setSlaForm({ ...slaForm, area: e.target.value })}>
              <option value="">Global</option>{technicalAreas.map(a => <option key={a}>{a}</option>)}
            </select>
            <select value={slaForm.severity} onChange={e => setSlaForm({ ...slaForm, severity: e.target.value })}>{severities.filter(s => s !== 'Crítica/SOS').map(s => <option key={s}>{s}</option>)}</select>
            <input type="number" min="1" value={slaForm.first_response_minutes} onChange={e => setSlaForm({ ...slaForm, first_response_minutes: Number(e.target.value) })} placeholder="1ra respuesta min" />
            <input type="number" min="1" value={slaForm.resolution_minutes} onChange={e => setSlaForm({ ...slaForm, resolution_minutes: Number(e.target.value) })} placeholder="Resolución min" />
            <label className="checkline"><input type="checkbox" checked={slaForm.business_hours_only} onChange={e => setSlaForm({ ...slaForm, business_hours_only: e.target.checked })} /> Horario laboral</label>
            <label className="checkline"><input type="checkbox" checked={slaForm.pause_allowed} onChange={e => setSlaForm({ ...slaForm, pause_allowed: e.target.checked })} /> Permite pausa</label>
            <button className="primary">Crear SLA</button>
          </form>
        </div>
        )}

        <div className="panel wide">
          <h2>Políticas existentes</h2>
          <table><thead><tr><th>Severidad</th><th>Área</th><th>1ra respuesta</th><th>Resolución</th><th>Horario laboral</th><th>Pausa</th><th>Activo</th><th>Acción</th></tr></thead><tbody>{sla.map(s => <SlaRow key={s.id} sla={s} canEdit={isAdmin} onSave={updateSla} />)}</tbody></table>
        </div>
      </div>
    </section>
  )
}

function SlaRow({ sla, canEdit, onSave }) {
  const [draft, setDraft] = useState(sla)
  useEffect(() => setDraft(sla), [sla])
  return <tr>
    <td>{canEdit ? <select value={draft.severity} onChange={e => setDraft({ ...draft, severity: e.target.value })}>{severities.filter(s => s !== 'Crítica/SOS').map(s => <option key={s}>{s}</option>)}</select> : sla.severity}</td>
    <td>{canEdit ? <select value={draft.area || ''} onChange={e => setDraft({ ...draft, area: e.target.value || null })}><option value="">Global</option>{technicalAreas.map(a => <option key={a}>{a}</option>)}</select> : (sla.area || 'Global')}</td>
    <td>{canEdit ? <input type="number" min="1" value={draft.first_response_minutes} onChange={e => setDraft({ ...draft, first_response_minutes: Number(e.target.value) })} /> : `${sla.first_response_minutes} min`}</td>
    <td>{canEdit ? <input type="number" min="1" value={draft.resolution_minutes} onChange={e => setDraft({ ...draft, resolution_minutes: Number(e.target.value) })} /> : `${sla.resolution_minutes} min`}</td>
    <td>{canEdit ? <select value={draft.business_hours_only ? 'true' : 'false'} onChange={e => setDraft({ ...draft, business_hours_only: e.target.value === 'true' })}><option value="true">Sí</option><option value="false">No</option></select> : (sla.business_hours_only ? 'Sí' : 'No')}</td>
    <td>{canEdit ? <select value={draft.pause_allowed ? 'true' : 'false'} onChange={e => setDraft({ ...draft, pause_allowed: e.target.value === 'true' })}><option value="true">Sí</option><option value="false">No</option></select> : (sla.pause_allowed ? 'Sí' : 'No')}</td>
    <td>{canEdit ? <select value={draft.active ? 'true' : 'false'} onChange={e => setDraft({ ...draft, active: e.target.value === 'true' })}><option value="true">Sí</option><option value="false">No</option></select> : (sla.active ? 'Sí' : 'No')}</td>
    <td>{canEdit ? <button className="ghost small" onClick={() => onSave(sla.id, draft)}>Guardar</button> : '-'}</td>
  </tr>
}
