import { useAuth } from './useAuth'
import { useSocket } from './useSocket'

/**
 * Proporciona un mecanismo de vigilancia activa de sesión.
 * 
 * Funcionalidades principales:
 * - Realiza un latido (heartbeat) cada 30 segundos para validar la sesión en el backend.
 * - Escucha eventos del WebSocket para forzar el cierre de sesión ('session_force_closed' y 'sessions_reset').
 * 
 * @returns {{ startGuard: () => void, stopGuard: () => void }} Funciones para iniciar y detener el guardián de sesión.
 */
export const useSessionGuard = () => {
  const { checkSession, logoutWithOverlay, getCurrentUser } = useAuth()
  const socket = useSocket()

  let heartbeatInterval: ReturnType<typeof setInterval> | null = null
  let isLoggingOut = false

  const HEARTBEAT_INTERVAL = 30 * 1000        // 30 segundos

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

  /**
   * Inicia la vigilancia de sesión con heartbeat y escuchadores de WebSocket.
   */
  const startGuard = () => {
    isLoggingOut = false

    // Listeners de WebSocket
    socket.on('session_force_closed', onSessionForceClosed)
    socket.on('sessions_reset', onSessionsReset)

    // Heartbeat periódico — solo valida la sesión con el backend
    heartbeatInterval = setInterval(async () => {
      if (isLoggingOut) return

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
    socket.off('session_force_closed', onSessionForceClosed)
    socket.off('sessions_reset', onSessionsReset)
  }

  return { startGuard, stopGuard }
}
