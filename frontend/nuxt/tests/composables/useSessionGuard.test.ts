import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useSessionGuard } from "../../composables/useSessionGuard"
import * as authComposable from "../../composables/useAuth"
import * as socketComposable from "../../composables/useSocket"

vi.mock('./useAuth')
vi.mock('./useSocket')

describe('useSessionGuard', () => {
  let guard: ReturnType<typeof useSessionGuard>
  let mockCheckSession: ReturnType<typeof vi.fn>
  let mockLogoutWithOverlay: ReturnType<typeof vi.fn>
  let mockGetCurrentUser: ReturnType<typeof vi.fn>
  let mockSocketOn: ReturnType<typeof vi.fn>
  let mockSocketOff: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.useFakeTimers()
    
    mockCheckSession = vi.fn().mockResolvedValue(true)
    mockLogoutWithOverlay = vi.fn().mockResolvedValue(undefined)
    mockGetCurrentUser = vi.fn().mockReturnValue({ id: 1 })

    vi.spyOn(authComposable, 'useAuth').mockReturnValue({
      checkSession: mockCheckSession,
      logoutWithOverlay: mockLogoutWithOverlay,
      getCurrentUser: mockGetCurrentUser,
      saveSession: vi.fn(),
      getSessionToken: vi.fn(),
      logout: vi.fn()
    })

    mockSocketOn = vi.fn()
    mockSocketOff = vi.fn()

    vi.spyOn(socketComposable, 'useSocket').mockReturnValue({
      on: mockSocketOn,
      off: mockSocketOff,
      connect: vi.fn(),
      emit: vi.fn(),
      disconnect: vi.fn(),
      connected: true,
      url: ''
    } as any)

    guard = useSessionGuard()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
    guard.stopGuard()
  })

  it('debería iniciar la vigilancia y escuchar eventos de socket (Caso normal)', () => {
    guard.startGuard()
    expect(mockSocketOn).toHaveBeenCalledWith('session_force_closed', expect.any(Function))
    expect(mockSocketOn).toHaveBeenCalledWith('sessions_reset', expect.any(Function))
  })

  it('debería cerrar sesión por inactividad después de 5 minutos (Caso límite de tiempo)', () => {
    guard.startGuard()
    
    // Avanzar 5 minutos
    vi.advanceTimersByTime(5 * 60 * 1000)
    
    expect(mockLogoutWithOverlay).toHaveBeenCalled()
  })

  it('debería validar sesión cada 30 segundos si hay actividad (Caso normal)', () => {
    guard.startGuard()

    // Simular un click para reiniciar actividad
    document.dispatchEvent(new Event('mousedown'))
    
    // Avanzar 30 segundos
    vi.advanceTimersByTime(30 * 1000)
    
    expect(mockCheckSession).toHaveBeenCalled()
    expect(mockLogoutWithOverlay).not.toHaveBeenCalled()
  })
  
  it('debería cerrar sesión si checkSession falla (Caso de error)', async () => {
    mockCheckSession.mockResolvedValueOnce(false)
    guard.startGuard()

    // Avanzar 30 segundos
    vi.advanceTimersByTime(30 * 1000)
    
    // Hay que esperar la ejecución asíncrona
    await vi.runAllTimersAsync()
    
    expect(mockLogoutWithOverlay).toHaveBeenCalled()
  })
})
