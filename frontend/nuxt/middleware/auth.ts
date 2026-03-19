export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return

  const { checkSession, getCurrentUser } = useAuth()

  // First check if we have local session data
  const user = getCurrentUser()
  if (!user) {
    return navigateTo('/login')
  }

  // Then validate with backend
  const isAuthenticated = await checkSession()
  if (!isAuthenticated) {
    return navigateTo('/login')
  }

  // --- Redirigir al usuario a su página correcta según su rol ---
  // No cierra sesión, solo redirige al lugar correcto.
  const path = to.path

  if (user.rol === 1) {
    // Admin: puede ir a /admin, /empleados, /historial
    if (!['/admin', '/empleados', '/historial'].includes(path)) {
      return navigateTo('/admin', { replace: true })
    }
  } else if (user.rol === 6) {
    // Subjefe: puede ir a /subjefes, /historial
    if (!['/subjefes', '/historial'].includes(path)) {
      return navigateTo('/subjefes', { replace: true })
    }
  } else {
    // Ventanilla: solo puede ir a /ventanilla
    if (path !== '/ventanilla') {
      return navigateTo('/ventanilla', { replace: true })
    }
  }
})
