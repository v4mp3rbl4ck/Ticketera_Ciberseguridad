import { useEffect, useRef, useState } from 'react'
import { formatDateTime } from '../utils/time'
import { Bell, CheckCheck, Clock, ExternalLink } from 'lucide-react'
import { apiFetch } from '../api/client'

function formatDate(value) {
  return formatDateTime(value)
}


function notificationTone(kind) {
  if (kind === 'sla_breached') return 'danger'
  if (kind === 'sla_warning') return 'warning'
  if (kind === 'ticket_resolved' || kind === 'ticket_closed') return 'success'
  if (kind === 'ticket_assigned') return 'info'
  return 'neutral'
}

export default function NotificationBell({ onOpenTicket }) {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState([])
  const [unread, setUnread] = useState(0)
  const [loading, setLoading] = useState(false)
  const panelRef = useRef(null)

  async function loadNotifications() {
    try {
      setLoading(true)
      const data = await apiFetch('/notifications?limit=12')
      setItems(data.items || [])
      setUnread(data.unread_count || 0)
    } catch (_) {
      // La campana no debe romper la navegación si el endpoint falla.
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadNotifications()
    const timer = window.setInterval(loadNotifications, 45000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    function handleClick(event) {
      if (panelRef.current && !panelRef.current.contains(event.target)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  async function markRead(item) {
    if (!item.read) {
      try {
        await apiFetch(`/notifications/${item.id}/read`, { method: 'PATCH' })
        setItems(prev => prev.map(row => row.id === item.id ? { ...row, read: true } : row))
        setUnread(prev => Math.max(0, prev - 1))
      } catch (_) {}
    }
  }

  async function handleItemClick(item) {
    await markRead(item)
    if (item.entity_type === 'ticket' && item.entity_id && onOpenTicket) {
      onOpenTicket(item.entity_id)
      setOpen(false)
    }
  }

  async function markAllRead() {
    try {
      await apiFetch('/notifications/read-all', { method: 'PATCH' })
      setItems(prev => prev.map(item => ({ ...item, read: true })))
      setUnread(0)
    } catch (_) {}
  }

  return (
    <div className="notification-wrapper" ref={panelRef}>
      <button className="notification-trigger" type="button" onClick={() => setOpen(prev => !prev)} aria-label="Notificaciones">
        <Bell size={18} />
        {unread > 0 && <span className="notification-count">{unread > 9 ? '9+' : unread}</span>}
      </button>

      {open && (
        <div className="notification-panel">
          <div className="notification-header">
            <div>
              <strong>Notificaciones</strong>
              <span>{unread} sin leer</span>
            </div>
            <button className="mini-link" onClick={markAllRead} disabled={unread === 0}>
              <CheckCheck size={14} /> Marcar leídas
            </button>
          </div>

          <div className="notification-list">
            {loading && items.length === 0 && <div className="notification-empty">Cargando notificaciones...</div>}
            {!loading && items.length === 0 && <div className="notification-empty">No hay notificaciones por ahora.</div>}
            {items.map(item => (
              <button
                key={item.id}
                className={`notification-item ${item.read ? 'read' : 'unread'} ${notificationTone(item.kind)}`}
                onClick={() => handleItemClick(item)}
                type="button"
              >
                <span className="notification-dot" />
                <span className="notification-content">
                  <strong>{item.title}</strong>
                  <small>{item.body}</small>
                  <em><Clock size={12} /> {formatDate(item.created_at)}</em>
                </span>
                {item.entity_type === 'ticket' && <ExternalLink size={14} className="notification-open-icon" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
