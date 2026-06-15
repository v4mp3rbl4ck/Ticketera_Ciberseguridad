import { useState } from 'react'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import TicketsPage from './pages/TicketsPage'
import KanbanPage from './pages/KanbanPage'
import ReportsPage from './pages/ReportsPage'
import NewTicketPage from './pages/NewTicketPage'
import TicketDetailPage from './pages/TicketDetailPage'
import SosPage from './pages/SosPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import AdminRolesPage from './pages/admin/AdminRolesPage'
import AdminUseCasesPage from './pages/admin/AdminUseCasesPage'
import AdminSlaPage from './pages/admin/AdminSlaPage'
import AdminCorporateAreasPage from './pages/admin/AdminCorporateAreasPage'
import AdminAuditPage from './pages/admin/AdminAuditPage'
import AdminQuestionsPage from './pages/admin/AdminQuestionsPage'
import ProfilePage from './pages/ProfilePage'

function Router() {
  const { user, loading } = useAuth()
  const [page, setPage] = useState('dashboard')
  const [selectedTicketId, setSelectedTicketId] = useState(null)

  if (loading) return <div className="center-screen">Cargando...</div>
  if (!user) return <LoginPage />

  function openTicket(id) {
    setSelectedTicketId(id)
    setPage('ticket-detail')
  }

  let content
  if (page === 'dashboard') content = <DashboardPage />
  if (page === 'tickets') content = <TicketsPage onOpenTicket={openTicket} />
  if (page === 'kanban') content = <KanbanPage onOpenTicket={openTicket} />
  if (page === 'reports') content = <ReportsPage />
  if (page === 'new-ticket') content = <NewTicketPage onCreated={openTicket} onGoSos={() => setPage('sos')} />
  if (page === 'ticket-detail') content = <TicketDetailPage ticketId={selectedTicketId} />
  if (page === 'sos') content = <SosPage />
  if (page === 'profile') content = <ProfilePage onOpenTicket={openTicket} />
  if (page === 'admin' || page === 'admin-users') content = <AdminUsersPage />
  if (page === 'admin-roles') content = <AdminRolesPage />
  if (page === 'admin-use-cases') content = <AdminUseCasesPage />
  if (page === 'admin-questions') content = <AdminQuestionsPage />
  if (page === 'admin-sla') content = <AdminSlaPage />
  if (page === 'admin-corporate-areas') content = <AdminCorporateAreasPage />
  if (page === 'admin-audit') content = <AdminAuditPage />

  return <Layout page={page} setPage={setPage} onOpenTicket={openTicket}>{content}</Layout>
}

export default function App() {
  return (
    <AuthProvider>
      <Router />
    </AuthProvider>
  )
}
