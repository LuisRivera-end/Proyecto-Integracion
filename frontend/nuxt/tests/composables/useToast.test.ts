import { describe, it, expect, vi } from 'vitest'
import { useToast } from "../../composables/useToast"
import Toastify from 'toastify-js'

// Mock de toastify-js
vi.mock('toastify-js', () => {
  return {
    default: vi.fn(() => ({
      showToast: vi.fn()
    }))
  }
})

describe('useToast', () => {
  it('debería llamar a Toastify con el estilo success por defecto (Caso normal)', () => {
    const { lanzarAlerta } = useToast()
    lanzarAlerta('Mensaje de prueba')

    expect(Toastify).toHaveBeenCalled()
    // Verificar que el background corresponde a success
    const mockCall = vi.mocked(Toastify).mock.calls[0][0]
    expect(mockCall.text).toBe('Mensaje de prueba')
    expect(mockCall.style?.background).toBe('linear-gradient(to right, #00b09b, #96c93d)')
  })

  it('debería utilizar el background de error si se especifica el tipo "error" (Caso de error cubierto visualmente)', () => {
    vi.clearAllMocks()
    const { lanzarAlerta } = useToast()
    lanzarAlerta('Ocurrió un error', 'error')

    expect(Toastify).toHaveBeenCalled()
    const mockCall = vi.mocked(Toastify).mock.calls[0][0]
    expect(mockCall.text).toBe('Ocurrió un error')
    expect(mockCall.style?.background).toBe('linear-gradient(to right, #ff5f6d, #ffc371)')
  })

  it('debería utilizar success de fallback si el tipo es desconocido o inválido (Caso límite)', () => {
    vi.clearAllMocks()
    const { lanzarAlerta } = useToast()
    // Forzamos un tipo inválido en TS usando any
    lanzarAlerta('Alerta rara', 'tipoInexistente' as any)

    expect(Toastify).toHaveBeenCalled()
    const mockCall = vi.mocked(Toastify).mock.calls[0][0]
    // Debe caer en BACKGROUNDS.success
    expect(mockCall.style?.background).toBe('linear-gradient(to right, #00b09b, #96c93d)')
  })
})
