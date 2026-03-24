import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Login from "../../pages/login.vue"
import * as authComposable from "../../composables/useAuth"

// Mocking composables and components
vi.mock('../../composables/useConfig', () => ({
  useConfig: () => ({ API_BASE_URL: 'https://localhost:4443' })
}))

vi.mock('../../composables/useAuth', () => ({
  useAuth: () => ({
    saveSession: vi.fn(),
    getSessionToken: vi.fn()
  })
}))

vi.mock('../../composables/useSocket', () => ({
  useSocket: () => ({
    on: vi.fn(),
    off: vi.fn()
  })
}))

vi.stubGlobal('useHead', vi.fn())
vi.stubGlobal('definePageMeta', vi.fn())
vi.stubGlobal('navigateTo', vi.fn())

const LoadingOverlayMock = { template: '<div></div>' }
const ClientOnlyMock = { template: '<div><slot /></div>' }
const GTranslateWidgetMock = { template: '<div></div>' }
const NuxtLinkMock = { template: '<a><slot /></a>', props: ['to'] }

describe('login.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn() as any
  })

  it('debería renderizar los campos de usuario y contraseña (Caso normal)', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          LoadingOverlay: LoadingOverlayMock,
          ClientOnly: ClientOnlyMock,
          GTranslateWidget: GTranslateWidgetMock,
          NuxtLink: NuxtLinkMock
        }
      }
    })

    expect(wrapper.find('input#username').exists()).toBe(true)
    expect(wrapper.find('input#password').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').text()).toContain('Iniciar Sesión')
  })

  it('debería mostrar un error si la API retorna fallo al hacer submit (Caso de error)', async () => {
    ;(global.fetch as any).mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: 'Credenciales inválidas' })
    })

    const wrapper = mount(Login, {
      global: {
        stubs: {
          LoadingOverlay: LoadingOverlayMock,
          ClientOnly: ClientOnlyMock,
          GTranslateWidget: GTranslateWidgetMock,
          NuxtLink: NuxtLinkMock
        }
      }
    })

    await wrapper.find('input#username').setValue('admin')
    await wrapper.find('input#password').setValue('badpassword')
    await wrapper.find('form').trigger('submit.prevent')

    // Esperamos que se resuelva el fetch
    await new Promise(r => setTimeout(r, 0))

    expect(wrapper.text()).toContain('Credenciales inválidas')
  })
})
