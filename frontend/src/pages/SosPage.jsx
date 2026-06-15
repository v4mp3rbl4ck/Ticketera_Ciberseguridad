import { useState } from 'react'
import { apiFetch } from '../api/client'

export default function SosPage() {
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    call_datetime: '',
    caller_name: '',
    leadership_contacted: '',
    affected_area: '',
    affected_service: '',
    impact_summary: '',
    actions_taken: '',
    policy_activated: '',
    evidence_summary: '',
    tlp: 'TLP:RED',
    status: 'Registrado',
  })

  function update(key, value) {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  async function submit(e) {
    e.preventDefault()
    setError('')
    setMessage('')
    try {
      await apiFetch('/sos', { method: 'POST', body: JSON.stringify(form) })
      setMessage('Evento SOS registrado correctamente.')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="page">
      <h1>Registro SOS posterior</h1>
      <p>Para severidad crítica, el contacto inicial es solo llamada. Este formulario registra el evento a posteriori.</p>
      {error && <div className="alert error">{error}</div>}
      {message && <div className="alert success">{message}</div>}
      <form className="form-grid" onSubmit={submit}>
        <div className="form-section">
          <label>Fecha/hora de llamada</label>
          <input type="datetime-local" value={form.call_datetime} onChange={e => update('call_datetime', e.target.value)} required />
          <label>Persona que llamó</label>
          <input value={form.caller_name} onChange={e => update('caller_name', e.target.value)} required />
          <label>Jefatura contactada</label>
          <input value={form.leadership_contacted} onChange={e => update('leadership_contacted', e.target.value)} required />
          <label>Área afectada</label>
          <input value={form.affected_area} onChange={e => update('affected_area', e.target.value)} required />
          <label>Servicio afectado</label>
          <input value={form.affected_service} onChange={e => update('affected_service', e.target.value)} required />
        </div>
        <div className="form-section">
          <label>Impacto general</label>
          <textarea value={form.impact_summary} onChange={e => update('impact_summary', e.target.value)} required />
          <label>Acciones iniciales realizadas</label>
          <textarea value={form.actions_taken} onChange={e => update('actions_taken', e.target.value)} />
          <label>Plan/política activada</label>
          <input value={form.policy_activated} onChange={e => update('policy_activated', e.target.value)} />
          <label>Evidencia</label>
          <textarea value={form.evidence_summary} onChange={e => update('evidence_summary', e.target.value)} />
          <button className="primary">Registrar SOS</button>
        </div>
      </form>
    </section>
  )
}
