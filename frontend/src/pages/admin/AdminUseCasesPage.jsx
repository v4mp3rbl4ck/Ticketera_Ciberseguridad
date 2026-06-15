import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'
import { severities, technicalAreas } from './adminConstants'

export default function AdminUseCasesPage() {
  const { user } = useAuth()
  const canManage = ['admin', 'analyst'].includes(user.role)
  const [categories, setCategories] = useState([])
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [categoryForm, setCategoryForm] = useState({ area: 'Ciberseguridad', severity: 'Media', name: '', description: '' })
  const [categoryFilter, setCategoryFilter] = useState({ area: '', severity: '' })

  async function load() {
    setError('')
    const data = await apiFetch('/admin/categories?include_inactive=true')
    setCategories(data)
  }

  useEffect(() => { load().catch(err => setError(err.message)) }, [])

  const filteredCategories = useMemo(() => {
    return categories.filter(c => (!categoryFilter.area || c.area === categoryFilter.area) && (!categoryFilter.severity || c.severity === categoryFilter.severity))
  }, [categories, categoryFilter])

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

  return (
    <section className="page admin-module-page">
      <div className="page-header"><div><h1>Casos de Uso</h1><p>Catálogo dinámico separado por área técnica y severidad. Evita menús gigantes en la creación de tickets.</p></div></div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert success">{ok}</div>}

      <div className="dashboard-grid">
        {canManage && (
          <div className="panel wide admin-card">
            <h2>Añadir caso de uso</h2>
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
          <h2>Catálogo existente</h2>
          <div className="table-toolbar">
            <select value={categoryFilter.area} onChange={e => setCategoryFilter({ ...categoryFilter, area: e.target.value })}>
              <option value="">Todas las áreas técnicas</option>{technicalAreas.map(a => <option key={a}>{a}</option>)}
            </select>
            <select value={categoryFilter.severity} onChange={e => setCategoryFilter({ ...categoryFilter, severity: e.target.value })}>
              <option value="">Todas las severidades</option>{severities.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <table>
            <thead><tr><th>Área</th><th>Severidad</th><th>Caso de uso</th><th>Descripción</th><th>Estado</th><th>Acción</th></tr></thead>
            <tbody>{filteredCategories.map(c => <CategoryRow key={c.id} category={c} canEdit={canManage} onSave={updateCategory} />)}</tbody>
          </table>
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
    <td>{canEdit ? <input value={draft.description || ''} onChange={e => setDraft({ ...draft, description: e.target.value })} /> : (category.description || '-')}</td>
    <td>{canEdit ? <select value={draft.is_active ? 'true' : 'false'} onChange={e => setDraft({ ...draft, is_active: e.target.value === 'true' })}><option value="true">Activo</option><option value="false">Inactivo</option></select> : (category.is_active ? 'Activo' : 'Inactivo')}</td>
    <td>{canEdit ? <button className="ghost small" onClick={() => onSave(category.id, { area: draft.area, severity: draft.severity, name: draft.name, description: draft.description, is_active: draft.is_active })}>Guardar</button> : '-'}</td>
  </tr>
}
