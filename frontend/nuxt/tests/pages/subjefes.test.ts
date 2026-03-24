import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Subjefes from "../../pages/subjefes.vue"

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
    emit: vi.fn(),
    connected: true
  })
}))

vi.mock('../../composables/useAuth', () => ({
  useAuth: () => ({ 
    getCurrentUser: vi.fn().mockReturnValue({ id: 1, rol: 6, sector: 'Cajas', id_sector: 1 }),
    getSessionToken: vi.fn().mockReturnValue('fake-token')
  })
}))

vi.mock('../../composables/useSessionGuard', () => ({
  useSessionGuard: () => ({ startGuard: vi.fn(), stopGuard: vi.fn() })
}))

vi.stubGlobal('useHead', vi.fn())
vi.stubGlobal('definePageMeta', vi.fn())
vi.stubGlobal('navigateTo', vi.fn())

describe('subjefes.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([])
    }) as any
  })

  it('debería montar correctamente', async () => {
    const wrapper = mount(Subjefes)
    await new Promise(r => setTimeout(r, 0))
    expect(wrapper.exists()).toBe(true)
  })
})
