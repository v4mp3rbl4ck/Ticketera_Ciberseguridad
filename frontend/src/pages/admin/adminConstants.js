export const severities = ['Crítica/SOS', 'Alta', 'Media', 'Baja']
export const technicalAreas = ['Ciberseguridad', 'Networking']
export const roles = ['requester', 'analyst', 'supervisor', 'admin']

export function roleLabel(role) {
  const labels = {
    requester: 'Solicitante',
    analyst: 'Analista',
    supervisor: 'Supervisor',
    admin: 'Administrador',
  }
  return labels[role] || role
}
