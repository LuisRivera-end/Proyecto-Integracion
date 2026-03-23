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

<script setup>
const props = defineProps({
  background: {
    type: String,
    default: 'linear-gradient(135deg, #475569, #64748b, #6ee7b7)',
  },
})

const visible = ref(true)

const { API_BASE_URL } = useConfig()

const checkBackend = async () => {
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
      // Backend not available, retry
    }
    await new Promise((r) => setTimeout(r, 2000))
  }
}

onMounted(() => {
  checkBackend()
})
</script>
