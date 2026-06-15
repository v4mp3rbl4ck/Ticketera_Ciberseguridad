import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../api/client'
import { APP_TIMEZONE, nowForDatetimeLocal } from '../utils/time'

const severities = ['Crítica/SOS', 'Alta', 'Media', 'Baja']
const technicalAreas = ['Ciberseguridad', 'Networking']
const NEW_USE_CASE = '__new_use_case__'
const subjectOptions = ['Solicitud de revision', 'Requerimiento', 'Validacion', 'Plan de mejora']
const affectedOptions = ['1', '5-10', 'Area completa', 'General']
const impactOptions = ['Operacion general', 'Servicios', 'Salida de prensa', 'Reportajes', 'Funcionamiento de areas']

const fallbackCorporateAreas = [
  'AREA LEGAL', 'AUDIO', 'CABLE', 'CALIDAD DE VIDA LABORAL', 'CAPACITACION',
  'COMUNICACIONES CORPORATIVAS', 'CONTABILIDAD', 'CONTENIDOS MULTIPLATAFORMAS',
  'CONTRALORIA', 'DESARROLLO MULTIPLATAFORMA', 'DIR PROCESOS CREATIVOS Y PROG.',
  'DIRECCION DE GESTION', 'DIRECCION EJECUTIVA', 'EQUIPOS DE PRODUCCION FIJO',
  'FINANZAS', 'GERENCIA DE INGENIERIA', 'GERENCIA DE MARKETING', 'GERENCIA DE PERSONAS',
  'GERENCIA DE PRODUCCION', 'ILUMINACION', 'INFORMATICA', 'INFRAESTRUCTURA Y SERVICIOS',
  'INVESTIGACION Y AUDIENCIAS', 'MANTENCION DE RED', 'MEDIOS DIGITALES', 'NUEVAS SEÑALES',
  'PERSONAL Y REMUNERACIONES', 'PLANIFICACION Y GESTION', 'PRENSA', 'PREVENCION DE RIESGOS',
  'PRODUCTORES EJECUTIVOS', 'REGIONAL CONCEPCION', 'REGIONAL VALPARAISO',
  'SERVICIOS ESCENOGRAFICOS', 'SOPORTE ELECTRICO', 'SOPORTE TECNICO',
  'SUPERVISION Y CONTROL TECNICO', 'TRANSMISION', 'TRANSPORTE Y MOVILIZACION',
  'VENTAS NEGOCIOS'
]

function isBlank(value) {
  return !String(value || '').trim()
}

export default function NewTicketPage({ onCreated, onGoSos }) {
  const [checklistInfo, setChecklistInfo] = useState({ questions: [], use_cases: [] })
  const [corporateAreas, setCorporateAreas] = useState(fallbackCorporateAreas)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [form, setForm] = useState({
    area_destino: 'Ciberseguridad',
    project_area: '',
    category: '',
    custom_category: '',
    severity: 'Media',
    subject: 'Solicitud de revision',
    description: '',
    involved_asset: '1',
    first_event_at: nowForDatetimeLocal(),
    evidence_summary: '',
    ip_address: '',
    hostname: '',
    impact: 'Servicios',
    scope_users_affected: '1',
    dynamic_answers: {},
  })

  useEffect(() => {
    apiFetch('/admin/corporate-areas')
      .then(data => {
        const names = Array.isArray(data) ? data.map(item => typeof item === 'string' ? item : item.name).filter(Boolean) : []
        setCorporateAreas(names.length ? names : fallbackCorporateAreas)
      })
      .catch(() => setCorporateAreas(fallbackCorporateAreas))
  }, [])

  useEffect(() => {
    apiFetch(`/tickets/checklist?area=${encodeURIComponent(form.area_destino)}&severity=${encodeURIComponent(form.severity)}`)
      .then(data => {
        const cases = data.use_cases || []
        setChecklistInfo(data)
        setForm(prev => ({ ...prev, category: cases[0] || NEW_USE_CASE, custom_category: '', dynamic_answers: {} }))
        setFieldErrors({})
      })
      .catch(err => {
        setChecklistInfo({ questions: [], use_cases: [] })
        setError(err.message)
      })
  }, [form.area_destino, form.severity])

  const selectedCategory = form.category === NEW_USE_CASE ? form.custom_category.trim() : form.category

  useEffect(() => {
    if (!selectedCategory || form.category === NEW_USE_CASE) return
    apiFetch(`/tickets/checklist?area=${encodeURIComponent(form.area_destino)}&severity=${encodeURIComponent(form.severity)}&category=${encodeURIComponent(selectedCategory)}`)
      .then(data => {
        setChecklistInfo(prev => ({ ...prev, questions: data.questions || [] }))
        setFieldErrors(prev => {
          const next = { ...prev }
          Object.keys(next).forEach(key => { if (key.startsWith('question_')) delete next[key] })
          return next
        })
      })
      .catch(() => {})
  }, [form.area_destino, form.severity, selectedCategory, form.category])

  const isCritical = form.severity === 'Crítica/SOS'
  const checklist = checklistInfo.questions || []
  const useCases = checklistInfo.use_cases || []
  const isNewUseCase = form.category === NEW_USE_CASE

  const severityClass = useMemo(() => {
    if (form.severity === 'Crítica/SOS') return 'critical'
    if (form.severity === 'Alta') return 'high'
    if (form.severity === 'Media') return 'medium'
    return 'low'
  }, [form.severity])

  function validateForm() {
    const nextErrors = {}

    if (isCritical) {
      nextErrors.severity = 'La severidad Crítica/SOS debe registrarse por el módulo SOS posterior a llamada.'
    }
    if (isBlank(form.project_area)) {
      nextErrors.project_area = 'Selecciona el área corporativa solicitante.'
    }
    if (isBlank(selectedCategory)) {
      nextErrors.category = 'Selecciona o ingresa un caso de uso específico.'
    }
    if (isNewUseCase && selectedCategory.length < 4) {
      nextErrors.custom_category = 'El nuevo caso de uso debe tener al menos 4 caracteres.'
    }
    if (isBlank(form.subject)) {
      nextErrors.subject = 'Selecciona el asunto claro.'
    }
    if (isBlank(form.impact)) {
      nextErrors.impact = 'Selecciona el impacto operacional.'
    }
    if (isBlank(form.scope_users_affected)) {
      nextErrors.scope_users_affected = 'Selecciona usuario afectado o alcance.'
    }
    if (isBlank(form.description) || form.description.trim().length < 8) {
      nextErrors.description = 'Describe brevemente el objetivo o contexto con al menos 8 caracteres.'
    }
    if (isBlank(form.first_event_at)) {
      nextErrors.first_event_at = 'Indica fecha y hora del primer evento.'
    }

    checklist.forEach(q => {
      const value = form.dynamic_answers[q.key]
      if (q.required && isBlank(value)) {
        nextErrors[`question_${q.key}`] = 'Esta pregunta es requerida para formalizar el ticket.'
      }
    })

    setFieldErrors(nextErrors)
    return nextErrors
  }

  function update(key, value) {
    setForm(prev => ({ ...prev, [key]: value }))
    setFieldErrors(prev => {
      const next = { ...prev }
      delete next[key]
      return next
    })
  }

  function updateArea(value) {
    setForm(prev => ({ ...prev, area_destino: value, dynamic_answers: {} }))
  }

  function updateSeverity(value) {
    setForm(prev => ({ ...prev, severity: value, dynamic_answers: {} }))
  }

  function updateAffected(value) {
    setForm(prev => ({ ...prev, involved_asset: value, scope_users_affected: value }))
    setFieldErrors(prev => {
      const next = { ...prev }
      delete next.scope_users_affected
      return next
    })
  }

  function updateAnswer(key, value) {
    setForm(prev => ({ ...prev, dynamic_answers: { ...prev.dynamic_answers, [key]: value } }))
    setFieldErrors(prev => {
      const next = { ...prev }
      delete next[`question_${key}`]
      return next
    })
  }

  async function submit(e) {
    e.preventDefault()
    setError('')

    const validationErrors = validateForm()
    if (Object.keys(validationErrors).length > 0) {
      setError('Revisa los campos marcados antes de crear el ticket.')
      const firstInvalid = document.querySelector('.field-invalid, .question.invalid textarea')
      firstInvalid?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      return
    }

    const payload = {
      area_destino: form.area_destino,
      project_area: form.project_area,
      category: selectedCategory,
      severity: form.severity,
      subject: form.subject,
      description: form.description,
      involved_asset: form.involved_asset,
      first_event_at: form.first_event_at || null,
      evidence_summary: form.evidence_summary,
      ip_address: form.ip_address,
      hostname: form.hostname,
      impact: form.impact,
      scope_users_affected: form.scope_users_affected,
      deadline: null,
      deadline_justification: null,
      dynamic_answers: checklist.map(q => ({
        question_key: q.key,
        question_text: q.text,
        answer: form.dynamic_answers[q.key] || '',
        required: q.required,
      })),
    }

    try {
      const created = await apiFetch('/tickets', { method: 'POST', body: JSON.stringify(payload) })
      onCreated(created.id)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="page">
      <h1>Nuevo Ticket</h1>
      <p>Formulario dinámico por área técnica, severidad y caso de uso. Los campos obligatorios se validan antes de crear la solicitud.</p>
      <p className="timezone-hint">Horario del sistema: {APP_TIMEZONE}</p>
      {error && <div className="alert error">{error}</div>}

      <div className={`catalog-summary ${severityClass}`}>
        <div><span className="eyebrow">Área técnica</span><strong>{form.area_destino}</strong></div>
        <div><span className="eyebrow">Severidad</span><strong>{form.severity}</strong></div>
        <div><span className="eyebrow">Canal</span><strong>{checklistInfo.channel || 'Correo/Ticket'}</strong></div>
        <p>{checklistInfo.description}</p>
      </div>

      {isCritical && (
        <div className="alert warning">
          Este caso corresponde a SOS. El contacto inicial debe ser por llamada a jefatura. Luego registra el evento en el módulo Registro SOS.
          {onGoSos && <button type="button" className="primary inline-action" onClick={onGoSos}>Ir a Registro SOS</button>}
        </div>
      )}

      <form className="form-grid enterprise-form" onSubmit={submit} noValidate>
        <div className="form-section compact-section classification-card">
          <h2>01 · Clasificación</h2>
          <div className="field-grid single">
            <FormField label="Área técnica destino">
              <select value={form.area_destino} onChange={e => updateArea(e.target.value)}>{technicalAreas.map(a => <option key={a}>{a}</option>)}</select>
            </FormField>
            <FormField label="Severidad / Categoría principal" error={fieldErrors.severity}>
              <select value={form.severity} onChange={e => updateSeverity(e.target.value)}>{severities.map(s => <option key={s}>{s}</option>)}</select>
            </FormField>
            <FormField label="Caso de uso específico" error={fieldErrors.category}>
              <select className={fieldErrors.category ? 'field-invalid' : ''} value={form.category} onChange={e => update('category', e.target.value)} disabled={isCritical}>
                {useCases.map(c => <option key={c} value={c}>{c}</option>)}
                <option value={NEW_USE_CASE}>Otro / añadir nuevo caso de uso</option>
              </select>
            </FormField>
            {isNewUseCase && (
              <FormField label="Nuevo caso de uso" error={fieldErrors.custom_category} help="Al crear el ticket, el caso quedará disponible en el catálogo dinámico.">
                <input className={fieldErrors.custom_category ? 'field-invalid' : ''} value={form.custom_category} onChange={e => update('custom_category', e.target.value)} placeholder="Ej: Validación de acceso a herramienta interna" disabled={isCritical} />
              </FormField>
            )}
          </div>
        </div>

        <div className="form-section compact-section request-card">
          <h2>02 · Solicitud</h2>
          <div className="field-grid two compact-grid">
            <FormField label="Área corporativa solicitante" error={fieldErrors.project_area}>
              <select className={fieldErrors.project_area ? 'field-invalid' : ''} value={form.project_area} onChange={e => update('project_area', e.target.value)} disabled={isCritical}>
                <option value="">Seleccionar área...</option>
                {corporateAreas.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </FormField>
            <FormField label="Usuario afectado / Alcance" error={fieldErrors.scope_users_affected}>
              <select value={form.scope_users_affected} onChange={e => updateAffected(e.target.value)} disabled={isCritical}>
                {affectedOptions.map(option => <option key={option} value={option}>{option}</option>)}
              </select>
            </FormField>
            <FormField label="Asunto claro" error={fieldErrors.subject}>
              <select value={form.subject} onChange={e => update('subject', e.target.value)} disabled={isCritical}>
                {subjectOptions.map(option => <option key={option} value={option}>{option}</option>)}
              </select>
            </FormField>
            <FormField label="Impacto operacional" error={fieldErrors.impact}>
              <select value={form.impact} onChange={e => update('impact', e.target.value)} disabled={isCritical}>
                {impactOptions.map(option => <option key={option} value={option}>{option}</option>)}
              </select>
            </FormField>
            <FormField label="Descripción breve" error={fieldErrors.description} className="span-2">
              <textarea className={`compact-textarea ${fieldErrors.description ? 'field-invalid' : ''}`} value={form.description} onChange={e => update('description', e.target.value)} placeholder="Describe el objetivo final o contexto necesario para resolver la solicitud" disabled={isCritical} />
            </FormField>
          </div>
        </div>

        <div className="form-section compact-section technical-card full">
          <h2>03 · Datos técnicos</h2>
          <div className="field-grid four compact-grid">
            <FormField label="Fecha/hora primer evento" error={fieldErrors.first_event_at} help="Por defecto se usa la hora actual de Chile.">
              <input className={fieldErrors.first_event_at ? 'field-invalid' : ''} type="datetime-local" value={form.first_event_at} onChange={e => update('first_event_at', e.target.value)} disabled={isCritical} />
            </FormField>
            <FormField label="IP">
              <input value={form.ip_address} onChange={e => update('ip_address', e.target.value)} placeholder="Opcional" disabled={isCritical} />
            </FormField>
            <FormField label="Hostname">
              <input value={form.hostname} onChange={e => update('hostname', e.target.value)} placeholder="Opcional" disabled={isCritical} />
            </FormField>
            <FormField label="Evidencia disponible">
              <input value={form.evidence_summary} onChange={e => update('evidence_summary', e.target.value)} placeholder="Correo, logs, capturas, alerta" disabled={isCritical} />
            </FormField>
          </div>
        </div>

        <div className="form-section full dynamic-section">
          <div className="section-title-row">
            <div>
              <h2>Información requerida según matriz</h2>
              <p className="section-help">Estas preguntas son administradas por el rol Administrador en el módulo Preguntas Requeridas.</p>
            </div>
            <span className="required-counter">{checklist.filter(q => q.required).length} obligatorias</span>
          </div>
          <div className="question-grid">
            {checklist.map(q => {
              const key = `question_${q.key}`
              return (
                <div className={`question ${fieldErrors[key] ? 'invalid' : ''}`} key={q.key}>
                  <label>{q.text} {q.required && <span className="required-mark">*</span>}</label>
                  <textarea value={form.dynamic_answers[q.key] || ''} onChange={e => updateAnswer(q.key, e.target.value)} disabled={isCritical} placeholder="Respuesta requerida para formalizar la solicitud" />
                  {fieldErrors[key] && <small className="field-error">{fieldErrors[key]}</small>}
                </div>
              )
            })}
            {checklist.length === 0 && <p>No hay preguntas requeridas configuradas para esta combinación.</p>}
          </div>
        </div>

        <div className="form-actions full">
          <button className="primary" disabled={isCritical}>Crear ticket</button>
        </div>
      </form>
    </section>
  )
}

function FormField({ label, error, help, className = '', children }) {
  return (
    <div className={`form-field ${error ? 'has-error' : ''} ${className}`}>
      <label>{label}</label>
      {children}
      {help && <small>{help}</small>}
      {error && <small className="field-error">{error}</small>}
    </div>
  )
}
