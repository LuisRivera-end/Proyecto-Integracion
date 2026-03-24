import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingOverlay from '../../components/LoadingOverlay.vue'
import * as configComposable from '../../composables/useConfig'

// Mock composable
vi.mock('../../composables/useConfig', () => ({
  useConfig: () => ({ API_BASE_URL: 'https://localhost:4443' })
}))

describe('LoadingOverlay.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  it('debería mostrarse inicialmente (Caso normal)', () => {
    global.fetch = vi.fn().mockReturnValue(new Promise(() => {})) // Nunca resuelve
    
    const wrapper = mount(LoadingOverlay)
    
    expect(wrapper.find('#loading-overlay').exists()).toBe(true)
    expect(wrapper.text()).toContain('Conectando con el servidor')
  })

  it('debería ocultarse si el fetch es exitoso (Caso normal)', async () => {
    // Simulamos respuesta OK
    global.fetch = vi.fn().mockResolvedValue({ ok: true })
    
    const wrapper = mount(LoadingOverlay)

    // Esperar a que se resuelvan las promesas
    await vi.runAllTimersAsync()
    
    expect(wrapper.vm.visible).toBe(false)
  })

  it('debería reintentar si el fetch falla (Caso de error)', async () => {
    let callCount = 0
    global.fetch = vi.fn().mockImplementation(() => {
      callCount++
      if (callCount === 1) return Promise.reject(new Error('Network error'))
      return Promise.resolve({ ok: true })
    })

    const wrapper = mount(LoadingOverlay)
    
    // Avanzar el tiempo para el reintento de 2 segundos
    await vi.advanceTimersByTimeAsync(2500)
    
    expect(fetch).toHaveBeenCalledTimes(2)
    expect(wrapper.vm.visible).toBe(false)
  })
})
