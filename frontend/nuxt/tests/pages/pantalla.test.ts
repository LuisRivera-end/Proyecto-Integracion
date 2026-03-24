import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Pantalla from "../../pages/pantalla.vue"

vi.mock('../../composables/useConfig', () => ({
  useConfig: () => ({ API_BASE_URL: 'https://localhost:4443' })
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
    getCurrentUser: vi.fn().mockReturnValue({ id: 1 }),
    getSessionToken: vi.fn().mockReturnValue('fake-token')
  })
}))

vi.stubGlobal('useHead', vi.fn())
vi.stubGlobal('definePageMeta', vi.fn())

// Fix for Nuxt publicAssetsURL error
vi.stubGlobal('useRuntimeConfig', () => ({ app: { baseURL: '/', buildAssetsDir: '/_nuxt/', cdnURL: '' } }))
;(globalThis as any).__NUXT__ = { config: { app: { baseURL: '/', buildAssetsDir: '/_nuxt/', cdnURL: '' } } }
;(window as any).__NUXT__ = { config: { app: { baseURL: '/', buildAssetsDir: '/_nuxt/', cdnURL: '' } } }

describe('pantalla.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([])
    }) as any
  })

  it('debería montar correctamente', async () => {
    const wrapper = mount(Pantalla, {
      global: {
        stubs: { NuxtLink: true, LoadingOverlay: true }
      }
    })
    await new Promise(r => setTimeout(r, 0))
    expect(wrapper.exists()).toBe(true)
  })
})
