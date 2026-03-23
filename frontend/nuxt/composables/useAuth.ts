export const useAuth = () => {
  const { API_BASE_URL } = useConfig()

  /** Save session data: token in sessionStorage (per-tab), user data in localStorage keyed by token */
  const saveSession = (userData: any, sessionToken: string) => {
    sessionStorage.setItem('session_token', sessionToken)
    localStorage.setItem(`session_${sessionToken}`, JSON.stringify(userData))
  }

  /** Get the session token for this tab */
  const getSessionToken = (): string | null => {
    return sessionStorage.getItem('session_token')
  }

  /** Get current user data using this tab's session token */
  const getCurrentUser = () => {
    try {
      const token = getSessionToken()
      if (!token) return null
      const data = localStorage.getItem(`session_${token}`)
      return data ? JSON.parse(data) : null
    } catch {
      return null
    }
  }

  /** Check if this tab's session token is still valid on the backend.
   *  Envía SOLO el token — el backend retorna {user_id, rol}. */
  const checkSession = async (): Promise<boolean> => {
    try {
      const token = getSessionToken()
      if (!token) return false

      const res = await fetch(`${API_BASE_URL}/api/check_session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ session_token: token })
      })

      if (!res.ok) return false

      // Actualizar los datos locales con el rol del backend (fuente de verdad)
      const data = await res.json()
      const user = getCurrentUser()
      if (user && data.rol !== undefined) {
        user.rol = data.rol
        localStorage.setItem(`session_${token}`, JSON.stringify(user))
      }

      return true
    } catch {
      return false
    }
  }

  /** Logout: envía solo el token al backend */
  const logout = async () => {
    const token = getSessionToken()

    try {
      if (token) {
        await fetch(`${API_BASE_URL}/api/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ session_token: token })
        })
      }
    } catch {
      // ignore
    }

    // Clear only this tab's data
    if (token) {
      localStorage.removeItem(`session_${token}`)
    }
    sessionStorage.removeItem('session_token')
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

  return { saveSession, getSessionToken, getCurrentUser, checkSession, logout, logoutWithOverlay }
}
