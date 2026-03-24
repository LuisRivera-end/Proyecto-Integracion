import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MobileHeader from "../../../components/admin/MobileHeader.vue"

describe('MobileHeader.vue', () => {
  it('debería renderizar correctamente el título pasado por props (Caso normal)', () => {
    const wrapper = mount(MobileHeader, {
      props: {
        title: 'Mi Título de Prueba'
      }
    })

    expect(wrapper.text()).toContain('Mi Título de Prueba')
  })

  it('debería emitir el evento openSidebar al hacer clic en el botón (Caso normal)', async () => {
    const wrapper = mount(MobileHeader, {
      props: {
        title: 'Panel'
      }
    })

    const button = wrapper.find('#openSidebar')
    await button.trigger('click')

    expect(wrapper.emitted()).toHaveProperty('openSidebar')
    expect(wrapper.emitted().openSidebar).toHaveLength(1)
  })
})
