export const useAuth = () => {
  const { API_BASE_URL } = useConfig()

  /**
   * Guarda los datos de sesión.
   * Almacena el token en sessionStorage (por pestaña) y los datos del usuario en localStorage indexados por el token.
   * 
   * @param {any} userData - Los datos del usuario a guardar.
   * @param {string} sessionToken - El token de la sesión.
   */
  const saveSession = (userData: any, sessionToken: string) => {
    sessionStorage.setItem('session_token', sessionToken)
    localStorage.setItem(`session_${sessionToken}`, JSON.stringify(userData))
  }

  /**
   * Obtiene el token de sesión para la pestaña actual.
   * 
   * @returns {string | null} El token de sesión si existe, o null en caso contrario.
   */
  const getSessionToken = (): string | null => {
    return sessionStorage.getItem('session_token')
  }

  /**
   * Obtiene los datos del usuario actual utilizando el token de sesión de la pestaña actual.
   * 
   * @returns {any | null} Los datos del usuario si existen, o null en caso contrario o si hay un error.
   */
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

  /**
   * Verifica si el token de sesión de la pestaña actual sigue siendo válido en el backend.
   * Envía SOLO el token al backend y actualiza el rol local si es necesario.
   * 
   * @returns {Promise<boolean>} Promesa que resuelve a true si la sesión es válida, false en caso contrario.
   */
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

  /**
   * Cierra la sesión enviando el token al backend y limpia los datos locales.
   * 
   * @returns {Promise<void>}
   */
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

  /**
   * Cierra la sesión, muestra una capa superpuesta de carga y redirige a la página de inicio de sesión.
   * 
   * @returns {Promise<void>}
   */
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
