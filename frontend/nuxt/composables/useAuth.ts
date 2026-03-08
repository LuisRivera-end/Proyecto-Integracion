export const useAuth = () => {
  const { API_BASE_URL } = useConfig()

  const checkSession = async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/check_session`, {
        credentials: 'include',
      })
      return res.ok
    } catch {
      return false
    }
  }

  const logout = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/logout`, {
        method: 'POST',
        credentials: 'include',
      })
    } catch {
      // ignore
    }
    localStorage.removeItem('currentUser')
  }

  const logoutWithOverlay = async () => {
    await logout()
    // Create overlay
    const o = document.createElement('div')
    o.style.cssText =
      'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;cursor:not-allowed'
    o.innerHTML =
      '<p style="color:white;font-size:1.25rem;font-weight:bold">Cerrando sesión...</p>'
    document.body.appendChild(o)
    setTimeout(() => {
      document.body.removeChild(o)
      navigateTo('/login')
    }, 1500)
  }

  const getCurrentUser = () => {
    try {
      const data = localStorage.getItem('currentUser')
      return data ? JSON.parse(data) : null
    } catch {
      return null
    }
  }

  return { checkSession, logout, logoutWithOverlay, getCurrentUser }
}
