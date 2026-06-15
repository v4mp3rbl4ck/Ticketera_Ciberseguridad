import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../../api/client'

const emptyPerm = { can_view: false, can_create: false, can_edit: false, can_delete: false }

function normalizePermissions(role, modules) {
  const map = Object.fromEntries(modules.map(module => [module.key, { module_key: module.key, ...emptyPerm }]))
  ;(role?.permissions || []).forEach(permission => {
    map[permission.module_key] = {
      module_key: permission.module_key,
      can_view: !!permission.can_view,
      can_create: !!permission.can_create,
      can_edit: !!permission.can_edit,
      can_delete: !!permission.can_delete,
    }
  })
  return map
}

export default function AdminRolesPage() {
  const [roles, setRoles] = useState([])
  const [modules, setModules] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [draft, setDraft] = useState(null)
  const [form, setForm] = useState({ key: '', name: '', description: '' })
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  async function load() {
    setError('')
    const [moduleData, roleData] = await Promise.all([
      apiFetch('/admin/role-modules'),
      apiFetch('/admin/roles'),
    ])
    setModules(moduleData)
    setRoles(roleData)
    if (!selectedId && roleData.length) setSelectedId(roleData[0].id)
  }

  useEffect(() => { load().catch(err => setError(err.message)) }, [])

  const selectedRole = useMemo(() => roles.find(role => role.id === Number(selectedId)), [roles, selectedId])

  useEffect(() => {
    if (!selectedRole || modules.length === 0) return
    setDraft({
      name: selectedRole.name,
      description: selectedRole.description || '',
      is_active: selectedRole.is_active,
      permissions: normalizePermissions(selectedRole, modules),
    })
  }, [selectedRole, modules])

  async function createRole(e) {
    e.preventDefault(); setError(''); setOk('')
    try {
      const permissions = modules.map(module => ({ module_key: module.key, ...emptyPerm }))
      const role = await apiFetch('/admin/roles', { method: 'POST', body: JSON.stringify({ ...form, permissions }) })
      setOk('Rol creado correctamente')
      setForm({ key: '', name: '', description: '' })
      await load()
      setSelectedId(role.id)
    } catch (err) { setError(err.message) }
  }

  function updatePermission(moduleKey, field, value) {
    setDraft(prev => ({
      ...prev,
      permissions: {
        ...prev.permissions,
        [moduleKey]: { ...prev.permissions[moduleKey], [field]: value, can_view: field !== 'can_view' && value ? true : prev.permissions[moduleKey].can_view },
      },
    }))
  }

  async function saveRole() {
    setError(''); setOk('')
    try {
      const permissions = Object.values(draft.permissions)
      await apiFetch(`/admin/roles/${selectedRole.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ name: draft.name, description: draft.description, is_active: draft.is_active, permissions }),
      })
      setOk('Rol actualizado correctamente')
      await load()
    } catch (err) { setError(err.message) }
  }

  const groupedModules = modules.reduce((acc, module) => {
    acc[module.group] = acc[module.group] || []
    acc[module.group].push(module)
    return acc
  }, {})

  return (
    <section className="page admin-module-page">
      <div className="page-header">
        <div>
          <h1>Roles por Módulo</h1>
          <p>Crea roles personalizados y define permisos granulares por módulo del sistema.</p>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert success">{ok}</div>}

      <div className="dashboard-grid">
        <div className="panel wide admin-card">
          <h2>Crear rol específico</h2>
          <form className="admin-form roles-create-form" onSubmit={createRole}>
            <input placeholder="Clave del rol, ej: coordinador_red" value={form.key} onChange={e => setForm({ ...form, key: e.target.value })} required />
            <input placeholder="Nombre visible" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
            <input placeholder="Descripción" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
            <button className="primary">Crear rol</button>
          </form>
        </div>

        <div className="panel role-list-panel">
          <h2>Roles existentes</h2>
          <div className="role-list">
            {roles.map(role => (
              <button key={role.id} className={Number(selectedId) === role.id ? 'role-pill active' : 'role-pill'} onClick={() => setSelectedId(role.id)}>
                <strong>{role.name}</strong>
                <span>{role.key}{role.is_system ? ' · sistema' : ''}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="panel role-editor-panel">
          <h2>Permisos del rol</h2>
          {!selectedRole || !draft ? <p>Selecciona un rol.</p> : (
            <div className="role-editor">
              <div className="field-grid three">
                <div><label>Nombre</label><input value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} /></div>
                <div><label>Clave</label><input value={selectedRole.key} disabled /></div>
                <div><label>Activo</label><select value={draft.is_active ? 'true' : 'false'} disabled={selectedRole.is_system} onChange={e => setDraft({ ...draft, is_active: e.target.value === 'true' })}><option value="true">Sí</option><option value="false">No</option></select></div>
                <div className="span-2"><label>Descripción</label><input value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value })} /></div>
              </div>

              {Object.entries(groupedModules).map(([group, groupModules]) => (
                <div className="permission-group" key={group}>
                  <h3>{group}</h3>
                  <table>
                    <thead><tr><th>Módulo</th><th>Ver</th><th>Crear</th><th>Editar</th><th>Eliminar</th></tr></thead>
                    <tbody>{groupModules.map(module => {
                      const perm = draft.permissions[module.key] || { module_key: module.key, ...emptyPerm }
                      return (
                        <tr key={module.key}>
                          <td><strong>{module.label}</strong><small>{module.description}</small></td>
                          {['can_view', 'can_create', 'can_edit', 'can_delete'].map(field => (
                            <td key={field}><input className="checkbox-input" type="checkbox" checked={!!perm[field]} onChange={e => updatePermission(module.key, field, e.target.checked)} /></td>
                          ))}
                        </tr>
                      )
                    })}</tbody>
                  </table>
                </div>
              ))}
              <button className="primary" onClick={saveRole}>Guardar permisos</button>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
