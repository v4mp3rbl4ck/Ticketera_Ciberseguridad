import { useEffect, useMemo, useState } from 'react'
import { formatDateTime } from '../utils/time'
import { apiFetch } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import Badge, { statusTone } from '../components/Badge'

function fmt(value) {
  return formatDateTime(value)
}

const statusGroups = {
  pending: ['Nuevo', 'Asignado'],
  review: ['En Progreso', 'En Espera'],
  completed: ['Resuelto', 'Cerrado'],
}

export default function ProfilePage({ onOpenTicket }) {
  const { user, logout, reload, setTheme } = useAuth()
  const [fullName, setFullName] = useState(user.full_name)
  const [themePreference, setThemePreference] = useState(user.theme_preference || 'light')
  const [password, setPassword] = useState({ current_password: '', new_password: '' })
  const [tickets, setTickets] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  async function loadOperationalProfile() {
    try {
      const [ticketData, metricData] = await Promise.all([
        apiFetch('/tickets'),
        apiFetch('/metrics/dashboard'),
      ])
      setTickets(ticketData)
      setMetrics(metricData)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => { loadOperationalProfile() }, [])

  function handleThemeChange(value) {
    setThemePreference(value)
    setTheme(value)
  }

  async function updateProfile(e) {
    e.preventDefault()
    setError(''); setOk('')
    try {
      await apiFetch('/auth/profile', { method: 'PATCH', body: JSON.stringify({ full_name: fullName, theme_preference: themePreference }) })
      await reload()
      setOk('Perfil actualizado correctamente')
    } catch (err) { setError(err.message) }
  }

  async function changePassword(e) {
    e.preventDefault()
    setError(''); setOk('')
    try {
      await apiFetch('/auth/change-password', { method: 'POST', body: JSON.stringify(password) })
      setPassword({ current_password: '', new_password: '' })
      setOk('Contraseña actualizada correctamente')
    } catch (err) { setError(err.message) }
  }

  const byStatus = useMemo(() => {
    return tickets.reduce((acc, ticket) => {
      acc[ticket.status] = (acc[ticket.status] || 0) + 1
      return acc
    }, {})
  }, [tickets])

  const ticketsByGroup = useMemo(() => {
    return {
      pending: tickets.filter(t => statusGroups.pending.includes(t.status)),
      review: tickets.filter(t => statusGroups.review.includes(t.status)),
      completed: tickets.filter(t => statusGroups.completed.includes(t.status)),
    }
  }, [tickets])

  const operativeTitle = user.role === 'requester' ? 'Tickets solicitados por mí' : 'Tickets asignados y procesos visibles'
  const initials = user.full_name?.split(' ').slice(0, 2).map(part => part[0]).join('').toUpperCase() || 'U'

  return (
    <section className="page profile-page">
      <div className="profile-hero">
        <div className="profile-avatar">{initials}</div>
        <div>
          <span className="eyebrow-line">Perfil operativo</span>
          <h1>{user.full_name}</h1>
          <p>{user.email}</p>
          <div className="badges">
            <Badge tone="info">{user.role}</Badge>
            <Badge tone={user.is_active ? 'success' : 'danger'}>{user.is_active ? 'Cuenta activa' : 'Cuenta inactiva'}</Badge>
            <Badge tone="muted">{user.area || 'Sin área técnica'}</Badge>
          </div>
        </div>
        <button className="button logout-profile" onClick={logout}>Cerrar sesión</button>
      </div>

      {error && <div className="alert error">{error}</div>}
      {ok && <div className="alert success">{ok}</div>}

      <div className="profile-kpi-grid">
        <ProfileKpi title="Total visibles" value={metrics?.my_tickets?.total ?? tickets.length} detail={operativeTitle} />
        <ProfileKpi title="Pendientes" value={metrics?.my_tickets?.pending ?? ticketsByGroup.pending.length} detail="Nuevo / Asignado" />
        <ProfileKpi title="En revisión" value={metrics?.my_tickets?.in_review ?? ticketsByGroup.review.length} detail="En Progreso / En Espera" />
        <ProfileKpi title="Completados" value={metrics?.my_tickets?.completed ?? ticketsByGroup.completed.length} detail="Resuelto / Cerrado" />
      </div>

      <div className="profile-layout">
        <div className="profile-left">
          <div className="panel profile-card">
            <h2>Datos de cuenta</h2>
            <Info label="Nombre" value={user.full_name} />
            <Info label="Correo" value={user.email} />
            <Info label="Rol base" value={user.role} />
            <Info label="Área técnica" value={user.area || 'No asignada'} />
            <Info label="Tema actual" value={themePreference === 'dark' ? 'Oscuro' : 'Claro'} />
          </div>

          <div className="panel profile-card">
            <h2>Preferencias</h2>
            <form className="comment-form" onSubmit={updateProfile}>
              <label>Nombre completo</label>
              <input value={fullName} onChange={e => setFullName(e.target.value)} required />
              <label>Apariencia de la interfaz</label>
              <select value={themePreference} onChange={e => handleThemeChange(e.target.value)}>
                <option value="light">Claro enterprise</option>
                <option value="dark">Oscuro SOC</option>
              </select>
              <button className="primary">Guardar preferencias</button>
            </form>
          </div>

          <div className="panel profile-card">
            <h2>Seguridad de cuenta</h2>
            <form className="comment-form" onSubmit={changePassword}>
              <label>Contraseña actual</label>
              <input type="password" value={password.current_password} onChange={e => setPassword(prev => ({ ...prev, current_password: e.target.value }))} required />
              <label>Nueva contraseña</label>
              <input type="password" value={password.new_password} onChange={e => setPassword(prev => ({ ...prev, new_password: e.target.value }))} minLength="10" required />
              <small className="muted-text">Mínimo 10 caracteres, con mayúscula, minúscula, número y carácter especial.</small>
              <button className="primary">Actualizar contraseña</button>
            </form>
          </div>
        </div>

        <div className="profile-main panel wide">
          <div className="section-heading">
            <div>
              <h2>{operativeTitle}</h2>
              <p className="panel-help">Seguimiento de procesos asociados a tu cuenta y estados actuales.</p>
            </div>
          </div>

          <div className="status-chips profile-status-chips">
            {Object.entries(byStatus).map(([status, count]) => <span key={status}><strong>{status}</strong>{count}</span>)}
            {Object.keys(byStatus).length === 0 && <span><strong>Sin tickets</strong>0</span>}
          </div>

          <div className="profile-process-columns">
            <ProcessColumn title="Pendientes" tickets={ticketsByGroup.pending} onOpenTicket={onOpenTicket} />
            <ProcessColumn title="En revisión" tickets={ticketsByGroup.review} onOpenTicket={onOpenTicket} />
            <ProcessColumn title="Completados" tickets={ticketsByGroup.completed} onOpenTicket={onOpenTicket} />
          </div>

          <h3>Últimos tickets</h3>
          <table>
            <thead><tr><th>ID</th><th>Categoría</th><th>Solicitante</th><th>Asignado</th><th>Estado</th><th>Creado</th><th>Última actualización</th></tr></thead>
            <tbody>{tickets.slice(0, 15).map(ticket => (
              <tr key={ticket.id} onClick={() => onOpenTicket?.(ticket.id)}>
                <td>{ticket.ticket_number}</td>
                <td>{ticket.category}</td>
                <td>{ticket.created_by_name || ticket.created_by_email}</td>
                <td>{ticket.assigned_to_name || 'Sin asignar'}</td>
                <td><Badge tone={statusTone(ticket.status)}>{ticket.status}</Badge></td>
                <td>{fmt(ticket.created_at)}</td>
                <td>{fmt(ticket.updated_at)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

function ProfileKpi({ title, value, detail }) {
  return <div className="profile-kpi"><span>{title}</span><strong>{value}</strong><small>{detail}</small></div>
}

function ProcessColumn({ title, tickets, onOpenTicket }) {
  return (
    <div className="process-column">
      <div className="process-column-header"><h3>{title}</h3><span>{tickets.length}</span></div>
      <div className="process-list">
        {tickets.slice(0, 6).map(ticket => (
          <button key={ticket.id} type="button" className="process-card" onClick={() => onOpenTicket?.(ticket.id)}>
            <strong>{ticket.ticket_number}</strong>
            <span>{ticket.category}</span>
            <Badge tone={statusTone(ticket.status)}>{ticket.status}</Badge>
          </button>
        ))}
        {tickets.length === 0 && <p className="empty-state">Sin tickets en este estado.</p>}
      </div>
    </div>
  )
}

function Info({ label, value }) {
  return <div className="info"><span>{label}</span><strong>{value}</strong></div>
}
