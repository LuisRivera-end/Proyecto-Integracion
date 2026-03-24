<template>
  <div class="p-6 md:p-10 lg:p-14 max-w-7xl mx-auto w-full flex flex-col gap-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-white tracking-tight drop-shadow-sm">Dashboard</h1>
        <p class="text-white/70 mt-1 font-medium">Vista general del sistema de turnos</p>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-white/60 text-sm font-medium">{{ fechaActual }}</span>
        <button @click="fetchStats" :disabled="loading" 
          class="px-4 py-2 bg-white/10 hover:bg-white/20 text-white font-bold text-sm rounded-xl transition-all flex items-center gap-2 disabled:opacity-50">
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Actualizar
        </button>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Tickets en Cola -->
      <div class="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg border border-white/60 p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">En cola</span>
        </div>
        <p class="text-3xl font-bold text-slate-800">{{ stats?.tickets_en_cola ?? '-' }}</p>
        <p class="text-sm text-slate-500 mt-1">Tickets esperando</p>
      </div>

      <!-- Atendiendo -->
      <div class="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg border border-white/60 p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Atendiendo</span>
        </div>
        <p class="text-3xl font-bold text-slate-800">{{ stats?.tickets_atendiendo ?? '-' }}</p>
        <p class="text-sm text-slate-500 mt-1">En servicio</p>
      </div>

      <!-- Completados Hoy -->
      <div class="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg border border-white/60 p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Hoy</span>
        </div>
        <p class="text-3xl font-bold text-slate-800">{{ stats?.tickets_completados_hoy ?? '-' }}</p>
        <p class="text-sm text-slate-500 mt-1">Completados</p>
      </div>

      <!-- Empleados Activos -->
      <div class="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg border border-white/60 p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
            <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.874 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Activos</span>
        </div>
        <p class="text-3xl font-bold text-slate-800">{{ stats?.empleados_activos ?? '-' }}</p>
        <p class="text-sm text-slate-500 mt-1">En ventanilla: {{ stats?.empleados_en_ventanilla ?? '-' }}</p>
      </div>
    </div>

    <!-- Stats adicionales -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Tiempo promedio -->
      <div class="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg border border-white/60 p-6">
        <h3 class="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Tiempo Promedio de Espera
        </h3>
        <div class="flex items-baseline gap-2">
          <p class="text-4xl font-bold text-slate-800">
            {{ stats?.tiempo_espera_promedio_segundos ? formatTime(stats.tiempo_espera_promedio_segundos) : '-' }}
          </p>
          <span v-if="stats?.tiempo_espera_promedio_segundos" class="text-slate-400 text-sm">(promedio hoy)</span>
        </div>
      </div>

      <!-- Resumen rápido -->
      <div class="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg border border-white/60 p-6">
        <h3 class="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Resumen del Día
        </h3>
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-slate-50 rounded-xl p-4">
            <p class="text-sm text-slate-500 font-medium">Total procesados</p>
            <p class="text-2xl font-bold text-slate-800 mt-1">{{ totalProcesados }}</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-4">
            <p class="text-sm text-slate-500 font-medium">Eficiencia</p>
            <p class="text-2xl font-bold mt-1" :class="eficienciaColor">{{ eficiencia }}%</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Por Sector Table -->
    <div class="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg border border-white/60">
      <div class="p-6 border-b border-slate-100">
        <h3 class="text-lg font-bold text-slate-800 flex items-center gap-2">
          <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          Tickets por Departamento
        </h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm text-left">
          <thead class="bg-slate-50 border-b border-slate-200">
            <tr>
              <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs">Departamento</th>
              <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs text-center">En Cola</th>
              <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs text-center">Ventanillas Activas</th>
              <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs text-center">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="!stats?.por_sector?.length">
              <td colspan="4" class="px-6 py-8 text-center text-slate-400 text-sm font-medium">Sin datos disponibles</td>
            </tr>
            <tr v-for="sector in stats?.por_sector" :key="sector.id_sector" class="hover:bg-slate-50 transition-colors">
              <td class="px-6 py-4 font-medium text-slate-800">{{ sector.nombre }}</td>
              <td class="px-6 py-4 text-center">
                <span :class="[
                  'inline-flex items-center justify-center min-w-[2rem] px-3 py-1 rounded-full text-sm font-bold',
                  sector.tickets_en_cola > 5 ? 'bg-red-100 text-red-700' : 
                  sector.tickets_en_cola > 0 ? 'bg-amber-100 text-amber-700' : 
                  'bg-emerald-100 text-emerald-700'
                ]">
                  {{ sector.tickets_en_cola }}
                </span>
              </td>
              <td class="px-6 py-4 text-center font-medium text-slate-600">{{ sector.ventanillas_activas }}</td>
              <td class="px-6 py-4 text-center">
                <span :class="[
                  'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold',
                  sector.tickets_en_cola === 0 ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' :
                  sector.tickets_en_cola > 5 ? 'bg-red-100 text-red-700 border border-red-200' :
                  'bg-amber-100 text-amber-700 border border-amber-200'
                ]">
                  <span :class="['w-1.5 h-1.5 rounded-full', 
                    sector.tickets_en_cola === 0 ? 'bg-emerald-500' :
                    sector.tickets_en_cola > 5 ? 'bg-red-500' : 'bg-amber-500']"></span>
                  {{ sector.tickets_en_cola === 0 ? 'Sin cola' : sector.tickets_en_cola > 5 ? 'Demora alta' : 'Normal' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Connection status -->
    <div class="fixed bottom-4 right-4 flex items-center gap-2 px-3 py-2 rounded-full text-xs font-bold transition-all"
      :class="socketConnected ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' : 'bg-red-100 text-red-700 border border-red-200'">
      <span :class="['w-2 h-2 rounded-full', socketConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500']"></span>
      {{ socketConnected ? 'Tiempo real' : 'Sin conexión' }}
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Página Dashboard
 * Muestra el panel principal de control para administradores.
 * Proporciona estadísticas en tiempo real y resumen de tickets.
 */
definePageMeta({ layout: 'admin', middleware: 'auth' })
useHead({ title: 'Dashboard — TurnosUal' })

const { API_BASE_URL } = useConfig()
const { lanzarAlerta } = useToast()
const socket = useSocket()
const { getSessionToken } = useAuth()
const { startGuard, stopGuard } = useSessionGuard()

const stats = ref<any>(null)
const loading = ref(false)
const socketConnected = ref(false)

const fechaActual = computed(() => {
  const now = new Date()
  return now.toLocaleDateString('es-MX', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
})

const totalProcesados = computed(() => {
  if (!stats.value) return '-'
  return (stats.value.tickets_completados_hoy || 0) + (stats.value.tickets_atendiendo || 0)
})

const eficiencia = computed(() => {
  if (!stats.value) return 0
  const completados = stats.value.tickets_completados_hoy || 0
  const enCola = stats.value.tickets_en_cola || 0
  const total = completados + enCola
  if (total === 0) return 100
  return Math.round((completados / total) * 100)
})

const eficienciaColor = computed(() => {
  const e = eficiencia.value
  if (e >= 80) return 'text-emerald-600'
  if (e >= 50) return 'text-amber-600'
  return 'text-red-600'
})

/**
 * Formatea una cantidad de segundos en minutos y segundos.
 * 
 * @param {number} seconds - La cantidad total de segundos.
 * @returns {string} La cadena de tiempo formateada (ej. '5m 30s').
 */
function formatTime(seconds: number): string {
  if (!seconds) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  if (mins === 0) return `${secs}s`
  return `${mins}m ${secs}s`
}

/**
 * Recupera las estadísticas actuales del backend y actualiza el estado.
 * 
 * @returns {Promise<void>}
 */
async function fetchStats(): Promise<void> {
  const token = getSessionToken()
  if (!token) return
  
  loading.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/api/dashboard/stats?session_token=${encodeURIComponent(token)}`)
    if (!res.ok) {
      const e = await res.json()
      throw new Error(e.detail || e.error || 'Error al cargar estadísticas')
    }
    stats.value = await res.json()
  } catch (err: any) {
    console.error('Error fetching dashboard stats:', err)
    lanzarAlerta(err.message || 'Error al cargar estadísticas', 'error')
  } finally {
    loading.value = false
  }
}

let onConnect: () => void
let onDisconnect: () => void
let onTicketsUpdate: () => void
let onVentanillaStatus: () => void

onMounted(() => {
  fetchStats()
  startGuard()

  onConnect = () => {
    socketConnected.value = true
    fetchStats()
  }
  onDisconnect = () => {
    socketConnected.value = false
  }
  onTicketsUpdate = () => {
    fetchStats()
  }
  onVentanillaStatus = () => {
    fetchStats()
  }

  socket.on('connect', onConnect)
  socket.on('disconnect', onDisconnect)
  socket.on('tickets_updated', onTicketsUpdate)
  socket.on('ventanilla_status_changed', onVentanillaStatus)
  socket.on('session_started', onTicketsUpdate)
  socket.on('session_ended', onTicketsUpdate)

  socketConnected.value = socket.connected
})

onUnmounted(() => {
  stopGuard()
  socket.off('connect', onConnect)
  socket.off('disconnect', onDisconnect)
  socket.off('tickets_updated', onTicketsUpdate)
  socket.off('ventanilla_status_changed', onVentanillaStatus)
  socket.off('session_started', onTicketsUpdate)
  socket.off('session_ended', onTicketsUpdate)
})
</script>
