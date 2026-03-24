import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuth } from "../../composables/useAuth"

// Mocks
vi.mock('./useConfig', () => ({
  useConfig: () => ({ API_BASE_URL: 'https://localhost:4443' })
}))
vi.stubGlobal('navigateTo', vi.fn())

describe('useAuth', () => {
  let auth: ReturnType<typeof useAuth>

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
    auth = useAuth()
    global.fetch = vi.fn() as any
  })

  it('debería guardar la sesión en storage (Caso normal)', () => {
    const userData = { id: 1, name: 'Admin', rol: 'admin' }
    auth.saveSession(userData, 'token123')

    expect(sessionStorage.getItem('session_token')).toBe('token123')
    expect(localStorage.getItem('session_token123')).toBe(JSON.stringify(userData))
  })

  it('debería obtener el token de sesión (Caso normal)', () => {
    sessionStorage.setItem('session_token', 'token-test')
    expect(auth.getSessionToken()).toBe('token-test')
  })

  it('debería retornar el usuario actual si existe (Caso normal)', () => {
    const userData = { id: 2, rol: 'empleado' }
    auth.saveSession(userData, 'token456')
    
    expect(auth.getCurrentUser()).toEqual(userData)
  })

  it('debería retornar null si no hay usuario o token (Caso límite)', () => {
    expect(auth.getCurrentUser()).toBeNull()
  })

  it('debería validar la sesión con el backend correctamente (Caso normal)', async () => {
    auth.saveSession({ id: 1 }, 'valid-token')
    
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ rol: 'admin' })
    })

    const result = await auth.checkSession()
    expect(result).toBe(true)
    expect(fetch).toHaveBeenCalledWith('https://localhost:4443/api/check_session', expect.any(Object))
    
    // Debería haber actualizado el rol
    const updatedUser = auth.getCurrentUser()
    expect(updatedUser.rol).toBe('admin')
  })

  it('debería retornar false si la API falla al verificar la sesión (Caso error)', async () => {
    auth.saveSession({ id: 1 }, 'invalid-token')
    
    ;(global.fetch as any).mockResolvedValue({
      ok: false
    })

    const result = await auth.checkSession()
    expect(result).toBe(false)
  })

  it('debería hacer logout y limpiar los storages (Caso normal)', async () => {
    auth.saveSession({ id: 1 }, 'token-logout')
    
    ;(global.fetch as any).mockResolvedValue({ ok: true })

    await auth.logout()

    expect(fetch).toHaveBeenCalledWith('https://localhost:4443/api/logout', expect.any(Object))
    expect(sessionStorage.getItem('session_token')).toBeNull()
    expect(localStorage.getItem('session_token-logout')).toBeNull()
  })
})
