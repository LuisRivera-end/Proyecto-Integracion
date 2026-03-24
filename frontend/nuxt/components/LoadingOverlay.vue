<template>
  <div
    v-if="visible"
    id="loading-overlay"
    class="fixed inset-0 z-[9999] flex flex-col items-center justify-center gap-6 transition-opacity duration-500"
    :style="{ background: background }"
  >
    <div
      class="w-14 h-14 border-4 border-white/25 border-t-white rounded-full animate-spin"
    ></div>
    <p class="text-white text-lg font-semibold tracking-wide">
      Conectando con el servidor…
    </p>
  </div>
</template>

<script setup lang="ts">
/**
 * Componente LoadingOverlay
 * Muestra una pantalla de carga mientras intenta conectarse con el servidor backend.
 * Desaparece automáticamente cuando la conexión es exitosa.
 */

const props = defineProps({
  /** Color o degradado de fondo de la superposición */
  background: {
    type: String,
    default: 'linear-gradient(135deg, #475569, #64748b, #6ee7b7)',
  },
})

const visible = ref(true)

const { API_BASE_URL } = useConfig()

/**
 * Función que verifica periódicamente si el backend está en línea.
 * Realiza peticiones a una ruta ligera de la API y oculta el overlay si responde correctamente.
 * 
 * @returns {Promise<void>}
 */
const checkBackend = async (): Promise<void> => {
  while (visible.value) {
    try {
      const res = await fetch(`${API_BASE_URL}/api/sectores`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      })
      if (res.ok) {
        visible.value = false
        return
      }
    } catch {
      // El backend no está disponible, se reintenta
    }
    // Esperar 2 segundos antes del siguiente reintento
    await new Promise((r) => setTimeout(r, 2000))
  }
}

onMounted(() => {
  checkBackend()
})
</script>
