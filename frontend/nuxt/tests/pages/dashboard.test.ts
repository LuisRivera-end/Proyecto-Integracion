import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Dashboard from "../../pages/dashboard.vue"

vi.mock('../../composables/useConfig', () => ({
  useConfig: () => ({ API_BASE_URL: 'https://localhost:4443' })
}))

vi.mock('../../composables/useToast', () => ({
  useToast: () => ({ lanzarAlerta: vi.fn() })
}))

vi.mock('../../composables/useSocket', () => ({
  useSocket: () => ({
    on: vi.fn(),
    off: vi.fn(),
    connected: true
  })
}))

vi.mock('../../composables/useAuth', () => ({
  useAuth: () => ({ getSessionToken: vi.fn().mockReturnValue('fake-token') })
}))

vi.mock('../../composables/useSessionGuard', () => ({
  useSessionGuard: () => ({ startGuard: vi.fn(), stopGuard: vi.fn() })
}))

vi.stubGlobal('useHead', vi.fn())
vi.stubGlobal('definePageMeta', vi.fn())

describe('dashboard.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        tickets_en_cola: 10,
        tickets_atendiendo: 2,
        tickets_completados_hoy: 50,
        empleados_activos: 5,
        empleados_en_ventanilla: 5,
        tiempo_espera_promedio_segundos: 120,
        por_sector: [
          { id_sector: 1, nombre: 'Control Escolar', tickets_en_cola: 0, ventanillas_activas: 2 }
        ]
      })
    }) as any
  })

  it('debería montar y solicitar estadísticas (Caso normal)', async () => {
    const wrapper = mount(Dashboard)
    
    // Esperar a que se monte y haga el fetch
    await new Promise(r => setTimeout(r, 0))

    expect(global.fetch).toHaveBeenCalled()
    // Comprobar que los KPIs se renderizan (10 en cola, 2 atendiendo, 50 completados)
    expect(wrapper.text()).toContain('10')
    expect(wrapper.text()).toContain('50')
    expect(wrapper.text()).toContain('Control Escolar')
  })
})
