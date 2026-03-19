<template>
  <body class="h-screen bg-gradient-to-br from-[#0c4944] via-[#115e59] to-[#042f2e] overflow-hidden">
    <LoadingOverlay v-if="loading" text="Conectando con el servidor..." />
    
    <div class="flex gap-5 p-5 h-full relative z-10">
      
      <!-- IZQUIERDA: Tablero de tickets -->
      <div class="flex-1 flex flex-col rounded-[2rem] overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.2)] border border-white/10 bg-white/95 backdrop-blur-xl min-h-0">
        
        <!-- Sección: Turnos en Atención -->
        <div v-if="atendiendo.length > 0" id="atendiendo-container">
          <div class="bg-gradient-to-r from-amber-500 to-orange-500 px-8 py-3.5 flex items-center gap-3 shadow-md z-10 relative">
            <span class="inline-block w-3 h-3 bg-white rounded-full pulse-dot"></span>
            <span class="text-white text-sm font-black uppercase tracking-widest drop-shadow-sm">Atendiendo Ahora</span>
          </div>
          <div id="atendiendo-filas" class="bg-orange-50/50">
            <div v-for="t in atendiendo" :key="t.folio" class="grid grid-cols-3 items-center px-8 py-3 border-b border-amber-200 fade-in-row">
              <span class="text-3xl font-black text-amber-800 tracking-tight">{{ t.folio }}</span>
              <span class="text-3xl font-black text-amber-800">{{ t.sector }}</span>
              <span class="text-3xl font-black text-amber-800">{{ getVentanillaDisplay(t) }}</span>
            </div>
          </div>
        </div>

        <!-- Cabecera del tablero -->
        <div class="grid grid-cols-3 bg-slate-100/80 px-8 py-4 border-y border-slate-200 backdrop-blur-sm">
          <span class="text-slate-500 text-lg font-bold uppercase tracking-widest">Ticket</span>
          <span class="text-slate-500 text-lg font-bold uppercase tracking-widest">Sector</span>
          <span class="text-slate-500 text-lg font-bold uppercase tracking-widest">Ventanilla</span>
        </div>

        <!-- Filas de tickets pendientes -->
        <div v-if="visibles.length > 0" id="contenedor" class="flex-1 overflow-hidden bg-white/50 custom-scrollbar overflow-y-auto">
          <div v-for="t in visibles" :key="t.folio" class="grid grid-cols-3 items-center px-8 py-5 border-b border-slate-200 hover:bg-slate-50 transition-colors fade-in-row">
            <span class="text-4xl font-black text-slate-800 tracking-tight">{{ t.folio }}</span>
            <span class="text-4xl font-black text-slate-800">{{ t.sector }}</span>
            <span class="text-4xl font-black text-slate-800">{{ getEstado(t) === 3 ? getVentanillaDisplay(t) : '—' }}</span>
          </div>
        </div>

        <!-- Sin tickets -->
        <div v-else id="sinTickets" class="flex-1 flex flex-col items-center justify-center gap-4 text-slate-400 py-16">
          <div class="bg-slate-100 p-6 rounded-full">
            <svg class="w-12 h-12 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p class="text-xl font-medium text-slate-500">No hay tickets en espera</p>
        </div>

        <!-- Footer ticker para tickets extra -->
        <div v-if="overflow.length > 0" id="ticker-container" class="bg-slate-800 border-t border-slate-700 px-6 py-3 overflow-hidden">
          <div class="flex items-center gap-4">
            <span class="text-amber-400 text-xs font-black uppercase tracking-widest flex-shrink-0 flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
              Más en cola
            </span>
            <div class="flex-1 overflow-hidden">
              <div id="ticker-track" class="ticker-track" :class="{ 'animado': overflow.length >= 5 }" :style="overflow.length >= 5 ? `animation-duration: ${Math.max(10, overflow.length * 3)}s; justify-content: flex-start;` : 'justify-content: center;'">
                 <template v-for="(t, idx) in tickerItems" :key="idx">
                    <span class="inline-flex items-center gap-2 text-slate-300 font-bold text-lg">
                        <span class="text-white font-black">{{ t.folio }}</span>
                        <span class="text-slate-400">{{ t.sector }}</span>
                    </span>
                    <span v-if="idx < tickerItems.length - 1 && !(overflow.length >= 5 && idx === Math.floor(tickerItems.length/2) - 1)" class="text-slate-600 mx-2">•</span>
                    <span v-if="overflow.length >= 5 && idx === Math.floor(tickerItems.length/2) - 1" class="text-slate-600 mx-4">|</span>
                 </template>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- DERECHA: Info + Sectores -->
      <div class="w-[26rem] flex-shrink-0 flex flex-col gap-5">
        
        <!-- Tarjeta: título + audio -->
        <div class="bg-white/95 backdrop-blur-xl rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.15)] border border-white/20 p-8 flex flex-col items-center text-center relative overflow-hidden">
            <div class="absolute -top-10 -right-10 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl"></div>
            
            <div class="flex justify-center mb-6 bg-slate-50 p-4 rounded-2xl w-full shadow-inner border border-slate-100 relative z-10">
                <img src="/ual_no_fondo.png" alt="Logo UAL" class="h-32 object-contain">
            </div>
            
            <h1 class="text-3xl font-black text-slate-800 tracking-tight relative z-10">Sistema de Turnos</h1>
            
            <button @click="toggleAudio" :disabled="audioActivado" :class="[
              'mt-8 w-full flex items-center justify-center gap-3 font-bold py-4 px-6 rounded-2xl transition-all duration-300 transform relative z-10',
              audioActivado ? 'bg-emerald-100 text-emerald-700 opacity-60 cursor-not-allowed shadow-inner' : 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/30 active:scale-95 hover:-translate-y-0.5'
            ]">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a6 6 0 000-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                </svg>
                {{ audioActivado ? '🔊 Audio activado' : 'Activar avisos por voz' }}
            </button>
        </div>
        
        <!-- Tarjeta: badges de sector -->
        <div class="bg-white/95 backdrop-blur-xl rounded-[2rem] shadow-[0_8px_30px_rgb(0,0,0,0.15)] border border-white/20 p-8 flex-1">
            <div class="flex items-center gap-3 mb-6">
                <svg class="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <h2 class="text-slate-500 text-xs font-bold uppercase tracking-widest">
                    Espera por sector
                </h2>
            </div>
            
            <div id="sector-badges" class="grid grid-cols-2 gap-4">
                <div v-for="(cantidad, sector) in sectorCounts" :key="sector" class="flex flex-col p-4 bg-slate-50 rounded-xl border border-slate-100 shadow-sm relative overflow-hidden group">
                  <span class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 line-clamp-1 truncate pr-8">{{ sector }}</span>
                  <span class="text-2xl font-black text-slate-700">{{ cantidad }}</span>
                  <div class="absolute right-0 top-0 bottom-0 w-1 flex flex-col">
                    <div class="h-1/2 bg-blue-400/20 w-full group-hover:bg-blue-400/40 transition-colors"></div>
                    <div class="h-1/2 bg-indigo-400/20 w-full group-hover:bg-indigo-400/40 transition-colors"></div>
                  </div>
                </div>
            </div>
        </div>

      </div>
    </div>
  </body>
</template>

<script setup>

definePageMeta({ layout: 'default' })
useHead({ title: 'Pantalla de Turnos' })

const { API_BASE_URL } = useConfig()
const socket = useSocket()
const { getCurrentUser, getSessionToken } = useAuth()

const allTickets = ref([])
const audioActivado = ref(false)
let audioContext = null
const audioQueue = []
let isPlaying = false
let estadoAnterior = new Map()

const loading = ref(true)
const sectorCounts = ref({})

const fechaActual = computed(() => {
  const f = new Date()
  return f.toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
})

const atendiendo = computed(() => allTickets.value.filter(t => {
  const e = getEstado(t)
  return e === 3 || e === 'Atendiendo'
}))

const pendientes = computed(() => allTickets.value.filter(t => {
  const e = getEstado(t)
  return e === 1 || e === 'Pendiente'
}))

const MAX_VISIBLE = computed(() => Math.max(3, 9 - atendiendo.value.length))
const visibles = computed(() => pendientes.value.slice(0, MAX_VISIBLE.value))
const overflow = computed(() => pendientes.value.slice(MAX_VISIBLE.value))
const tickerItems = computed(() => overflow.value.length >= 5 ? [...overflow.value, ...overflow.value] : overflow.value)

function getEstado(t) { return t.estado_id || t.ID_Estados || t.estado }
function getVentanillaDisplay(t) {
  const v = t.ventanilla || t.Ventanilla
  if (v) return v.replace(/ventanilla\s*/i, '')
  if (t.id_ventanilla) return `Ventanilla ${t.id_ventanilla}`
  return 'En atención'
}

function toggleAudio() {
  audioActivado.value = true
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  audioContext = new AudioCtx()
  if (audioContext.state === 'suspended') audioContext.resume()
  const buf = audioContext.createBuffer(1, 1, 22050)
  const src = audioContext.createBufferSource()
  src.buffer = buf; src.connect(audioContext.destination); src.start(0)
}

function reproducirAudio(url) {
  if (!audioActivado.value || !audioContext) return
  audioQueue.push(url)
  if (!isPlaying) _playNext()
}

async function _playNext() {
  if (!audioQueue.length) { isPlaying = false; return }
  isPlaying = true
  const url = audioQueue.shift()
  try {
    if (audioContext.state === 'suspended') await audioContext.resume()
    const resp = await fetch(url)
    const ab = await resp.arrayBuffer()
    const buf = await audioContext.decodeAudioData(ab)
    const src = audioContext.createBufferSource()
    src.buffer = buf; src.connect(audioContext.destination)
    src.onended = () => _playNext()
    src.start(0)
  } catch { _playNext() }
}

async function llamarTicket(folio, ventanilla, id_ventanilla) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/turno/llamar`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folio, ventanilla, id_ventanilla })
    })
    if (!res.ok) return
    const data = await res.json()
    if (data.audio_url) {
      const audioUrl = data.audio_url.startsWith('http') ? data.audio_url : `${API_BASE_URL}${data.audio_url}`
      reproducirAudio(audioUrl)
    }
  } catch {}
}

async function cargarTickets() {
  try {
    const [resTickets, resCounts] = await Promise.all([
      fetch(`${API_BASE_URL}/api/tickets/publico`),
      fetch(`${API_BASE_URL}/api/tickets_count`)
    ])

    if (!resTickets.ok) {
      allTickets.value = []
    } else {
        const data = await resTickets.json()
        const prev = new Map(estadoAnterior)
    
        allTickets.value = data.filter(t => {
          const e = getEstado(t)
          return e !== 4 && e !== 'Completado' && e !== 2 && e !== 'Cancelado'
        })
    
        allTickets.value.forEach(t => {
          const e = String(getEstado(t))
          const prevHash = prev.get(t.folio)
          if ((e === '3' || e === 'Atendiendo') && prevHash !== e) {
            llamarTicket(t.folio, t.ventanilla, t.id_ventanilla)
          }
        })
    
        estadoAnterior = new Map()
        allTickets.value.forEach(t => estadoAnterior.set(t.folio, String(getEstado(t))))
    }

    if (resCounts.ok) {
        sectorCounts.value = await resCounts.json()
    }
    
  } catch {
    allTickets.value = []
    sectorCounts.value = {}
  } finally {
      loading.value = false
  }
}


onMounted(() => {
  cargarTickets()
  socket.on('connect', () => {
    const u = getCurrentUser()
    if (u?.id) socket.emit('ventanilla_register', { id_empleado: u.id, session_token: getSessionToken() })
  })
  socket.on('tickets_updated', () => cargarTickets())
})
onUnmounted(() => { socket.off('tickets_updated') })
</script>

<style scoped>
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.ticker-track { display: flex; gap: 2rem; white-space: nowrap; }
.animado { animation: ticker-scroll 20s linear infinite; }
.ticker-track:hover { animation-play-state: paused; }

.fade-in-row { animation: fadeIn 0.5s ease-out forwards; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse-dot {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(255, 255, 255, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
}
.pulse-dot { animation: pulse-dot 2s infinite; }

.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
