import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Emergencia from "../../pages/emergencia.vue"

vi.mock('../../composables/useConfig', () => ({
  useConfig: () => ({ API_BASE_URL: 'https://localhost:4443' })
}))

vi.stubGlobal('useHead', vi.fn())
vi.stubGlobal('definePageMeta', vi.fn())
vi.stubGlobal('navigateTo', vi.fn())

import { createRouter, createWebHistory } from 'vue-router'
const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', component: {} }]
})

describe('emergencia.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({})
    }) as any
  })

  it('debería montar correctamente', async () => {
    const wrapper = mount(Emergencia, {
      global: { 
        plugins: [router],
        stubs: { NuxtLink: true }
      }
    })
    await new Promise(r => setTimeout(r, 0))
    expect(wrapper.exists()).toBe(true)
  })
})
