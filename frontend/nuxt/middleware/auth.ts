export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return

  const { checkSession } = useAuth()
  const isAuthenticated = await checkSession()

  if (!isAuthenticated) {
    return navigateTo('/login')
  }
})
