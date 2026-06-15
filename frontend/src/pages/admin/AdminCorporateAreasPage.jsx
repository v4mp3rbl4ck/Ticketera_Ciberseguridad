import { useEffect, useState } from 'react'
import { apiFetch } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'

export default function AdminCorporateAreasPage() {
  const { user } = useAuth()
  const isAdmin = user.role === 'admin'
  const [areas, setAreas] = useState([])
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [form, setForm] = useState({ name: '', description: '' })

  async function load() {
    setError('')
    const data = await apiFetch('/admin/corporate-areas?include_inactive=true')
    setAreas(data)
  }

  useEffect(() => { load().catch(err => setError(err.message)) }, [])

  async function createArea(e) {
    e.preventDefault(); setError(''); setOk('')
    try {
      await apiFetch('/admin/corporate-areas', { method: 'POST', body: JSON.stringify({ ...form, is_active: true }) })
      setOk('Área corporativa creada correctamente')
      setForm({ name: '', description: '' })
      await load()
    } catch (err) { setError(err.message) }
  }

  async function updateArea(id, patch) {
    setError(''); setOk('')
    try {
      await apiFetch(`/admin/corporate-areas/${id}`, { method: 'PATCH', body: JSON.stringify(patch) })
      setOk('Área corporativa actualizada')
      await load()
    } catch (err) { setError(err.message) }
  }

  return (
    <section className="page admin-module-page">
      <div className="page-header"><div><h1>Áreas Corporativas</h1><p>Catálogo de áreas solicitantes utilizado en el formulario de creación de tickets y en métricas Top 10.</p></div></div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert success">{ok}</div>}

      <div className="dashboard-grid">
        {isAdmin && (
        <div className="panel wide admin-card">
          <h2>Crear área corporativa</h2>
          <form className="admin-form areas-form" onSubmit={createArea}>
            <input placeholder="Nombre del área" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
            <input placeholder="Descripción opcional" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
            <button className="primary">Crear área</button>
          </form>
        </div>
        )}

        <div className="panel wide">
          <h2>Catálogo de áreas</h2>
          <table><thead><tr><th>Área</th><th>Descripción</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{areas.map(a => <CorporateAreaRow key={a.id} area={a} canEdit={isAdmin} onSave={updateArea} />)}</tbody></table>
        </div>
      </div>
    </section>
  )
}

function CorporateAreaRow({ area, canEdit, onSave }) {
  const [draft, setDraft] = useState(area)
  useEffect(() => setDraft(area), [area])
  return <tr>
    <td>{canEdit ? <input value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} /> : area.name}</td>
    <td>{canEdit ? <input value={draft.description || ''} onChange={e => setDraft({ ...draft, description: e.target.value })} /> : (area.description || '-')}</td>
    <td>{canEdit ? <select value={draft.is_active ? 'true' : 'false'} onChange={e => setDraft({ ...draft, is_active: e.target.value === 'true' })}><option value="true">Activo</option><option value="false">Inactivo</option></select> : (area.is_active ? 'Activo' : 'Inactivo')}</td>
    <td>{canEdit ? <button className="ghost small" onClick={() => onSave(area.id, { name: draft.name, description: draft.description, is_active: draft.is_active })}>Guardar</button> : '-'}</td>
  </tr>
}
