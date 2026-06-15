import { useEffect, useMemo, useState } from 'react'
import { API_URL, apiFetch } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import Badge, { severityTone, statusTone } from '../components/Badge'
import { formatDateTime, formatDurationHuman, getTicketTiming, toDate } from '../utils/time'

const statuses = ['Nuevo', 'Asignado', 'En Progreso', 'En Espera', 'Resuelto', 'Cerrado']
const BASE_URL = API_URL.replace('/api/v1', '')

function fmt(value) {
  return formatDateTime(value)
}

function fileSize(bytes = 0) {
  if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${Math.max(1, Math.round(bytes / 1024))} KB`
}

function fileIcon(file) {
  const type = file.content_type || ''
  if (type.startsWith('image/')) return '🖼️'
  if (type.includes('pdf')) return '📄'
  if (type.includes('zip')) return '🗜️'
  if (type.includes('sheet') || file.file_name?.match(/\.xlsx?$|\.csv$/i)) return '📊'
  return '📎'
}

function statusIndex(status) {
  const index = statuses.indexOf(status)
  return index >= 0 ? index : 0
}

function slaState(ticket) {
  if (ticket.sla_state_label) return { label: ticket.sla_state_label, tone: ticket.sla_state_tone || 'info' }
  if (!ticket.sla_due_at) return { label: 'Sin SLA', tone: 'muted' }
  if (ticket.is_sla_breached) return { label: 'SLA vencido', tone: 'critical' }
  if (['Resuelto', 'Cerrado'].includes(ticket.status)) return { label: 'SLA finalizado', tone: 'success' }
  return { label: 'SLA activo', tone: 'info' }
}

function formatDuration(seconds) {
  return formatDurationHuman(seconds, { compact: true })
}

function pct(value) {
  if (value === null || value === undefined) return 0
  return Math.max(0, Math.min(100, Number(value)))
}

export default function TicketDetailPage({ ticketId }) {
  const { user } = useAuth()
  const [ticket, setTicket] = useState(null)
  const [users, setUsers] = useState([])
  const [comment, setComment] = useState('')
  const [commentType, setCommentType] = useState('public')
  const [statusDraft, setStatusDraft] = useState('')
  const [statusReason, setStatusReason] = useState('')
  const [files, setFiles] = useState([])
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [now, setNow] = useState(() => new Date())

  const canManage = !!user.permissions?.tickets?.edit || ['analyst', 'admin', 'supervisor'].includes(user.role)

  async function load() {
    if (!ticketId) return
    try {
      const nextTicket = await apiFetch(`/tickets/${ticketId}`)
      setTicket(nextTicket)
      setStatusDraft(nextTicket.status)
      if (canManage) setUsers(await apiFetch('/tickets/assignees'))
    } catch (err) { setError(err.message) }
  }

  useEffect(() => { load() }, [ticketId])
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 60000)
    return () => window.clearInterval(timer)
  }, [])

  async function updateStatus(e) {
    e.preventDefault()
    if (!ticket || statusDraft === ticket.status) return
    if (['En Espera', 'Resuelto', 'Cerrado'].includes(statusDraft) && !statusReason.trim()) {
      setError('Indica una nota o motivo para este cambio de estado.')
      return
    }
    setError('')
    try {
      await apiFetch(`/tickets/${ticket.id}/status`, { method: 'PATCH', body: JSON.stringify({ status: statusDraft, reason: statusReason }) })
      setStatusReason('')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function assign(assigned_to_id) {
    if (!assigned_to_id) return
    try {
      await apiFetch(`/tickets/${ticket.id}/assign`, { method: 'PATCH', body: JSON.stringify({ assigned_to_id: Number(assigned_to_id) }) })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  function addFiles(nextFiles) {
    const incoming = Array.from(nextFiles || [])
    if (!incoming.length) return
    setFiles(prev => [...prev, ...incoming])
  }

  function removeSelectedFile(index) {
    setFiles(prev => prev.filter((_, itemIndex) => itemIndex !== index))
  }

  function handlePasteEvidence(e) {
    const items = Array.from(e.clipboardData?.items || [])
    const imageFiles = []
    for (const item of items) {
      if (item.kind === 'file' && item.type.startsWith('image/')) {
        const blob = item.getAsFile()
        if (blob) {
          const extension = blob.type.includes('jpeg') ? 'jpg' : (blob.type.split('/')[1] || 'png')
          imageFiles.push(new File([blob], `captura-pegada-${Date.now()}.${extension}`, { type: blob.type }))
        }
      }
    }
    if (imageFiles.length) {
      e.preventDefault()
      addFiles(imageFiles)
    }
  }

  async function uploadFilesForComment(commentId) {
    if (!files.length) return null
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('comment_id', String(commentId))
    return apiFetch(`/tickets/${ticket.id}/attachments`, { method: 'POST', body: formData })
  }

  async function sendComment(e) {
    e.preventDefault()
    setUploading(true)
    setError('')
    try {
      const updated = await apiFetch(`/tickets/${ticket.id}/comments`, { method: 'POST', body: JSON.stringify({ comment_type: commentType, body: comment }) })
      const newComment = [...(updated.comments || [])].sort((a, b) => b.id - a.id)[0]
      if (newComment?.id && files.length) {
        await uploadFilesForComment(newComment.id)
      }
      setComment('')
      setFiles([])
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const timeline = useMemo(() => {
    if (!ticket) return []
    const rows = [
      { at: ticket.created_at, title: 'Ticket creado', body: `Creado por ${ticket.created_by_name || ticket.created_by_email || 'usuario'}` },
      ticket.assigned_at && { at: ticket.assigned_at, title: 'Ticket asignado', body: ticket.assigned_to_name || 'Asignado' },
      ticket.first_response_at && { at: ticket.first_response_at, title: 'Primera respuesta', body: 'Inicio de atención operacional' },
      ticket.resolved_at && { at: ticket.resolved_at, title: 'Ticket resuelto', body: 'Resolución registrada' },
      ticket.closed_at && { at: ticket.closed_at, title: 'Ticket cerrado', body: 'Cierre final del caso' },
      ...ticket.comments.map(c => ({
        at: c.created_at,
        title: c.comment_type === 'internal' ? 'Nota interna' : c.comment_type === 'system' ? 'Evento de sistema' : 'Comentario público',
        body: c.attachments?.length ? `${c.body} · ${c.attachments.length} adjunto(s)` : c.body,
        author: c.author_name,
      })),
      ...ticket.attachments.map(a => ({ at: a.created_at, title: 'Adjunto general agregado', body: a.file_name, author: a.uploaded_by_name })),
    ].filter(Boolean)
    return rows.sort((a, b) => (toDate(a.at)?.getTime() || 0) - (toDate(b.at)?.getTime() || 0))
  }, [ticket])

  if (error && !ticket) return <section className="page"><div className="alert error">{error}</div></section>
  if (!ticket) return <section className="page"><p>Cargando ticket...</p></section>

  const visibleComments = ticket.comments.filter(c => canManage || c.comment_type === 'public' || c.comment_type === 'system')
  const currentSla = slaState(ticket)
  const currentStatusIndex = statusIndex(ticket.status)
  const timing = getTicketTiming(ticket, now)

  return (
    <section className="page ticket-detail-page">
      <div className="ticket-detail-header enterprise-detail-header">
        <div>
          <span className="eyebrow-line">Seguimiento de incidente / requerimiento</span>
          <h1>{ticket.ticket_number} · {ticket.subject}</h1>
          <p>{ticket.category} · Solicitado por {ticket.created_by_name || ticket.created_by_email}</p>
        </div>
        <div className="badges">
          <Badge tone={severityTone(ticket.severity)}>{ticket.severity}</Badge>
          <Badge tone={statusTone(ticket.status)}>{ticket.status}</Badge>
          <Badge tone={currentSla.tone}>{currentSla.label}</Badge>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}

      <div className="ticket-progress panel wide">
        {statuses.map((status, index) => (
          <div className={`progress-step ${index <= currentStatusIndex ? 'done' : ''} ${status === ticket.status ? 'current' : ''}`} key={status}>
            <span>{index + 1}</span>
            <strong>{status}</strong>
          </div>
        ))}
      </div>

      <div className="panel wide sla-control-card">
        <div className="section-title-row">
          <div>
            <h2>SLA avanzado</h2>
            <p className="panel-help">Control de primera respuesta, resolución objetivo, pausas y consumo de SLA.</p>
          </div>
          <Badge tone={currentSla.tone}>{currentSla.label}</Badge>
        </div>
        <div className="sla-progress-row">
          <div className="sla-progress-info">
            <strong>{Math.round(pct(ticket.sla_elapsed_percent))}% consumido</strong>
            <span>{ticket.sla_is_paused ? 'SLA pausado por estado En Espera' : `Tiempo restante: ${formatDuration(ticket.sla_remaining_seconds)}`}</span>
          </div>
          <div className={`sla-progress-track ${ticket.sla_state || ''}`}><div style={{ width: `${pct(ticket.sla_elapsed_percent)}%` }} /></div>
        </div>
        <div className="ticket-time-grid">
          <div className="time-metric-card primary">
            <span>Vida del ticket</span>
            <strong>{timing.lifecycleLabel}</strong>
            <small>{timing.measurementLabel}</small>
          </div>
          <div className="time-metric-card">
            <span>SLA transcurrido</span>
            <strong>{timing.slaElapsedLabel}</strong>
            <small>Tiempo de atención menos pausas registradas</small>
          </div>
          <div className="time-metric-card">
            <span>Fin de medición</span>
            <strong>{timing.finalized ? fmt(timing.endAt) : 'En curso'}</strong>
            <small>{timing.finalized ? 'Medición cerrada' : 'Se actualiza automáticamente cada minuto'}</small>
          </div>
        </div>
        <div className="sla-detail-grid">
          <Info label="Política aplicada" value={ticket.sla_policy_scope || 'N/A'} />
          <Info label="Horario laboral" value={ticket.sla_business_hours_only === null || ticket.sla_business_hours_only === undefined ? 'N/A' : ticket.sla_business_hours_only ? 'Sí' : 'No'} />
          <Info label="Pausa permitida" value={ticket.sla_pause_allowed === null || ticket.sla_pause_allowed === undefined ? 'N/A' : ticket.sla_pause_allowed ? 'Sí' : 'No'} />
          <Info label="1ra respuesta límite" value={fmt(ticket.sla_first_response_due_at)} />
          <Info label="1ra respuesta" value={ticket.sla_first_response_breached ? 'Vencida' : 'Dentro de control'} />
          <Info label="Tiempo pausado" value={formatDuration(ticket.sla_paused_seconds)} />
        </div>
      </div>

      <div className="detail-grid enterprise-detail-grid">
        <div className="panel wide detail-main-card">
          <div className="section-title-row">
            <div>
              <h2>Detalle del ticket</h2>
              <p className="panel-help">Resumen ejecutivo, trazabilidad y datos clave de atención.</p>
            </div>
            <Badge tone={statusTone(ticket.status)}>{ticket.status}</Badge>
          </div>
          <div className="summary-grid">
            <Info label="ID" value={`${ticket.ticket_number} / #${ticket.id}`} />
            <Info label="Categoría" value={ticket.category} />
            <Info label="Área técnica" value={ticket.area_destino} />
            <Info label="Área solicitante" value={ticket.project_area} />
            <Info label="Solicitante" value={ticket.created_by_name || ticket.created_by_email} />
            <Info label="Asignado" value={ticket.assigned_to_name || 'Sin asignar'} />
            <Info label="Creación" value={fmt(ticket.created_at)} />
            <Info label="Actualización" value={fmt(ticket.updated_at)} />
            <Info label="Resolución" value={fmt(ticket.resolved_at)} />
            <Info label="Vida del ticket" value={timing.lifecycleLabel} />
            <Info label="SLA transcurrido" value={timing.slaElapsedLabel} />
            <Info label="SLA límite" value={ticket.sla_due_at ? fmt(ticket.sla_due_at) : 'N/A'} />
          </div>
          <div className="ticket-description-blocks">
            <div><h3>Descripción</h3><p>{ticket.description}</p></div>
            <div><h3>Impacto operacional</h3><p>{ticket.impact}</p></div>
            <div><h3>Evidencia declarada</h3><p>{ticket.evidence_summary || 'Sin evidencia registrada'}</p></div>
          </div>
        </div>

        <div className="panel side-card">
          <h2>Datos técnicos</h2>
          <Info label="Usuario afectado / alcance" value={ticket.scope_users_affected} />
          <Info label="Activo involucrado" value={ticket.involved_asset} />
          <Info label="Primer evento" value={fmt(ticket.first_event_at)} />
          <Info label="IP" value={ticket.ip_address || 'N/A'} />
          <Info label="Hostname" value={ticket.hostname || 'N/A'} />
        </div>
      </div>

      {canManage && (
        <div className="panel actions-panel enterprise-actions-panel">
          <div>
            <h2>Gestión operacional</h2>
            <p className="panel-help">Los cambios de estado quedan registrados en auditoría y línea de tiempo.</p>
          </div>
          <form onSubmit={updateStatus} className="status-change-form">
            <div>
              <label>Estado</label>
              <select value={statusDraft} onChange={e => setStatusDraft(e.target.value)}>{statuses.map(s => <option key={s}>{s}</option>)}</select>
            </div>
            <div>
              <label>Nota / motivo</label>
              <input value={statusReason} onChange={e => setStatusReason(e.target.value)} placeholder="Requerido para espera, resolución o cierre" />
            </div>
            <button className="primary">Actualizar estado</button>
          </form>
          <div>
            <label>Asignar a</label>
            <select value={ticket.assigned_to_id || ''} onChange={e => assign(e.target.value)}>
              <option value="">Sin asignar</option>
              {users.map(u => <option value={u.id} key={u.id}>{u.full_name} · {u.area || 'Global'}</option>)}
            </select>
          </div>
        </div>
      )}

      <div className="panel wide">
        <h2>Línea de tiempo</h2>
        <div className="timeline enhanced-timeline">
          {timeline.map((item, index) => <div className="timeline-item" key={`${item.title}-${index}`}><span>{fmt(item.at)}</span><strong>{item.title}</strong>{item.author && <em>{item.author}</em>}<p>{item.body}</p></div>)}
        </div>
      </div>

      <div className="panel wide">
        <h2>Checklist / Preguntas requeridas</h2>
        {ticket.dynamic_answers.map(a => <div className="qa" key={a.id}><strong>{a.question_text}</strong><p>{a.answer || 'Sin respuesta'}</p></div>)}
        {ticket.dynamic_answers.length === 0 && <p className="panel-help">Este ticket no tiene preguntas requeridas registradas.</p>}
      </div>

      <div className="panel wide">
        <h2>Comentarios y evidencias</h2>
        <p className="panel-help">Cada respuesta puede incluir sus propios adjuntos, capturas o documentos para mantener el seguimiento del incidente ordenado.</p>

        <div className="comment-thread">
          {visibleComments.map(c => (
            <div className={`comment ${c.comment_type}`} key={c.id}>
              <div className="comment-meta">
                <strong>{c.comment_type === 'internal' ? 'Nota interna' : c.comment_type === 'system' ? 'Sistema' : 'Respuesta pública'} · {c.author_name || c.author_id}</strong>
                <small>{fmt(c.created_at)}</small>
              </div>
              <p>{c.body}</p>
              {c.attachments?.length > 0 && (
                <div className="comment-attachments">
                  {c.attachments.map(file => <AttachmentCard file={file} key={file.id} />)}
                </div>
              )}
            </div>
          ))}
        </div>

        <form onSubmit={sendComment} className="comment-form evidence-comment-form" onPaste={handlePasteEvidence}>
          {canManage && <select value={commentType} onChange={e => setCommentType(e.target.value)}><option value="public">Respuesta pública</option><option value="internal">Nota interna</option></select>}
          <textarea value={comment} onChange={e => setComment(e.target.value)} placeholder="Escribir comentario, avance, resolución o nota técnica..." required />
          <div className="evidence-composer">
            <input type="file" multiple accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.log,.zip" onChange={e => addFiles(e.target.files)} />
            <div className="paste-zone" tabIndex="0" onPaste={handlePasteEvidence}>Pega una captura con Ctrl+V para adjuntarla a este comentario.</div>
          </div>
          {files.length > 0 && (
            <div className="selected-files">
              {files.map((file, index) => (
                <span key={`${file.name}-${index}`}>{file.name}<button type="button" onClick={() => removeSelectedFile(index)}>×</button></span>
              ))}
            </div>
          )}
          <button className="primary" disabled={uploading}>{uploading ? 'Guardando...' : 'Agregar comentario'}</button>
        </form>
      </div>

      {ticket.attachments.length > 0 && (
        <div className="panel wide">
          <h2>Adjuntos generales heredados</h2>
          <p className="panel-help">Archivos cargados sin comentario asociado antes de la organización por hilo.</p>
          <div className="attachment-grid">
            {ticket.attachments.map(file => <AttachmentCard file={file} key={file.id} />)}
          </div>
        </div>
      )}
    </section>
  )
}

function AttachmentCard({ file }) {
  return (
    <a className="attachment-card" href={`${BASE_URL}${file.download_url}`} target="_blank" rel="noreferrer">
      <span className="attachment-icon">{fileIcon(file)}</span>
      <strong>{file.file_name}</strong>
      <small>{fileSize(file.size_bytes)} · {file.uploaded_by_name || 'Usuario'} · {fmt(file.created_at)}</small>
    </a>
  )
}

function Info({ label, value }) {
  return <div className="info"><span>{label}</span><strong>{value}</strong></div>
}
