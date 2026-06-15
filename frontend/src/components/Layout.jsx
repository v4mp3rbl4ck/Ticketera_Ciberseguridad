import { BarChart3, ShieldAlert, Ticket, PlusCircle, Users, ClipboardList, Timer, Building2, ScrollText, LogOut, HelpCircle, UserCircle, KeyRound, FileBarChart2 } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import NotificationBell from './NotificationBell'

const mainNavItems = [
  { key: 'dashboard', module: 'dashboard', label: 'Dashboard', icon: BarChart3, fallbackRoles: ['requester', 'analyst', 'supervisor', 'admin'] },
  { key: 'tickets', module: 'tickets', label: 'Tickets', icon: Ticket, fallbackRoles: ['requester', 'analyst', 'supervisor', 'admin'] },
  { key: 'kanban', module: 'kanban', label: 'Kanban', icon: ClipboardList, fallbackRoles: ['analyst', 'supervisor', 'admin'] },
  { key: 'reports', module: 'reports', label: 'Reportes', icon: FileBarChart2, fallbackRoles: ['analyst', 'supervisor', 'admin'] },
  { key: 'new-ticket', module: 'new_ticket', label: 'Nuevo Ticket', icon: PlusCircle, fallbackRoles: ['requester', 'analyst', 'supervisor', 'admin'] },
  { key: 'sos', module: 'sos', label: 'Registro SOS', icon: ShieldAlert, fallbackRoles: ['analyst', 'supervisor', 'admin'] },
  { key: 'profile', module: 'profile', label: 'Perfil', icon: UserCircle, fallbackRoles: ['requester', 'analyst', 'supervisor', 'admin'] },
]

const adminNavItems = [
  { key: 'admin-users', module: 'admin_users', label: 'Usuarios', icon: Users, fallbackRoles: ['admin'] },
  { key: 'admin-roles', module: 'admin_roles', label: 'Roles', icon: KeyRound, fallbackRoles: ['admin'] },
  { key: 'admin-use-cases', module: 'admin_use_cases', label: 'Casos de Uso', icon: ClipboardList, fallbackRoles: ['admin', 'analyst', 'supervisor'] },
  { key: 'admin-questions', module: 'admin_questions', label: 'Preguntas Requeridas', icon: HelpCircle, fallbackRoles: ['admin'] },
  { key: 'admin-sla', module: 'admin_sla', label: 'SLA', icon: Timer, fallbackRoles: ['admin', 'analyst', 'supervisor'] },
  { key: 'admin-corporate-areas', module: 'admin_corporate_areas', label: 'Áreas Corporativas', icon: Building2, fallbackRoles: ['admin', 'analyst', 'supervisor'] },
  { key: 'admin-audit', module: 'admin_audit', label: 'Auditoría', icon: ScrollText, fallbackRoles: ['admin', 'analyst', 'supervisor'] },
]

function canView(user, item) {
  if (!user) return false
  if (user.permissions?.[item.module]?.view) return true
  return item.fallbackRoles?.includes(user.role)
}

export default function Layout({ children, page, setPage, onOpenTicket }) {
  const { user, logout } = useAuth()
  const visibleMainItems = mainNavItems.filter(item => canView(user, item))
  const visibleAdminItems = adminNavItems.filter(item => canView(user, item))

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">CS</div>
          <div>
            <strong>Ticketera</strong>
            <span>Ciberseguridad & Networking</span>
          </div>
        </div>

        <nav className="nav">
          {visibleMainItems.map(item => {
            const Icon = item.icon
            return (
              <button key={item.key} className={page === item.key ? 'active' : ''} onClick={() => setPage(item.key)}>
                <Icon size={18} /> {item.label}
              </button>
            )
          })}

          {visibleAdminItems.length > 0 && (
            <>
              <div className="nav-section-title">Administración</div>
              {visibleAdminItems.map(item => {
                const Icon = item.icon
                return (
                  <button key={item.key} className={page === item.key || (page === 'admin' && item.key === 'admin-users') ? 'active' : ''} onClick={() => setPage(item.key)}>
                    <Icon size={18} /> {item.label}
                  </button>
                )
              })}
            </>
          )}
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <strong>{user.full_name}</strong>
            <span>{user.role} {user.area ? `· ${user.area}` : ''}</span>
          </div>
          <div className="topbar-actions">
            <NotificationBell onOpenTicket={onOpenTicket} />
            <button className="ghost" onClick={logout}><LogOut size={16} /> Salir</button>
          </div>
        </header>
        {children}
      </main>
    </div>
  )
}
