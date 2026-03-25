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

          <div class="mt-6 text-center">
            <NuxtLink
              to="/emergencia"
              class="text-sm text-slate-500 hover:text-emerald-600 transition-colors duration-200 underline underline-offset-2"
            >
              ¿Problemas para iniciar sesión?
            </NuxtLink>
          </div>
        </div>
      </div>

      <!-- ═══ Modal: Configuración del Administrador ═══ -->
      <div
        v-if="showSetupModal"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      >
        <div class="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-lg border border-slate-200 animate-fadeIn">
          <div class="text-center mb-6">
            <div class="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl mb-3 shadow-lg">
              <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
            <h2 class="text-2xl font-bold text-slate-800 mb-1">Configure su cuenta</h2>
            <p class="text-slate-500 text-sm">Establezca los datos definitivos del administrador.</p>
          </div>

          <form @submit.prevent="handleFinalize" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label for="setup-nombre1" class="block text-xs font-semibold text-slate-600 mb-1">Primer Nombre *</label>
                <input v-model="setup.nombre1" type="text" id="setup-nombre1" required maxlength="20"
                  class="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none transition-all bg-slate-50 text-slate-800 text-sm" />
              </div>
              <div>
                <label for="setup-nombre2" class="block text-xs font-semibold text-slate-600 mb-1">Segundo Nombre</label>
                <input v-model="setup.nombre2" type="text" id="setup-nombre2" maxlength="20"
                  class="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none transition-all bg-slate-50 text-slate-800 text-sm" />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label for="setup-apellido1" class="block text-xs font-semibold text-slate-600 mb-1">Primer Apellido *</label>
                <input v-model="setup.apellido1" type="text" id="setup-apellido1" required maxlength="20"
                  class="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none transition-all bg-slate-50 text-slate-800 text-sm" />
              </div>
              <div>
                <label for="setup-apellido2" class="block text-xs font-semibold text-slate-600 mb-1">Segundo Apellido</label>
                <input v-model="setup.apellido2" type="text" id="setup-apellido2" maxlength="20"
                  class="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none transition-all bg-slate-50 text-slate-800 text-sm" />
              </div>
            </div>

            <div>
              <label for="setup-usuario" class="block text-xs font-semibold text-slate-600 mb-1">Nuevo Usuario *</label>
              <input v-model="setup.usuario" type="text" id="setup-usuario" required maxlength="20" pattern="^[a-zA-Z0-9_.\-]+$"
                class="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none transition-all bg-slate-50 text-slate-800 text-sm"
                placeholder="Solo letras, números, _ . -" />
            </div>

            <div>
              <label for="setup-passwd" class="block text-xs font-semibold text-slate-600 mb-1">Nueva Contraseña *</label>
              <input v-model="setup.passwd" type="password" id="setup-passwd" required minlength="8" maxlength="100"
                class="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none transition-all bg-slate-50 text-slate-800 text-sm"
                placeholder="Mayúscula, minúscula, número y símbolo" />
            </div>

            <div>
              <label for="setup-passwd-confirm" class="block text-xs font-semibold text-slate-600 mb-1">Confirmar Contraseña *</label>
              <input v-model="setup.passwdConfirm" type="password" id="setup-passwd-confirm" required minlength="8" maxlength="100"
                class="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none transition-all bg-slate-50 text-slate-800 text-sm"
                placeholder="Repita la contraseña" />
            </div>

            <div v-if="setupError" class="bg-red-50 border border-red-300 text-red-700 px-3 py-2 rounded-lg text-sm">
              {{ setupError }}
            </div>

            <button
              type="submit"
              :disabled="setupLoading"
              class="w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-semibold py-3 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-50"
            >
              <span v-if="setupLoading" class="flex items-center justify-center gap-2">
                <svg class="animate-spin h-5 w-5 border-b-2 border-white rounded-full" viewBox="0 0 24 24"></svg>
                Guardando...
              </span>
              <span v-else>✅ Guardar y Continuar</span>
            </button>
          </form>
        </div>
      </div>

      <ClientOnly>
        <GTranslateWidget />
      </ClientOnly>
    </div>
</template>

<script setup lang="ts">
/**
 * Página Login
 * Maneja la autenticación de usuarios (Administradores, Jefes de sector y Operadores de ventanilla).
 * Si la autenticación es exitosa, guarda la sesión y redirige a la vista correspondiente.
 * Si el admin es temporal (needs_setup), muestra un modal para configurar los datos reales.
 */
definePageMeta({ layout: 'default' })

useHead({ title: 'Inicio de Sesión' })

const { API_BASE_URL } = useConfig()
const { saveSession, getSessionToken } = useAuth()
const socket = useSocket()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

// ── Setup modal state ──
const showSetupModal = ref(false)
const setupLoading = ref(false)
const setupError = ref('')
const pendingSessionToken = ref('')

interface SetupForm {
  nombre1: string
  nombre2: string
  apellido1: string
  apellido2: string
  usuario: string
  passwd: string
  passwdConfirm: string
}

const setup = reactive<SetupForm>({
  nombre1: '',
  nombre2: '',
  apellido1: '',
  apellido2: '',
  usuario: '',
  passwd: '',
  passwdConfirm: '',
})

/**
 * Muestra un mensaje de error en pantalla durante 5 segundos.
 */
const showError = (message: string): void => {
  errorMsg.value = message
  setTimeout(() => { errorMsg.value = '' }, 5000)
}

// Al llegar al login, limpiar datos locales y verificar si hay admin.
onMounted(async () => {
  const existingToken = getSessionToken()
  if (existingToken) {
    localStorage.removeItem(`session_${existingToken}`)
    sessionStorage.removeItem('session_token')
  }

  // ── Verificar si el sistema necesita setup ──
  try {
    const statusRes = await fetch(`${API_BASE_URL}/api/setup/status`)
    if (statusRes.ok) {
      const statusData = await statusRes.json()
      if (statusData.needs_setup) {
        navigateTo('/setup', { replace: true })
        return
      }
    }
  } catch {
    // Si falla la verificación, continuar con login normal
  }

  // Escuchar eventos WS de sesión en tiempo real
  socket.on('session_already_active', (payload: any) => {
    console.log('🔒 Intento de login bloqueado — sesión ya activa para empleado:', payload?.employee_id)
  })

  socket.on('session_started', (payload: any) => {
    console.log('🟢 Sesión iniciada para empleado:', payload?.employee_id)
  })

  socket.on('session_ended', (payload: any) => {
    console.log('🔓 Sesión cerrada para empleado:', payload?.employee_id)
  })
})

onUnmounted(() => {
  socket.off('session_already_active')
  socket.off('session_started')
  socket.off('session_ended')
})

/**
 * Maneja el envío del formulario de inicio de sesión.
 */
const handleLogin = async (): Promise<void> => {
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
    const currentUser: any = {
      id: data.id,
      username: data.nombre,
      rol: data.rol,
      sector: data.sector,
      id_sector: data.id_sector,
    }

    // ── Admin temporal: mostrar modal de configuración ──
    if (currentUser.rol === 1 && data.needs_setup) {
      pendingSessionToken.value = data.session_token
      showSetupModal.value = true
      loading.value = false
      return
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
  } catch (err: any) {
    console.error('Error en login:', err)
    showError(err.message)
  } finally {
    loading.value = false
  }
}

/**
 * Maneja la finalización de la configuración del administrador.
 */
const handleFinalize = async (): Promise<void> => {
  setupError.value = ''

  // Validaciones locales
  if (!setup.nombre1.trim() || !setup.apellido1.trim() || !setup.usuario.trim() || !setup.passwd.trim()) {
    setupError.value = 'Todos los campos marcados con * son obligatorios.'
    return
  }

  if (setup.passwd !== setup.passwdConfirm) {
    setupError.value = 'Las contraseñas no coinciden.'
    return
  }

  if (setup.passwd.length < 8) {
    setupError.value = 'La contraseña debe tener al menos 8 caracteres.'
    return
  }

  // Validación de contraseña segura
  const missingRules: string[] = []
  if (!/[A-Z]/.test(setup.passwd)) missingRules.push('una letra mayúscula')
  if (!/[a-z]/.test(setup.passwd)) missingRules.push('una letra minúscula')
  if (!/[0-9]/.test(setup.passwd)) missingRules.push('un número')
  if (!/[^A-Za-z0-9]/.test(setup.passwd)) missingRules.push('un símbolo (ej. @, #, $, !)')

  if (missingRules.length > 0) {
    setupError.value = `La contraseña debe contener al menos: ${missingRules.join(', ')}.`
    return
  }

  setupLoading.value = true

  try {
    const res = await fetch(`${API_BASE_URL}/api/setup/finalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_token: pendingSessionToken.value,
        nombre1: setup.nombre1.trim(),
        nombre2: setup.nombre2.trim(),
        apellido1: setup.apellido1.trim(),
        apellido2: setup.apellido2.trim(),
        usuario: setup.usuario.trim(),
        passwd: setup.passwd,
      }),
    })

    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'Error al guardar la configuración')
    }

    // Guardar sesión con datos actualizados
    const currentUser: any = {
      id: 0, // Se recargará al redirigir
      username: `${setup.nombre1.trim()} ${setup.apellido1.trim()}`,
      rol: 1,
      sector: 'Admin',
      id_sector: null,
    }
    saveSession(currentUser, pendingSessionToken.value)
    showSetupModal.value = false
    navigateTo('/admin', { replace: true })
  } catch (err: any) {
    setupError.value = err.message
  } finally {
    setupLoading.value = false
  }
}
</script>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
