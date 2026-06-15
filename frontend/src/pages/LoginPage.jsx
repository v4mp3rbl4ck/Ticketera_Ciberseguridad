import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('admin@ticketera.cl')
  const [password, setPassword] = useState('Admin123!')
  const [error, setError] = useState('')

  async function submit(e) {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <h1>Ticketera Operacional</h1>
        <p>Ciberseguridad & Networking</p>
        <label>Correo</label>
        <input value={email} onChange={e => setEmail(e.target.value)} />
        <label>Contraseña</label>
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
        {error && <div className="alert error">{error}</div>}
        <button className="primary">Ingresar</button>
        <small>Demo: admin@ticketera.cl / Admin123!</small>
      </form>
    </div>
  )
}
