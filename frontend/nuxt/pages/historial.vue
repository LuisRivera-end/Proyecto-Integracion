<template>
  <div class="p-6 md:p-10 lg:p-14 max-w-7xl mx-auto w-full flex flex-col gap-8">

    <!-- Header / Summary Card -->
    <div
      class="bg-white/95 backdrop-blur-sm rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-8 border border-white/60 relative overflow-hidden">
      <div class="relative z-10 flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
          <h1 class="text-3xl font-bold text-slate-800 tracking-tight">Resumen de Tickets</h1>
          <p class="text-slate-500 mt-1 font-medium">{{ fechaActual }}</p>
        </div>
        <div class="flex gap-3">
          <button @click="abrirModalReporte"
            class="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white px-5 py-2.5 rounded-xl font-bold shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 hover:-translate-y-0.5 active:translate-y-0 active:scale-95 transition-all duration-200"
            title="Generar Reporte PDF Semanal">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Reporte PDF</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Total Today -->
      <div
        class="bg-white/90 backdrop-blur rounded-2xl p-6 shadow-sm border border-slate-100 flex flex-col items-center justify-center md:col-span-4 lg:col-span-1 lg:row-span-2">
        <p class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">Tickets Hoy</p>
        <p class="text-6xl font-black text-slate-800 tracking-tighter">{{ totalTicketsHoy }}</p>
      </div>

      <!-- Status Cards -->
      <div
        class="bg-white/80 rounded-2xl p-5 shadow-sm border border-slate-100 text-center hover:bg-white transition-colors">
        <p class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Agregados</p>
        <p class="text-3xl font-bold text-slate-800">{{ resumen.total }}</p>
      </div>
      <div
        class="bg-white/80 rounded-2xl p-5 shadow-sm border border-slate-100 text-center hover:bg-white transition-colors">
        <p class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Completados</p>
        <p class="text-3xl font-bold text-emerald-500">{{ resumen.completados }}</p>
      </div>
      <div
        class="bg-white/80 rounded-2xl p-5 shadow-sm border border-slate-100 text-center hover:bg-white transition-colors">
        <p class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Atendiendo</p>
        <p class="text-3xl font-bold text-blue-500">{{ resumen.atendiendo }}</p>
      </div>
      <div
        class="bg-white/80 rounded-2xl p-5 shadow-sm border border-slate-100 text-center hover:bg-white transition-colors">
        <p class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Cancelados</p>
        <p class="text-3xl font-bold text-rose-500">{{ resumen.cancelados }}</p>
      </div>
      <div
        class="bg-white/80 rounded-2xl p-5 shadow-sm border border-slate-100 text-center hover:bg-white transition-colors">
        <p class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Pendientes</p>
        <p class="text-3xl font-bold text-amber-500">{{ resumen.pendientes }}</p>
      </div>
    </div>

    <!-- History List (Refined Layout) -->
    <div class="bg-white/95 backdrop-blur-sm rounded-3xl shadow-lg border border-white/60 p-6 md:p-8">

      <!-- Section Header & Filters Container -->
      <div class="flex flex-col xl:flex-row justify-between items-start xl:items-end gap-6 mb-8">

        <!-- Title & Subtitle -->
        <div class="shrink-0">
          <h2 class="text-2xl font-bold text-slate-800 tracking-tight">Historial Detallado</h2>
          <p class="text-slate-500 text-sm mt-1 font-medium">Busca y filtra entre todos los tickets históricos</p>
        </div>

        <!-- Filters Bar -->
        <div class="flex flex-col md:flex-row flex-wrap items-end gap-3 w-full xl:w-auto">

          <!-- Search by Folio -->
          <div class="w-full md:w-auto flex flex-col gap-1.5">
            <label class="text-[11px] font-bold text-slate-400 uppercase tracking-wider ml-1">Buscar Ticket</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input v-model="buscarFolio" @input="aplicarFiltros" type="text" placeholder="Ej: C11P89"
                class="w-full md:w-44 bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 block p-2.5 pl-9 font-medium transition-all hover:bg-slate-100 placeholder-slate-400"
                autocomplete="off">
            </div>
          </div>

          <!-- Filter: Status -->
          <div class="w-full md:w-auto flex flex-col gap-1.5">
            <label class="text-[11px] font-bold text-slate-400 uppercase tracking-wider ml-1">Estado</label>
            <div class="relative">
              <select v-model="filtroEstado" @change="aplicarFiltros"
                class="w-full md:w-40 bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 block p-2.5 appearance-none font-medium cursor-pointer transition-all hover:bg-slate-100">
                <option value="todos">Todos</option>
                <option value="Completado">Completado</option>
                <option value="Cancelado">Cancelado</option>
                <option value="Pendiente">Pendiente</option>
                <option value="Atendiendo">Atendiendo</option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Filter: Sector -->
          <div v-if="!esSubjefe" class="w-full md:w-auto flex flex-col gap-1.5">
            <label class="text-[11px] font-bold text-slate-400 uppercase tracking-wider ml-1">Sector</label>
            <div class="relative">
              <select v-model="filtroSector" @change="aplicarFiltros"
                class="w-full md:w-48 bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 block p-2.5 appearance-none font-medium cursor-pointer transition-all hover:bg-slate-100">
                <option value="todos">Todos</option>
                <option v-for="s in sectores" :key="s.Sector" :value="s.Sector">{{ s.Sector }}</option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Filter: Date Range -->
          <div class="w-full md:w-auto flex flex-col gap-1.5">
            <label class="text-[11px] font-bold text-slate-400 uppercase tracking-wider ml-1">Fecha</label>
            <div class="flex gap-2">
              <input v-model="fechaInicio" @change="aplicarFiltros" type="date"
                class="flex-1 md:w-36 bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 block p-2.5 font-medium transition-all hover:bg-slate-100 placeholder-slate-400">
              <input v-model="fechaFin" @change="aplicarFiltros" type="date"
                class="flex-1 md:w-36 bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 block p-2.5 font-medium transition-all hover:bg-slate-100 placeholder-slate-400">
            </div>
          </div>

          <!-- Action: Clean -->
          <button @click="limpiarFiltros"
            class="h-[42px] px-4 bg-white border border-slate-200 text-slate-500 hover:text-rose-500 hover:border-rose-200 hover:bg-rose-50 rounded-xl text-sm font-bold transition-all duration-200 flex items-center gap-2 shadow-sm hover:shadow"
            title="Limpiar filtros">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span class="hidden md:inline">Limpiar</span>
          </button>
        </div>
      </div>

      <!-- Table Container -->
      <div class="relative overflow-hidden rounded-2xl border border-slate-200 shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-sm text-left">
            <thead class="bg-slate-50/80 border-b border-slate-200">
              <tr>
                <th scope="col" class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs">ID</th>
                <th scope="col" class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs">Sector
                </th>
                <th scope="col"
                  class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs text-center">Estado
                </th>
                <th scope="col" class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs">Creado
                </th>
                <th scope="col" class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs">
                  Actualizado</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-slate-100">
              <tr v-if="filtrado.length === 0">
                <td colspan="5" class="py-16 px-4 bg-white/50 relative">
                  <div class="flex-col items-center justify-center flex">
                    <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                      <svg class="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    </div>
                    <h3 class="text-slate-800 font-bold text-lg">Sin resultados</h3>
                    <p class="text-slate-500 text-sm mt-1 max-w-xs text-center">No se encontraron tickets con los filtros seleccionados.</p>
                  </div>
                </td>
              </tr>
              <tr v-for="t in filtrado" :key="t.folio" class="hover:bg-slate-50 transition-colors duration-150">
                <td class="px-6 py-4">{{ t.folio }}</td>
                <td class="px-6 py-4">{{ t.sector }}</td>
                <td class="px-6 py-4 capitalize text-center" :class="getEstadoColor(t.estado)">{{ t.estado }}</td>
                <td class="px-6 py-4">{{ formatearFecha(t.creado) }}</td>
                <td class="px-6 py-4">{{ t.finalizado ? formatearFecha(t.finalizado) : '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>

    <!-- Modal Reporte PDF -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" @click="cerrarModal"></div>
      <div class="relative bg-white rounded-3xl shadow-2xl w-full max-w-lg mx-4 p-8 animate-[fadeInUp_0.3s_ease-out] z-10">
        <button @click="cerrarModal" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>

        <div class="mb-6">
          <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2">
            <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            Generar Reporte PDF
          </h3>
          <p class="text-sm text-slate-500 mt-1">{{ semestreActual ? `Semestre actual: ${semestreActual.label} (${formatDateLabel(semestreActual.inicio)} - ${formatDateLabel(semestreActual.fin)})` : 'Selecciona un rango de fechas' }}</p>
        </div>

        <div class="mb-5">
          <label class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2 block">Rango rápido</label>
          <div class="flex gap-2">
            <button v-for="p in presets" :key="p.key" @click="aplicarPreset(p.key)" :class="['preset-btn flex-1 px-4 py-2.5 rounded-xl text-sm font-bold border-2 transition-all duration-200', presetActivo === p.key ? 'border-blue-500 text-blue-600 bg-blue-50' : 'border-slate-200 text-slate-600 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50']">
              {{ p.label }}
            </button>
          </div>
        </div>

        <div class="mb-5">
          <label class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2 block">Rango personalizado</label>
          <div class="flex gap-3">
            <div class="flex-1">
              <label class="text-xs text-slate-500 mb-1 block">Desde</label>
              <input v-model="reporteDesde" type="date" class="w-full bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 p-2.5 font-medium transition-all hover:bg-slate-100" />
            </div>
            <div class="flex-1">
              <label class="text-xs text-slate-500 mb-1 block">Hasta</label>
              <input v-model="reporteHasta" type="date" class="w-full bg-slate-50 border border-slate-200 text-slate-700 text-sm rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 p-2.5 font-medium transition-all hover:bg-slate-100" />
            </div>
          </div>
        </div>

        <div v-if="modalError" class="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-600 text-sm font-medium">{{ modalError }}</div>

        <div class="flex gap-3">
          <button @click="cerrarModal" class="flex-1 px-5 py-2.5 rounded-xl text-sm font-bold border border-slate-200 text-slate-600 hover:bg-slate-50 transition-all">Cancelar</button>
          <button @click="generarReporte" :disabled="generando" class="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-blue-500 to-indigo-500 text-white px-5 py-2.5 rounded-xl font-bold shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 hover:-translate-y-0.5 active:translate-y-0 active:scale-95 transition-all duration-200">
            <svg v-if="generando" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            {{ generando ? 'Generando...' : 'Generar PDF' }}
          </button>
        </div>
      </div>
    </div>
</template>

<script setup lang="ts">

definePageMeta({ layout: 'admin', middleware: 'auth' })
useHead({ title: 'Historial de Tickets' })

const { API_BASE_URL } = useConfig()
const socket = useSocket()
const { getCurrentUser, getSessionToken } = useAuth()
const { startGuard, stopGuard } = useSessionGuard()
const { lanzarAlerta } = useToast()

const currentUser = ref(null)
const esSubjefe = ref(false)
const sectorSubjefe = ref(null)

const historial = ref([])
const filtrado = ref([])
const sectores = ref([])
const totalTicketsHoy = ref(0)
const resumen = reactive({ total: 0, completados: 0, cancelados: 0, atendiendo: 0, pendientes: 0 })

const buscarFolio = ref('')
const filtroEstado = ref('todos')
const filtroSector = ref('todos')
const fechaInicio = ref('')
const fechaFin = ref('')

const showModal = ref(false)
const reporteDesde = ref('')
const reporteHasta = ref('')
const modalError = ref('')
const generando = ref(false)
const semestreActual = ref(null)
const presetActivo = ref('')
const presets = [{ key: 'hoy', label: 'Hoy' }, { key: 'semanal', label: 'Última Semana' }, { key: 'mensual', label: 'Último Mes' }]

const fechaActual = computed(() => new Date().toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }))

/**
 * Parsea una fecha desde un string.
 * @param {string | null} str - Cadena de fecha.
 * @returns {Date | null}
 */
function parseFecha(str: string | null): Date | null { if (!str) return null; const d = new Date(str); return isNaN(d.getTime()) ? null : d }
/**
 * Formatea una fecha a string.
 * @param {string} str - Cadena de fecha.
 * @returns {string}
 */
function formatearFecha(str: string): string {
  const f = parseFecha(str); if (!f) return '-'
  const dd = String(f.getUTCDate()).padStart(2,'0'), mm = String(f.getUTCMonth()+1).padStart(2,'0'), yy = f.getUTCFullYear()
  const hh = String(f.getUTCHours()).padStart(2,'0'), mi = String(f.getUTCMinutes()).padStart(2,'0')
  return `${dd}/${mm}/${yy}, ${hh}:${mi}`
}
/**
 * Formatea una etiqueta de fecha.
 * @param {string} s - Cadena de fecha YYYY-MM-DD.
 * @returns {string}
 */
function formatDateLabel(s: string): string { const [y,m,d] = s.split('-'); return `${d}/${m}/${y}` }
/**
 * Convierte un objeto Date a formato YYYY-MM-DD.
 * @param {Date} d - Objeto Date.
 * @returns {string}
 */
function toYMD(d: Date): string { return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` }
/**
 * Obtiene la clase de color para un estado.
 * @param {string} e - Estado.
 * @returns {string}
 */
const estadoColors: Record<string, string> = { Completado:'text-green-600 font-semibold', Cancelado:'text-red-600 font-semibold', Atendiendo:'text-blue-600 font-semibold', Pendiente:'text-yellow-600 font-semibold' };
function getEstadoColor(e: string): string { return estadoColors[e] || 'text-gray-600' }

/**
 * Carga el historial de tickets.
 * @returns {Promise<void>}
 */
async function cargarHistorial(): Promise<void> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/tickets/historial`); if (!res.ok) return
    let data = await res.json()
    if (esSubjefe.value && sectorSubjefe.value) data = data.filter(t => t.sector === sectorSubjefe.value)
    historial.value = data.map(t => ({ ...t, creado: t.fecha_ticket, finalizado: t.fecha_ultimo_estado || null }))
  } catch {}
}

/**
 * Carga el total de tickets del día.
 * @returns {Promise<void>}
 */
async function cargarTotalTickets(): Promise<void> {
  if (esSubjefe.value) {
    const hoy = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Mexico_City' })
    totalTicketsHoy.value = historial.value.filter(t => {
      const f = parseFecha(t.creado); if (!f) return false
      const local = f.toLocaleDateString('en-CA', { timeZone: 'America/Mexico_City' })
      return local === hoy
    }).length
  } else {
    try {
      const res = await fetch(`${API_BASE_URL}/api/total_tickets`); if (!res.ok) return
      const data = await res.json()
      totalTicketsHoy.value = Array.isArray(data) ? (data[0]?.cantidad || 0) : (data.cantidad ?? data ?? 0)
    } catch {}
  }
}

/**
 * Aplica los filtros seleccionados al historial de tickets.
 * @returns {void}
 */
function aplicarFiltros(): void {
  let f = [...historial.value]
  if (filtroEstado.value !== 'todos') f = f.filter(t => t.estado === filtroEstado.value)
  if (filtroSector.value !== 'todos') f = f.filter(t => t.sector === filtroSector.value)
  if (buscarFolio.value) f = f.filter(t => t.folio.toLowerCase().includes(buscarFolio.value.toLowerCase()))
  if (fechaInicio.value && fechaFin.value) {
    const fi = new Date(fechaInicio.value + 'T00:00:00'), ff = new Date(fechaFin.value + 'T23:59:59')
    f = f.filter(t => { const d = parseFecha(t.creado); if (!d) return false; const y=d.getUTCFullYear(),m=String(d.getUTCMonth()+1).padStart(2,'0'),dd=String(d.getUTCDate()).padStart(2,'0'); const cd = new Date(`${y}-${m}-${dd}T00:00:00`); return cd >= fi && cd <= ff })
  }
  f.sort((a,b) => { const da = parseFecha(a.creado), db = parseFecha(b.creado); return db - da })
  filtrado.value = f
  resumen.total = f.length
  resumen.completados = f.filter(t => t.estado === 'Completado').length
  resumen.cancelados = f.filter(t => t.estado === 'Cancelado').length
  resumen.atendiendo = f.filter(t => t.estado === 'Atendiendo').length
  resumen.pendientes = f.filter(t => t.estado === 'Pendiente').length
}

/**
 * Limpia los filtros actuales.
 * @returns {void}
 */
function limpiarFiltros(): void { filtroEstado.value = 'todos'; filtroSector.value = 'todos'; fechaInicio.value = ''; fechaFin.value = ''; buscarFolio.value = ''; aplicarFiltros() }

/**
 * Carga la lista de sectores disponibles.
 * @returns {Promise<void>}
 */
async function cargarSectores(): Promise<void> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/sectores`); if (!res.ok) return
    sectores.value = await res.json()
  } catch {}
}

/**
 * Abre el modal de reporte.
 * @returns {void}
 */
function abrirModalReporte(): void { showModal.value = true; modalError.value = ''; presetActivo.value = ''; cargarInfoSemestre() }
/**
 * Cierra el modal de reporte.
 * @returns {void}
 */
function cerrarModal(): void { showModal.value = false; modalError.value = '' }

/**
 * Carga la información del semestre actual.
 * @returns {Promise<void>}
 */
async function cargarInfoSemestre(): Promise<void> {
  try { const res = await fetch(`${API_BASE_URL}/api/reporte/semestre-actual`); if (res.ok) semestreActual.value = await res.json() } catch {}
}

/**
 * Aplica un preset de fechas para el reporte.
 * @param {string} key - Identificador del preset.
 * @returns {void}
 */
function aplicarPreset(key: string): void {
  const hoy = new Date(); let desde, hasta
  if (key === 'hoy') { desde = hasta = toYMD(hoy) }
  else if (key === 'semanal') { const h7 = new Date(hoy); h7.setDate(hoy.getDate()-7); desde = toYMD(h7); hasta = toYMD(hoy) }
  else if (key === 'mensual') { const h30 = new Date(hoy); h30.setDate(hoy.getDate()-30); desde = toYMD(h30); hasta = toYMD(hoy) }
  if (semestreActual.value) { if (desde < semestreActual.value.inicio) desde = semestreActual.value.inicio; if (hasta > semestreActual.value.fin) hasta = semestreActual.value.fin }
  reporteDesde.value = desde; reporteHasta.value = hasta; presetActivo.value = key; modalError.value = ''
}

/**
 * Genera el reporte en PDF.
 * @returns {Promise<void>}
 */
async function generarReporte(): Promise<void> {
  if (!reporteDesde.value || !reporteHasta.value) { modalError.value = 'Selecciona ambas fechas'; return }
  if (reporteDesde.value > reporteHasta.value) { modalError.value = "'Desde' no puede ser posterior a 'Hasta'"; return }
  generando.value = true; modalError.value = ''
  try {
    let url = `${API_BASE_URL}/api/reporte/generar?desde=${reporteDesde.value}&hasta=${reporteHasta.value}`
    if (esSubjefe.value && sectorSubjefe.value) url += `&sector=${encodeURIComponent(sectorSubjefe.value)}`
    const res = await fetch(url); if (!res.ok) { const e = await res.json(); throw new Error(e.detail || e.error || 'Error') }
    const blob = await res.blob(); const u = window.URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = u; a.download = `reporte_${reporteDesde.value}_${reporteHasta.value}.pdf`
    document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(u)
    cerrarModal()
  } catch (err) { modalError.value = err.message } finally { generando.value = false }
}




onMounted(async () => {
  currentUser.value = getCurrentUser()
  esSubjefe.value = currentUser.value?.rol === 6
  sectorSubjefe.value = esSubjefe.value ? currentUser.value.sector : null

  await cargarSectores()
  await cargarHistorial()
  aplicarFiltros()
  cargarTotalTickets()

  socket.on('connect', () => { if (currentUser.value?.id) socket.emit('ventanilla_register', { id_empleado: currentUser.value.id, session_token: getSessionToken() }) })
  socket.on('tickets_updated', async () => { await cargarHistorial(); aplicarFiltros(); cargarTotalTickets() })

  startGuard()
})
onUnmounted(() => {
  stopGuard()
  socket.off('tickets_updated')
})
</script>
