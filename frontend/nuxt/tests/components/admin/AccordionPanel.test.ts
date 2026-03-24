import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AccordionPanel from "../../../components/admin/AccordionPanel.vue"

describe('AccordionPanel.vue', () => {
  it('debería renderizar el título correctamente (Caso normal)', () => {
    const wrapper = mount(AccordionPanel, {
      props: {
        id: 'test-1',
        title: 'Configuraciones'
      }
    })

    expect(wrapper.text()).toContain('Configuraciones')
  })

  it('debería iniciar cerrado por defecto y abrirse al hacer clic (Caso normal)', async () => {
    const wrapper = mount(AccordionPanel, {
      props: {
        id: 'test-2',
        title: 'Avanzado'
      }
    })

    // El componente expone isOpen (por defecto false)
    expect(wrapper.vm.isOpen).toBe(false)

    const button = wrapper.find('.accordion-header')
    await button.trigger('click')

    expect(wrapper.vm.isOpen).toBe(true)
  })

  it('debería respetar la prop defaultOpen (Caso normal)', () => {
    const wrapper = mount(AccordionPanel, {
      props: {
        id: 'test-3',
        title: 'General',
        defaultOpen: true
      }
    })

    expect(wrapper.vm.isOpen).toBe(true)
  })

  it('debería exponer los métodos open y close (Caso límite)', () => {
    const wrapper = mount(AccordionPanel, {
      props: {
        id: 'test-4',
        title: 'Test'
      }
    })

    expect(wrapper.vm.isOpen).toBe(false)
    
    wrapper.vm.open()
    expect(wrapper.vm.isOpen).toBe(true)

    wrapper.vm.close()
    expect(wrapper.vm.isOpen).toBe(false)
  })
})
