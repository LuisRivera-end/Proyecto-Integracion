<template>
    <LoadingOverlay />

    <div class="bg-gradient-to-br from-slate-600 via-slate-500 to-emerald-300 min-h-screen">
      <NuxtLink
        to="/"
        id="back-Button"
        class="fixed top-6 right-6 bg-slate-600 hover:bg-slate-700 text-white p-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 z-50"
        title="Regresar a Generación de Tickets"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </NuxtLink>

      <div id="login-screen" class="min-h-screen flex items-center justify-center p-4">
        <div class="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-10 w-full max-w-md border border-slate-200">
          <div class="text-center mb-10">
            <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-slate-600 to-emerald-600 rounded-2xl mb-4 shadow-lg">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h1 class="text-3xl font-bold text-slate-800 mb-2">Inicio de Sesión</h1>
            <p class="text-slate-600">Ingresa tus credenciales</p>
          </div>

          <form @submit.prevent="handleLogin" class="space-y-6">
            <div>
              <label for="username" class="block text-sm font-semibold text-slate-700 mb-2">Usuario</label>
              <input
                v-model="username"
                type="text"
                id="username"
                required
                placeholder="Ingresa tu usuario"
                class="w-full px-4 py-3.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-slate-500 focus:border-slate-500 outline-none transition-all bg-slate-50 text-slate-800 placeholder:text-slate-400"
              />
            </div>

            <div>
              <label for="password" class="block text-sm font-semibold text-slate-700 mb-2">Contraseña</label>
              <input
                v-model="password"
                type="password"
                id="password"
                required
                placeholder="Ingresa tu contraseña"
                class="w-full px-4 py-3.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-slate-500 focus:border-slate-500 outline-none transition-all bg-slate-50 text-slate-800 placeholder:text-slate-400"
              />
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full bg-gradient-to-r from-slate-600 to-emerald-600 hover:from-slate-700 hover:to-emerald-700 text-white font-semibold py-3.5 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              v-html="loading ? '<svg class=\'animate-spin h-5 w-5 mr-2 border-b-2 border-white rounded-full inline-block\' viewBox=\'0 0 24 24\'></svg> Iniciando sesión...' : 'Iniciar Sesión'"
            ></button>
          </form>

          <div
            v-if="errorMsg"
            class="mt-4 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-xl text-sm"
          >
            {{ errorMsg }}
          </div>
        </div>
      </div>

      <ClientOnly>
        <GTranslateWidget />
      </ClientOnly>
    </div>
</template>

<script setup>
definePageMeta({ layout: 'default' })

useHead({ title: 'Inicio de Sesión' })

const { API_BASE_URL } = useConfig()
const { saveSession, getSessionToken } = useAuth()
const socket = useSocket()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

const showError = (message) => {
  errorMsg.value = message
  setTimeout(() => { errorMsg.value = '' }, 5000)
}

// Al llegar al login, limpiar solo los datos locales de esta pestaña.
// NO llamar al backend logout porque eso emite session_unlocked
// y puede interferir con otras sesiones.
onMounted(() => {
  const existingToken = getSessionToken()
  if (existingToken) {
    // Solo limpiar datos locales de este tab, sin tocar el backend
    localStorage.removeItem(`session_${existingToken}`)
    sessionStorage.removeItem('session_token')
  }

  socket.on('session_locked', (payload) => {
    console.log('🔒 Sesión bloqueada para empleado:', payload?.employee_id)
  })

  socket.on('session_unlocked', (payload) => {
    console.log('🔓 Sesión liberada para empleado:', payload?.employee_id)
  })
})

onUnmounted(() => {
  socket.off('session_locked')
  socket.off('session_unlocked')
})

const handleLogin = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    const res = await fetch(`${API_BASE_URL}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value.trim(), password: password.value.trim() }),
    })

    if (!res.ok) {
      const errorData = await res.json()
      throw new Error(errorData.detail || errorData.error || 'Credenciales incorrectas')
    }

    const data = await res.json()
    const currentUser = {
      id: data.id,
      username: data.nombre,
      rol: data.rol,
      sector: data.sector,
    }

    if (currentUser.rol === 1) {
      saveSession(currentUser, data.session_token)
      navigateTo('/admin', { replace: true })
      return
    }

    if (currentUser.rol === 6) {
      saveSession(currentUser, data.session_token)
      navigateTo('/subjefes', { replace: true })
      return
    }

    // Check ventanilla for operators
    const ventanillaRes = await fetch(`${API_BASE_URL}/api/empleado/${currentUser.id}/ventanilla-activa`)
    if (!ventanillaRes.ok) {
      throw new Error('Error al verificar ventanilla del empleado')
    }

    const ventanillaActiva = await ventanillaRes.json()
    if (ventanillaActiva && ventanillaActiva.ID_Ventanilla) {
      currentUser.ventanilla = {
        id: ventanillaActiva.ID_Ventanilla,
        nombre: ventanillaActiva.Ventanilla,
      }
      saveSession(currentUser, data.session_token)
      navigateTo('/ventanilla', { replace: true })
      return
    }

    showError('No tienes una ventanilla asignada. Contacta al administrador.')
  } catch (err) {
    console.error('Error en login:', err)
    showError(err.message)
  } finally {
    loading.value = false
  }
}
</script>
