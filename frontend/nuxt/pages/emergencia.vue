<template>
  <div class="bg-gradient-to-br from-slate-600 via-slate-500 to-emerald-300 min-h-screen">
    <NuxtLink
      to="/login"
      id="back-to-login"
      class="fixed top-6 right-6 bg-slate-600 hover:bg-slate-700 text-white p-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 z-50"
      title="Regresar al Login"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </NuxtLink>

    <div class="min-h-screen flex items-center justify-center p-4">
      <!-- ═══ Vista 1: Ingresar PIN ═══ -->
      <div
        v-if="!authenticated"
        class="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-10 w-full max-w-md border border-slate-200"
      >
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-amber-500 to-red-500 rounded-2xl mb-4 shadow-lg">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-slate-800 mb-2">Acceso de Emergencia</h1>
          <p class="text-slate-500 text-sm">Ingresa el PIN de seguridad para continuar</p>
        </div>

        <form @submit.prevent="handlePinSubmit" class="space-y-6">
          <div>
            <label for="pin-input" class="block text-sm font-semibold text-slate-700 mb-2">PIN de Seguridad</label>
            <input
              v-model="pin"
              type="password"
              id="pin-input"
              required
              maxlength="10"
              placeholder="Ingresa el PIN"
              class="w-full px-4 py-3.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all bg-slate-50 text-slate-800 placeholder:text-slate-400 text-center tracking-[0.5em] text-lg font-mono"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-gradient-to-r from-amber-500 to-red-500 hover:from-amber-600 hover:to-red-600 text-white font-semibold py-3.5 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            v-html="loading ? '<svg class=\'animate-spin h-5 w-5 mr-2 border-b-2 border-white rounded-full inline-block\' viewBox=\'0 0 24 24\'></svg> Validando...' : 'Verificar PIN'"
          ></button>
        </form>

        <div
          v-if="errorMsg"
          class="mt-4 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-xl text-sm"
        >
          {{ errorMsg }}
        </div>

        <div class="mt-6 text-center">
          <NuxtLink
            to="/login"
            class="text-sm text-slate-500 hover:text-slate-700 transition-colors duration-200"
          >
            ← Volver al inicio de sesión
          </NuxtLink>
        </div>
      </div>

      <!-- ═══ Vista 2: Panel de Emergencia ═══ -->
      <div
        v-else
        class="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-10 w-full max-w-lg border border-slate-200"
      >
        <div class="text-center mb-6">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-amber-500 to-red-500 rounded-2xl mb-4 shadow-lg">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-slate-800">Herramienta de Emergencia</h1>
          <p v-if="countdown > 0" class="text-xs text-slate-400 mt-1 font-mono">Sesión de emergencia expira en {{ formattedCountdown }}</p>
        </div>

        <!-- Warning Banner -->
        <div class="bg-amber-50 border-l-4 border-amber-500 rounded-xl p-5 mb-8">
          <div class="flex items-start gap-3">
            <span class="text-2xl flex-shrink-0">⚠️</span>
            <div>
              <h3 class="font-bold text-amber-800 mb-2">Advertencia – Herramienta de emergencia</h3>
              <p class="text-amber-700 text-sm leading-relaxed">
                Esta función está diseñada únicamente para <strong>situaciones de emergencia</strong>
                cuando los usuarios no pueden iniciar sesión debido a bloqueos de sesión.
              </p>
              <p class="text-amber-700 text-sm leading-relaxed mt-2">
                Al presionar <strong>"Reiniciar sesiones del sistema"</strong> se
                <strong>cerrarán inmediatamente todas las sesiones activas</strong>,
                lo que obligará a <strong>todos los usuarios a iniciar sesión nuevamente</strong>.
              </p>
              <p class="text-amber-700 text-sm font-semibold mt-2">
                Utilice esta herramienta solo cuando sea estrictamente necesario.
              </p>
            </div>
          </div>
        </div>

        <!-- Reset Button -->
        <button
          @click="handleResetSessions"
          :disabled="resetting || resetDone"
          class="w-full font-semibold py-4 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 text-lg"
          :class="resetDone
            ? 'bg-emerald-500 text-white cursor-default'
            : 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white'"
          v-html="resetting
            ? '<svg class=\'animate-spin h-5 w-5 mr-2 border-b-2 border-white rounded-full inline-block\' viewBox=\'0 0 24 24\'></svg> Reiniciando sesiones...'
            : resetDone
              ? '✓ Sesiones reiniciadas exitosamente'
              : '🔄 Reiniciar sesiones del sistema'"
        ></button>

        <div
          v-if="resetError"
          class="mt-4 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-xl text-sm"
        >
          {{ resetError }}
        </div>

        <div
          v-if="resetDone"
          class="mt-4 bg-emerald-50 border border-emerald-300 text-emerald-700 px-4 py-3 rounded-xl text-sm"
        >
          Todas las sesiones han sido cerradas. Los usuarios deberán iniciar sesión nuevamente.
        </div>

        <div class="mt-6 text-center">
          <NuxtLink
            to="/login"
            class="text-sm text-slate-500 hover:text-slate-700 transition-colors duration-200"
          >
            ← Volver al inicio de sesión
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

useHead({ title: 'Acceso de Emergencia' })

const { API_BASE_URL } = useConfig()

// ── Estado: Vista PIN ──
const pin = ref('')
const loading = ref(false)
const errorMsg = ref('')
const authenticated = ref(false)
const emergencyToken = ref('')

// ── Estado: Vista Panel ──
const resetting = ref(false)
const resetDone = ref(false)
const resetError = ref('')

// ── Countdown (5 minutos) ──
const countdown = ref(0)
let countdownInterval = null

const formattedCountdown = computed(() => {
  const m = Math.floor(countdown.value / 60)
  const s = countdown.value % 60
  return `${m}:${s.toString().padStart(2, '0')}`
})

/**
 * Inicia el temporizador de la sesión de emergencia.
 * @returns {void}
 */
const startCountdown = (): void => {
  countdown.value = 300 // 5 minutos
  countdownInterval = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownInterval)
      navigateTo('/login', { replace: true })
    }
  }, 1000)
}

onUnmounted(() => {
  if (countdownInterval) clearInterval(countdownInterval)
})

/**
 * Muestra un mensaje de error.
 * @param {string} message - El mensaje a mostrar.
 * @returns {void}
 */
const showError = (message: string): void => {
  errorMsg.value = message
  setTimeout(() => { errorMsg.value = '' }, 5000)
}

/**
 * Maneja el envío del PIN de seguridad.
 * @returns {Promise<void>}
 */
const handlePinSubmit = async (): Promise<void> => {
  loading.value = true
  errorMsg.value = ''

  try {
    const res = await fetch(`${API_BASE_URL}/api/emergency/validate-pin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin: pin.value.trim() }),
    })

    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || 'PIN incorrecto')
    }

    const data = await res.json()
    emergencyToken.value = data.emergency_token
    authenticated.value = true
    startCountdown()
  } catch (err) {
    showError(err.message)
  } finally {
    loading.value = false
  }
}

/**
 * Reinicia todas las sesiones del sistema.
 * @returns {Promise<void>}
 */
const handleResetSessions = async (): Promise<void> => {
  resetting.value = true
  resetError.value = ''
 
  try {
    const res = await fetch(`${API_BASE_URL}/api/emergency/reset-sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ emergency_token: emergencyToken.value }),
    })

    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || 'Error al reiniciar sesiones')
    }

    resetDone.value = true
    // Redirigir al login después de 3 segundos
    setTimeout(() => {
      navigateTo('/login', { replace: true })
    }, 3000)
  } catch (err) {
    resetError.value = err.message
  } finally {
    resetting.value = false
  }
}
</script>
