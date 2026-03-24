import { useAuth } from './useAuth'
import { useSocket } from './useSocket'

/**
 * useSessionGuard – Vigilancia activa de sesión
 *
 * • Detecta inactividad de 5 minutos → logout + redirect a /login
 * • Heartbeat cada 30 s que valida la sesión en el backend (y la extiende si hay actividad)
 * • Escucha WS `session_force_closed` → si el empleado afectado es el actual → logout
 * • Escucha WS `sessions_reset` → logout inmediato (reinicio de emergencia)
 */
export const useSessionGuard = () => {
  const { checkSession, logoutWithOverlay, getCurrentUser } = useAuth()
  const socket = useSocket()

  let lastActivity = Date.now()
  let heartbeatInterval: ReturnType<typeof setInterval> | null = null
  let isLoggingOut = false

  const INACTIVITY_TIMEOUT = 5 * 60 * 1000   // 5 minutos
  const HEARTBEAT_INTERVAL = 30 * 1000        // 30 segundos

  // ── Helpers ──────────────────────────────────────────────
  const onActivity = () => {
    lastActivity = Date.now()
  }

  const forceLogout = async () => {
    if (isLoggingOut) return
    isLoggingOut = true
    stopGuard()
    await logoutWithOverlay()
  }

  // ── WS handlers ─────────────────────────────────────────
  const onSessionForceClosed = async (data: any) => {
    const user = getCurrentUser()
    if (data && user && data.employee_id === user.id) {
      console.log('🚫 Sesión forzada a cerrar por administrador')
      await forceLogout()
    }
  }

  const onSessionsReset = async () => {
    console.log('🔄 Todas las sesiones han sido reiniciadas')
    await forceLogout()
  }

  // ── Start / Stop ────────────────────────────────────────
  const ACTIVITY_EVENTS = ['mousedown', 'keydown', 'scroll', 'touchstart', 'mousemove']

  const startGuard = () => {
    lastActivity = Date.now()
    isLoggingOut = false

    // Rastrear actividad del usuario
    ACTIVITY_EVENTS.forEach(e =>
      document.addEventListener(e, onActivity, { passive: true })
    )

    // Listeners de WebSocket
    socket.on('session_force_closed', onSessionForceClosed)
    socket.on('sessions_reset', onSessionsReset)

    // Heartbeat periódico
    heartbeatInterval = setInterval(async () => {
      if (isLoggingOut) return

      const elapsed = Date.now() - lastActivity

      // Sin actividad por 5 minutos → cerrar sesión
      if (elapsed >= INACTIVITY_TIMEOUT) {
        console.log('⏱️ Inactividad de 5 minutos detectada — cerrando sesión')
        await forceLogout()
        return
      }

      // Hay actividad reciente → verificar sesión con el backend (también la extiende)
      const valid = await checkSession()
      if (!valid) {
        console.log('❌ Sesión no válida en el backend — cerrando sesión')
        await forceLogout()
      }
    }, HEARTBEAT_INTERVAL)
  }

  const stopGuard = () => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
    }
    ACTIVITY_EVENTS.forEach(e =>
      document.removeEventListener(e, onActivity)
    )
    socket.off('session_force_closed', onSessionForceClosed)
    socket.off('sessions_reset', onSessionsReset)
  }

  return { startGuard, stopGuard }
}
