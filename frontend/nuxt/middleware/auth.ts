export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return

  const { checkSession, getCurrentUser, logout } = useAuth()

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

  // --- Validar rutas por rol ---
  // Si la ruta NO corresponde al rol → logout + login
  const path = to.path

  if (user.rol === 1) {
    // Admin: puede ir a /admin, /empleados, /historial, /pantalla
    if (!['/admin', '/empleados', '/historial', '/pantalla'].includes(path)) {
      await logout()
      return navigateTo('/login', { replace: true })
    }
  } else if (user.rol === 6) {
    // Subjefe: puede ir a /subjefes, /historial
    if (!['/subjefes', '/historial'].includes(path)) {
      await logout()
      return navigateTo('/login', { replace: true })
    }
  } else {
    // Ventanilla: solo puede ir a /ventanilla
    if (path !== '/ventanilla') {
      await logout()
      return navigateTo('/login', { replace: true })
    }
  }
})
