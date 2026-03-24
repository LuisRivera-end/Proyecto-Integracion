import { useAuth } from './useAuth'
import { useSocket } from './useSocket'

/**
 * Proporciona un mecanismo de vigilancia activa de sesión.
 * 
 * Funcionalidades principales:
 * - Detecta inactividad de 5 minutos y cierra la sesión redirigiendo al login.
 * - Realiza un latido (heartbeat) cada 30 segundos para validar la sesión en el backend.
 * - Escucha eventos del WebSocket para forzar el cierre de sesión ('session_force_closed' y 'sessions_reset').
 * 
 * @returns {{ startGuard: () => void, stopGuard: () => void }} Funciones para iniciar y detener el guardián de sesión.
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
  /**
   * Actualiza el tiempo de última actividad detectada.
   */
  const onActivity = () => {
    lastActivity = Date.now()
  }

  /**
   * Fuerza el cierre de sesión de manera asíncrona.
   * Evita llamadas múltiples estableciendo la bandera isLoggingOut.
   * 
   * @returns {Promise<void>}
   */
  const forceLogout = async () => {
    if (isLoggingOut) return
    isLoggingOut = true
    stopGuard()
    await logoutWithOverlay()
  }

  // ── WS handlers ─────────────────────────────────────────
  /**
   * Manejador del evento de WebSocket que fuerza el cierre de sesión de un usuario específico.
   * 
   * @param {any} data - Los datos recibidos del servidor WebSocket, esperando que contenga el employee_id.
   * @returns {Promise<void>}
   */
  const onSessionForceClosed = async (data: any) => {
    const user = getCurrentUser()
    if (data && user && data.employee_id === user.id) {
      console.log('🚫 Sesión forzada a cerrar por administrador')
      await forceLogout()
    }
  }

  /**
   * Manejador del evento de WebSocket que fuerza el cierre de todas las sesiones activas.
   * 
   * @returns {Promise<void>}
   */
  const onSessionsReset = async () => {
    console.log('🔄 Todas las sesiones han sido reiniciadas')
    await forceLogout()
  }

  // ── Start / Stop ────────────────────────────────────────
  const ACTIVITY_EVENTS = ['mousedown', 'keydown', 'scroll', 'touchstart', 'mousemove']

  /**
   * Inicia la vigilancia de inactividad, añade escuchadores de eventos y el intervalo de verificación.
   */
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

  /**
   * Detiene la vigilancia de la sesión y remueve todos los escuchadores y el intervalo del latido.
   */
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
