import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../api/client'
import { formatDateTime } from '../utils/time'
import { useAuth } from '../contexts/AuthContext'

const severities = ['Crítica/SOS', 'Alta', 'Media', 'Baja']
const technicalAreas = ['Ciberseguridad', 'Networking']
const roles = ['requester', 'analyst', 'supervisor', 'admin']

export default function AdminPage() {
  const { user } = useAuth()
  const isAdmin = user.role === 'admin'
  const canManageCatalog = ['admin', 'analyst'].includes(user.role)
  const [users, setUsers] = useState([])
  const [sla, setSla] = useState([])
  const [audit, setAudit] = useState([])
  const [categories, setCategories] = useState([])
  const [corporateAreas, setCorporateAreas] = useState([])
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [userForm, setUserForm] = useState({ full_name: '', email: '', password: '', role: 'requester', area: '' })
  const [categoryForm, setCategoryForm] = useState({ area: 'Ciberseguridad', severity: 'Media', name: '', description: '' })
  const [slaForm, setSlaForm] = useState({ area: '', severity: 'Media', first_response_minutes: 240, resolution_minutes: 1440, business_hours_only: true, pause_allowed: true, active: true })
  const [categoryFilter, setCategoryFilter] = useState({ area: '', severity: '' })

  async function load() {
    setError('')
    const [u, s, a, c, ca] = await Promise.all([
      apiFetch('/admin/users').catch(() => []),
      apiFetch('/admin/sla').catch(() => []),
      apiFetch('/admin/audit').catch(() => []),
      apiFetch('/admin/categories?include_inactive=true').catch(() => []),
      apiFetch('/admin/corporate-areas').catch(() => []),
    ])
    setUsers(u); setSla(s); setAudit(a); setCategories(c); setCorporateAreas(ca)
  }

  useEffect(() => {
    load().catch(err => setError(err.message))
  }, [])

  const filteredCategories = useMemo(() => {
    return categories.filter(c => (!categoryFilter.area || c.area === categoryFilter.area) && (!categoryFilter.severity || c.severity === categoryFilter.severity))
  }, [categories, categoryFilter])

  async function createUser(e) {
    e.preventDefault(); setError(''); setOk('')
    try {
      const payload = { ...userForm, area: userForm.area || null }
      await apiFetch('/admin/users', { method: 'POST', body: JSON.stringify(payload) })
      setOk('Usuario creado correctamente')
      setUserForm({ full_name: '', email: '', password: '', role: 'requester', area: '' })
      await load()
    } catch (err) { setError(err.message) }
  }

  async function createCategory(e) {
    e.preventDefault(); setError(''); setOk('')
    try {
      await apiFetch('/admin/categories', { method: 'POST', body: JSON.stringify({ ...categoryForm, is_active: true }) })
      setOk('Caso de uso guardado en el catálogo dinámico')
      setCategoryForm({ ...categoryForm, name: '', description: '' })
      await load()
    } catch (err) { setError(err.message) }
  }

  async function updateCategory(id, patch) {
    setError(''); setOk('')
    try {
      await apiFetch(`/admin/categories/${id}`, { method: 'PATCH', body: JSON.stringify(patch) })
      setOk('Caso de uso actualizado')
      await load()
    } catch (err) { setError(err.message) }
  }

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
    <section className="page admin-page">
      <h1>Administración</h1>
      <p>Gestión de usuarios, roles, SLA, casos de uso dinámicos y auditoría inmutable.</p>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert success">{ok}</div>}

      <div className="dashboard-grid">
        {isAdmin && (
          <div className="panel wide admin-card">
            <h2>Crear usuario</h2>
            <form className="admin-form" onSubmit={createUser}>
              <input placeholder="Nombre completo" value={userForm.full_name} onChange={e => setUserForm({ ...userForm, full_name: e.target.value })} required />
              <input placeholder="Correo" value={userForm.email} onChange={e => setUserForm({ ...userForm, email: e.target.value })} required />
              <input placeholder="Contraseña temporal" type="password" value={userForm.password} onChange={e => setUserForm({ ...userForm, password: e.target.value })} required />
              <select value={userForm.role} onChange={e => setUserForm({ ...userForm, role: e.target.value })}>{roles.map(r => <option key={r}>{r}</option>)}</select>
              <select value={userForm.area} onChange={e => setUserForm({ ...userForm, area: e.target.value })}>
                <option value="">Área global / solicitante</option>
                {technicalAreas.map(a => <option key={a}>{a}</option>)}
              </select>
              <button className="primary">Crear usuario</button>
            </form>
          </div>
        )}

        <div className="panel wide">
          <h2>Usuarios</h2>
          <table><thead><tr><th>Nombre</th><th>Correo</th><th>Rol</th><th>Área técnica</th><th>Activo</th></tr></thead><tbody>{users.map(u => <tr key={u.id}><td>{u.full_name}</td><td>{u.email}</td><td>{u.role}</td><td>{u.area || 'Global'}</td><td>{u.is_active ? 'Sí' : 'No'}</td></tr>)}</tbody></table>
        </div>

        {canManageCatalog && (
          <div className="panel wide admin-card">
            <h2>Añadir caso de uso</h2>
            <p className="panel-help">El caso se mostrará solo dentro de su Área técnica + Severidad. Así se evita un menú gigante.</p>
            <form className="admin-form catalog-form" onSubmit={createCategory}>
              <select value={categoryForm.area} onChange={e => setCategoryForm({ ...categoryForm, area: e.target.value })}>{technicalAreas.map(a => <option key={a}>{a}</option>)}</select>
              <select value={categoryForm.severity} onChange={e => setCategoryForm({ ...categoryForm, severity: e.target.value })}>{severities.map(s => <option key={s}>{s}</option>)}</select>
              <input placeholder="Nuevo caso de uso" value={categoryForm.name} onChange={e => setCategoryForm({ ...categoryForm, name: e.target.value })} required />
              <input placeholder="Descripción opcional" value={categoryForm.description} onChange={e => setCategoryForm({ ...categoryForm, description: e.target.value })} />
              <button className="primary">Guardar caso</button>
            </form>
          </div>
        )}

        <div className="panel wide">
          <h2>Catálogo dinámico de casos de uso</h2>
          <div className="table-toolbar">
            <select value={categoryFilter.area} onChange={e => setCategoryFilter({ ...categoryFilter, area: e.target.value })}>
              <option value="">Todas las áreas técnicas</option>
              {technicalAreas.map(a => <option key={a}>{a}</option>)}
            </select>
            <select value={categoryFilter.severity} onChange={e => setCategoryFilter({ ...categoryFilter, severity: e.target.value })}>
              <option value="">Todas las severidades</option>
              {severities.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <table><thead><tr><th>Área</th><th>Severidad</th><th>Caso de uso</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{filteredCategories.map(c => <CategoryRow key={c.id} category={c} canEdit={canManageCatalog} onSave={updateCategory} />)}</tbody></table>
        </div>

        {isAdmin && (
          <div className="panel wide admin-card">
            <h2>Crear SLA</h2>
            <form className="admin-form" onSubmit={createSla}>
              <select value={slaForm.area} onChange={e => setSlaForm({ ...slaForm, area: e.target.value })}>
                <option value="">Global</option>
                {technicalAreas.map(a => <option key={a}>{a}</option>)}
              </select>
              <select value={slaForm.severity} onChange={e => setSlaForm({ ...slaForm, severity: e.target.value })}>{severities.filter(s => s !== 'Crítica/SOS').map(s => <option key={s}>{s}</option>)}</select>
              <input type="number" min="1" value={slaForm.first_response_minutes} onChange={e => setSlaForm({ ...slaForm, first_response_minutes: Number(e.target.value) })} />
              <input type="number" min="1" value={slaForm.resolution_minutes} onChange={e => setSlaForm({ ...slaForm, resolution_minutes: Number(e.target.value) })} />
              <label className="checkline"><input type="checkbox" checked={slaForm.business_hours_only} onChange={e => setSlaForm({ ...slaForm, business_hours_only: e.target.checked })} /> Horario laboral</label>
              <button className="primary">Crear SLA</button>
            </form>
          </div>
        )}

        <div className="panel wide">
          <h2>SLA</h2>
          <table><thead><tr><th>Severidad</th><th>Área</th><th>1ra respuesta</th><th>Resolución</th><th>Horario laboral</th><th>Acción</th></tr></thead><tbody>{sla.map(s => <SlaRow key={s.id} sla={s} canEdit={isAdmin} onSave={updateSla} />)}</tbody></table>
        </div>

        <div className="panel wide">
          <h2>Top áreas corporativas disponibles</h2>
          <p className="panel-help">Estas áreas se muestran al solicitante al crear tickets.</p>
          <div className="tag-list">{corporateAreas.map(a => <span key={a}>{a}</span>)}</div>
        </div>

        <div className="panel wide">
          <h2>Auditoría reciente</h2>
          <table><thead><tr><th>Fecha</th><th>Actor</th><th>Rol</th><th>Entidad</th><th>Acción</th><th>Valor</th><th>Hash</th></tr></thead><tbody>{audit.slice(0, 80).map(a => <tr key={a.id}><td>{formatDateTime(a.timestamp)}</td><td>{a.actor_user_id}</td><td>{a.actor_role}</td><td>{a.entity_type}:{a.entity_id}</td><td>{a.action}</td><td>{a.new_value || a.old_value || '-'}</td><td><code>{String(a.current_hash).slice(0, 12)}...</code></td></tr>)}</tbody></table>
        </div>
      </div>
    </section>
  )
}

function CategoryRow({ category, canEdit, onSave }) {
  const [draft, setDraft] = useState(category)
  useEffect(() => setDraft(category), [category])
  return <tr>
    <td>{canEdit ? <select value={draft.area} onChange={e => setDraft({ ...draft, area: e.target.value })}>{technicalAreas.map(a => <option key={a}>{a}</option>)}</select> : category.area}</td>
    <td>{canEdit ? <select value={draft.severity} onChange={e => setDraft({ ...draft, severity: e.target.value })}>{severities.map(s => <option key={s}>{s}</option>)}</select> : category.severity}</td>
    <td>{canEdit ? <input value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} /> : category.name}</td>
    <td>{canEdit ? <select value={draft.is_active ? 'true' : 'false'} onChange={e => setDraft({ ...draft, is_active: e.target.value === 'true' })}><option value="true">Activo</option><option value="false">Inactivo</option></select> : (category.is_active ? 'Activo' : 'Inactivo')}</td>
    <td>{canEdit ? <button className="ghost small" onClick={() => onSave(category.id, { area: draft.area, severity: draft.severity, name: draft.name, is_active: draft.is_active, description: draft.description })}>Guardar</button> : '-'}</td>
  </tr>
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
    <td>{canEdit ? <button className="ghost small" onClick={() => onSave(sla.id, draft)}>Guardar</button> : '-'}</td>
  </tr>
}
