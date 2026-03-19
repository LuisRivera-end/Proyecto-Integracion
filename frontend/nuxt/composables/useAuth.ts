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

  /** Check if this tab's session token is still valid on the backend */
  const checkSession = async (): Promise<boolean> => {
    try {
      const token = getSessionToken()
      const user = getCurrentUser()
      if (!token || !user) return false

      const res = await fetch(`${API_BASE_URL}/api/check_session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ session_token: token, employee_id: user.id })
      })
      return res.ok
    } catch {
      return false
    }
  }

  /** Logout: clear only this tab's session */
  const logout = async () => {
    const token = getSessionToken()
    const user = getCurrentUser()

    try {
      if (token && user) {
        await fetch(`${API_BASE_URL}/api/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ session_token: token, employee_id: user.id })
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
