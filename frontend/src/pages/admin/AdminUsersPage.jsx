import { useEffect, useState } from 'react'
import { apiFetch } from '../../api/client'
import { roleLabel, technicalAreas } from './adminConstants'
import { useAuth } from '../../contexts/AuthContext'

export default function AdminUsersPage() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [roles, setRoles] = useState([])
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [userForm, setUserForm] = useState({ full_name: '', email: '', password: '', role: 'requester', area: '' })

  async function load() {
    setError('')
    const [userData, roleData] = await Promise.all([
      apiFetch('/admin/users'),
      apiFetch('/admin/roles'),
    ])
    setUsers(userData)
    setRoles(roleData.filter(role => role.is_active))
  }

  useEffect(() => { load().catch(err => setError(err.message)) }, [])

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

  async function updateUser(id, patch) {
    setError(''); setOk('')
    try {
      await apiFetch(`/admin/users/${id}`, { method: 'PATCH', body: JSON.stringify(patch) })
      setOk(patch.new_password ? 'Usuario y contraseña actualizados correctamente' : 'Usuario actualizado')
      await load()
    } catch (err) { setError(err.message) }
  }

  async function resetPassword(id, newPassword) {
    setError(''); setOk('')
    try {
      await apiFetch(`/admin/users/${id}/reset-password`, { method: 'POST', body: JSON.stringify({ new_password: newPassword }) })
      setOk('Contraseña temporal actualizada correctamente')
      await load()
    } catch (err) { setError(err.message) }
  }

  async function deleteUser(id, email) {
    setError(''); setOk('')
    const confirmed = window.confirm(`¿Eliminar el usuario ${email}? Esta acción desactivará la cuenta y la quitará del listado.`)
    if (!confirmed) return
    try {
      await apiFetch(`/admin/users/${id}`, { method: 'DELETE' })
      setOk('Usuario eliminado correctamente')
      await load()
    } catch (err) { setError(err.message) }
  }

  return (
    <section className="page admin-module-page">
      <div className="page-header">
        <div>
          <h1>Usuarios</h1>
          <p>Alta, mantenimiento de cuentas, rol por módulo, área técnica, restablecimiento de contraseña y eliminación lógica.</p>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert success">{ok}</div>}

      <div className="dashboard-grid">
        <div className="panel wide admin-card">
          <h2>Crear usuario</h2>
          <form className="admin-form" onSubmit={createUser}>
            <input placeholder="Nombre completo" value={userForm.full_name} onChange={e => setUserForm({ ...userForm, full_name: e.target.value })} required />
            <input placeholder="Correo corporativo" value={userForm.email} onChange={e => setUserForm({ ...userForm, email: e.target.value })} required />
            <input placeholder="Contraseña temporal" type="password" value={userForm.password} onChange={e => setUserForm({ ...userForm, password: e.target.value })} minLength="10" required />
            <select value={userForm.role} onChange={e => setUserForm({ ...userForm, role: e.target.value })}>{roles.map(r => <option key={r.key} value={r.key}>{r.name || roleLabel(r.key)}</option>)}</select>
            <select value={userForm.area} onChange={e => setUserForm({ ...userForm, area: e.target.value })}>
              <option value="">Área global / solicitante</option>
              {technicalAreas.map(a => <option key={a}>{a}</option>)}
            </select>
            <button className="primary">Crear usuario</button>
          </form>
        </div>

        <div className="panel wide">
          <h2>Usuarios existentes</h2>
          <p className="panel-help">La contraseña se puede restablecer desde una acción separada para evitar confusión con el botón de guardar datos del usuario.</p>
          <table>
            <thead><tr><th>Nombre</th><th>Correo</th><th>Rol</th><th>Área técnica</th><th>Activo</th><th>Contraseña temporal</th><th>Acciones</th></tr></thead>
            <tbody>{users.map(u => <UserRow key={u.id} user={u} currentUser={currentUser} roles={roles} onSave={updateUser} onResetPassword={resetPassword} onDelete={deleteUser} />)}</tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

function UserRow({ user, currentUser, roles, onSave, onResetPassword, onDelete }) {
  const [draft, setDraft] = useState(user)
  const [newPassword, setNewPassword] = useState('')
  useEffect(() => { setDraft(user); setNewPassword('') }, [user])

  function saveProfile() {
    const payload = {
      full_name: draft.full_name,
      role: draft.role,
      area: draft.area,
      is_active: draft.is_active,
    }
    if (newPassword.length >= 10) payload.new_password = newPassword
    onSave(user.id, payload)
  }

  function resetOnlyPassword() {
    onResetPassword(user.id, newPassword)
  }

  const isSelf = currentUser?.id === user.id
  const canReset = newPassword.length >= 10

  return (
    <tr>
      <td><input value={draft.full_name} onChange={e => setDraft({ ...draft, full_name: e.target.value })} /></td>
      <td>{user.email}</td>
      <td><select value={draft.role} onChange={e => setDraft({ ...draft, role: e.target.value })}>{roles.map(r => <option key={r.key} value={r.key}>{r.name || roleLabel(r.key)}</option>)}</select></td>
      <td><select value={draft.area || ''} onChange={e => setDraft({ ...draft, area: e.target.value || null })}><option value="">Global / Solicitante</option>{technicalAreas.map(a => <option key={a}>{a}</option>)}</select></td>
      <td><select value={draft.is_active ? 'true' : 'false'} onChange={e => setDraft({ ...draft, is_active: e.target.value === 'true' })} disabled={isSelf}><option value="true">Sí</option><option value="false">No</option></select></td>
      <td>
        <input type="password" placeholder="Nueva contraseña" value={newPassword} onChange={e => setNewPassword(e.target.value)} minLength="10" />
        <small className="muted-text">Mínimo 10 caracteres, con mayúscula, minúscula, número y carácter especial.</small>
      </td>
      <td className="action-cell stacked-actions">
        <button className="ghost small" onClick={saveProfile}>Guardar cambios</button>
        <button className="ghost small" disabled={!canReset} onClick={resetOnlyPassword}>Restablecer clave</button>
        <button className="danger small" disabled={isSelf} onClick={() => onDelete(user.id, user.email)}>Eliminar</button>
      </td>
    </tr>
  )
}
