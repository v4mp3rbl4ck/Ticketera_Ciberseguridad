import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../../api/client'

const severities = ['Crítica/SOS', 'Alta', 'Media', 'Baja']
const areas = ['Ciberseguridad', 'Networking']

export default function AdminQuestionsPage() {
  const [items, setItems] = useState([])
  const [categories, setCategories] = useState([])
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [filter, setFilter] = useState({ area: 'Ciberseguridad', severity: 'Media', category: '*' })
  const [form, setForm] = useState({ question_text: '', required: true, sort_order: 1 })

  async function load() {
    setError('')
    const params = new URLSearchParams()
    if (filter.area) params.set('area', filter.area)
    if (filter.severity) params.set('severity', filter.severity)
    if (filter.category) params.set('category', filter.category)
    params.set('include_inactive', 'true')
    try {
      setItems(await apiFetch(`/admin/required-questions?${params.toString()}`))
      setCategories(await apiFetch(`/admin/categories?area=${encodeURIComponent(filter.area)}&severity=${encodeURIComponent(filter.severity)}&include_inactive=false`))
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => { load() }, [filter.area, filter.severity, filter.category])

  const categoryOptions = useMemo(() => ['*', ...categories.map(c => c.name)], [categories])

  async function create(e) {
    e.preventDefault()
    setError(''); setOk('')
    try {
      await apiFetch('/admin/required-questions', {
        method: 'POST',
        body: JSON.stringify({
          area: filter.area,
          severity: filter.severity,
          category: filter.category,
          question_text: form.question_text,
          required: form.required,
          sort_order: Number(form.sort_order || 0),
          is_active: true,
        }),
      })
      setForm({ question_text: '', required: true, sort_order: Number(form.sort_order || 0) + 1 })
      setOk('Pregunta creada correctamente')
      load()
    } catch (err) { setError(err.message) }
  }

  async function update(item, patch) {
    setError(''); setOk('')
    try {
      await apiFetch(`/admin/required-questions/${item.id}`, { method: 'PATCH', body: JSON.stringify(patch) })
      setOk('Pregunta actualizada')
      load()
    } catch (err) { setError(err.message) }
  }

  async function remove(item) {
    if (!confirm('¿Eliminar definitivamente esta pregunta requerida?')) return
    await apiFetch(`/admin/required-questions/${item.id}`, { method: 'DELETE' })
    load()
  }

  return (
    <section className="page admin-module-page">
      <div className="page-header">
        <div>
          <h1>Preguntas Requeridas</h1>
          <p>Administra las preguntas dinámicas por área técnica, severidad y caso de uso. Usa categoría <strong>*</strong> como plantilla general.</p>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert success">{ok}</div>}

      <div className="panel admin-card">
        <h2>Filtros de matriz</h2>
        <div className="admin-form questions-filter">
          <div><label>Área técnica</label><select value={filter.area} onChange={e => setFilter(prev => ({ ...prev, area: e.target.value, category: '*' }))}>{areas.map(a => <option key={a}>{a}</option>)}</select></div>
          <div><label>Severidad</label><select value={filter.severity} onChange={e => setFilter(prev => ({ ...prev, severity: e.target.value, category: '*' }))}>{severities.map(s => <option key={s}>{s}</option>)}</select></div>
          <div><label>Caso de uso</label><select value={filter.category} onChange={e => setFilter(prev => ({ ...prev, category: e.target.value }))}>{categoryOptions.map(c => <option value={c} key={c}>{c === '*' ? '* · Plantilla general' : c}</option>)}</select></div>
        </div>
      </div>

      <div className="panel admin-card">
        <h2>Añadir pregunta</h2>
        <form className="admin-form question-form" onSubmit={create}>
          <div><label>Pregunta requerida</label><input value={form.question_text} onChange={e => setForm(prev => ({ ...prev, question_text: e.target.value }))} placeholder="Ej: ¿Qué evidencia tiene disponible?" required /></div>
          <div><label>Orden</label><input type="number" value={form.sort_order} onChange={e => setForm(prev => ({ ...prev, sort_order: e.target.value }))} /></div>
          <label className="checkline"><input type="checkbox" checked={form.required} onChange={e => setForm(prev => ({ ...prev, required: e.target.checked }))} /> Obligatoria</label>
          <button className="primary">Crear</button>
        </form>
      </div>

      <div className="panel wide">
        <h2>Preguntas existentes</h2>
        <table>
          <thead><tr><th>Orden</th><th>Pregunta</th><th>Obligatoria</th><th>Activa</th><th>Acciones</th></tr></thead>
          <tbody>
            {items.map(item => <QuestionRow key={item.id} item={item} onUpdate={update} onRemove={remove} />)}
            {items.length === 0 && <tr><td colSpan="5">No hay preguntas para esta combinación.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function QuestionRow({ item, onUpdate, onRemove }) {
  const [draft, setDraft] = useState(item)
  useEffect(() => setDraft(item), [item])
  return (
    <tr>
      <td><input type="number" value={draft.sort_order} onChange={e => setDraft(prev => ({ ...prev, sort_order: e.target.value }))} /></td>
      <td><input value={draft.question_text} onChange={e => setDraft(prev => ({ ...prev, question_text: e.target.value }))} /></td>
      <td><input type="checkbox" checked={draft.required} onChange={e => setDraft(prev => ({ ...prev, required: e.target.checked }))} /></td>
      <td><input type="checkbox" checked={draft.is_active} onChange={e => setDraft(prev => ({ ...prev, is_active: e.target.checked }))} /></td>
      <td className="action-cell"><button className="small" onClick={() => onUpdate(item, { question_text: draft.question_text, sort_order: Number(draft.sort_order || 0), required: draft.required, is_active: draft.is_active })}>Guardar</button><button className="small danger-button" onClick={() => onRemove(item)}>Eliminar</button></td>
    </tr>
  )
}
