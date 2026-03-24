<template>
    <div class="bg-gradient-to-br from-slate-600 via-slate-500 to-emerald-300 min-h-screen">
      <div class="min-h-screen flex items-center justify-center p-4">
        <div class="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-10 w-full max-w-lg border border-slate-200">

          <!-- Loading state -->
          <div v-if="checking" class="text-center py-8">
            <svg class="animate-spin h-8 w-8 mx-auto mb-4 text-slate-500" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            <p class="text-slate-600">Verificando estado del sistema...</p>
          </div>

          <!-- Setup form: generate credentials -->
          <div v-else-if="!credentials">
            <div class="text-center mb-8">
              <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl mb-4 shadow-lg">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h1 class="text-3xl font-bold text-slate-800 mb-2">Configuración Inicial</h1>
              <p class="text-slate-600">El sistema necesita un administrador para funcionar.</p>
              <p class="text-slate-500 text-sm mt-2">
                Se generarán credenciales temporales que deberá anotar. Al iniciar sesión, se le pedirá configurar sus datos reales.
              </p>
            </div>

            <button
              @click="generateCredentials"
              :disabled="generating"
              id="generate-credentials-btn"
              class="w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-semibold py-3.5 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="generating" class="flex items-center justify-center gap-2">
                <svg class="animate-spin h-5 w-5 border-b-2 border-white rounded-full" viewBox="0 0 24 24"></svg>
                Generando...
              </span>
              <span v-else>🔑 Generar Credenciales de Administrador</span>
            </button>

            <div v-if="errorMsg" class="mt-4 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-xl text-sm">
              {{ errorMsg }}
            </div>
          </div>

          <!-- Credentials display -->
          <div v-else>
            <div class="text-center mb-6">
              <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl mb-4 shadow-lg">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 class="text-2xl font-bold text-slate-800 mb-2">¡Administrador Creado!</h2>
              <p class="text-slate-600 text-sm">Anote estas credenciales. <strong>No se mostrarán de nuevo.</strong></p>
            </div>

            <div class="bg-slate-50 border-2 border-dashed border-slate-300 rounded-2xl p-6 mb-6 space-y-4">
              <div>
                <label class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Usuario</label>
                <div class="flex items-center gap-2 mt-1">
                  <code id="generated-username" class="flex-1 bg-white px-4 py-2.5 rounded-lg border border-slate-200 text-slate-800 font-mono text-lg select-all">
                    {{ credentials.usuario }}
                  </code>
                  <button @click="copy(credentials.usuario)" class="p-2 text-slate-500 hover:text-emerald-600 transition-colors" title="Copiar">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
              </div>
              <div>
                <label class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Contraseña</label>
                <div class="flex items-center gap-2 mt-1">
                  <code id="generated-password" class="flex-1 bg-white px-4 py-2.5 rounded-lg border border-slate-200 text-slate-800 font-mono text-lg select-all">
                    {{ credentials.password }}
                  </code>
                  <button @click="copy(credentials.password)" class="p-2 text-slate-500 hover:text-emerald-600 transition-colors" title="Copiar">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <div class="bg-amber-50 border border-amber-300 text-amber-800 px-4 py-3 rounded-xl text-sm mb-6">
              ⚠️ Estas credenciales son <strong>temporales</strong>. Al iniciar sesión deberá configurar sus datos definitivos.
            </div>

            <NuxtLink
              to="/login"
              id="go-to-login-btn"
              class="block w-full text-center bg-gradient-to-r from-slate-600 to-emerald-600 hover:from-slate-700 hover:to-emerald-700 text-white font-semibold py-3.5 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Ir al Inicio de Sesión →
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
</template>

<script setup lang="ts">
/**
 * Página de Configuración Inicial (/setup)
 * Genera credenciales temporales para el primer administrador.
 * Solo es accesible cuando no existe ningún administrador en la BD.
 */
definePageMeta({ layout: 'default' })

useHead({ title: 'Configuración Inicial' })

const { API_BASE_URL } = useConfig()

const checking = ref(true)
const generating = ref(false)
const errorMsg = ref('')
const credentials = ref<{ usuario: string; password: string } | null>(null)

/**
 * Copia texto al portapapeles.
 */
const copy = async (text: string): Promise<void> => {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    // Fallback silencioso
  }
}

/**
 * Verifica el estado del sistema. Si ya hay admin, redirige al login.
 */
onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/setup/status`)
    if (!res.ok) throw new Error('Error al verificar estado')
    const data = await res.json()

    if (!data.needs_setup) {
      navigateTo('/login', { replace: true })
      return
    }
  } catch (err: any) {
    errorMsg.value = 'Error al conectar con el servidor.'
  } finally {
    checking.value = false
  }
})

/**
 * Genera las credenciales temporales del administrador.
 */
const generateCredentials = async (): Promise<void> => {
  generating.value = true
  errorMsg.value = ''

  try {
    const res = await fetch(`${API_BASE_URL}/api/setup/init`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })

    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'Error al generar credenciales')
    }

    const data = await res.json()
    credentials.value = { usuario: data.usuario, password: data.password }
  } catch (err: any) {
    errorMsg.value = err.message
  } finally {
    generating.value = false
  }
}
</script>
