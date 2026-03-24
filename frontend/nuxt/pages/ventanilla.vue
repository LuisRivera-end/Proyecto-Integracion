<template>
  <body class="min-h-screen">
    <div class="bg-gradient-to-br from-slate-600 via-slate-500 to-emerald-300 min-h-screen">
      <div id="management-screen" class="min-h-screen p-8">
        <div class="max-w-6xl mx-auto">
          <!-- Header Card -->
          <div class="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-8 mb-8 flex justify-between items-center border border-slate-200">
            <div class="flex items-center gap-5 flex-1">
              <img src="/ual_no_fondo.png" alt="Logo UAL" class="h-14 object-contain" />
              <div>
                <h1 class="text-3xl font-bold text-slate-800">Panel de Ventanilla</h1>
                <p class="text-slate-600 mt-1">Sector: <span class="font-semibold text-emerald-700">{{ userSectorDisplay }}</span></p>
                <p class="text-sm text-slate-500 mt-0.5">Usuario: <span class="font-medium">{{ userName }}</span></p>
              </div>
            </div>
            <button @click="cerrarSesion" class="bg-slate-600 hover:bg-slate-700 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-300 flex items-center gap-2 shadow-md hover:shadow-lg">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Cerrar Sesión
            </button>
          </div>

          <!-- Main Card -->
          <div class="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl p-8 border border-slate-200">
            <!-- Banner Caja Rápida -->
            <div v-if="cajaRapidaVisible"
                class="mb-6 rounded-xl border border-amber-300 bg-gradient-to-r from-amber-50 to-amber-100 p-4 items-center gap-3 shadow-sm flex">
                <div class="w-10 h-10 rounded-lg bg-amber-200 flex items-center justify-center flex-shrink-0">
                    <svg class="w-5 h-5 text-amber-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                </div>
                <div>
                    <p class="font-bold text-amber-800 text-sm">Modo Caja Rápida Activo</p>
                    <p class="text-xs text-amber-600 font-medium">{{ cajaRapidaBannerHora }}</p>
                </div>
            </div>

            <button @click="llamarSiguiente" :disabled="!!currentTicket" title="También puedes presionar la tecla Enter" :class="[
              'w-full text-white text-lg font-bold py-3 mb-6 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl',
              currentTicket ? 'bg-gray-400 opacity-50 cursor-not-allowed' : 'bg-gradient-to-r from-slate-500 to-emerald-600 hover:from-slate-700 hover:to-emerald-700'
            ]">
              Llamar Siguiente Ticket
            </button>

            <!-- Current Ticket -->
            <div v-if="currentTicket" class="mb-6">
              <div class="bg-blue-50 border border-blue-200 rounded-xl p-6">
                <h3 class="text-lg font-semibold text-emerald-800 mb-4 text-center">Ticket en Atención</h3>
                <div class="flex items-center justify-center space-x-6 mb-4">
                  <div class="text-center">
                    <p class="text-2xl font-bold text-emerald-600">{{ currentTicket.folio }}</p>
                    <p class="text-sm text-emerald-500 mt-1">Folio</p>
                  </div>
                </div>
                <div class="flex gap-4 mt-4">
                  <button @click="cancelarTicket" class="flex-1 bg-red-600 hover:bg-red-700 text-white text-lg font-bold py-3 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl flex items-center justify-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    Cancelar Ticket
                  </button>
                  <button @click="completarTicket" title="También puedes presionar la tecla F" class="flex-1 bg-green-600 hover:bg-green-700 text-white text-lg font-bold py-3 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl flex items-center justify-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                    Completar Ticket
                  </button>
                </div>
              </div>
            </div>

            <h2 class="text-2xl font-bold text-slate-800 mb-6">Tickets en Espera</h2>
            <div v-if="pendientes.length > 0" class="space-y-4 mb-6">
              <div v-for="t in pendientes" :key="t.folio" class="p-4 bg-gray-50 border rounded-lg shadow-sm">
                <div class="text-center">
                  <p class="font-semibold text-gray-800">Ticket: <span class="text-blue-600">{{ t.folio || t.Folio }}</span></p>
                  <p class="text-xs text-gray-500 mt-1">Estado: <span class="text-orange-500">{{ t.estado || 'Pendiente' }}</span></p>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-16 bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-200">
              <div class="inline-flex items-center justify-center w-24 h-24 bg-slate-100 rounded-full mb-4">
                <svg class="w-12 h-12 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p class="text-slate-600 text-xl font-semibold">No hay tickets pendientes</p>
              <p class="text-slate-500 mt-2">Los nuevos tickets aparecerán aquí automáticamente</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Confirm Modal -->
      <div v-if="showConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white rounded-xl shadow-lg p-6 w-96 text-center">
          <h2 class="text-lg font-semibold mb-4">{{ confirmTitle }}</h2>
          <p class="text-gray-600 mb-6">{{ confirmMessage }}</p>
          <div class="flex justify-center gap-4">
            <button @click="confirmResolve(false); showConfirm = false" class="px-4 py-2 bg-gray-300 hover:bg-gray-400 rounded-lg">Cancelar</button>
            <button @click="confirmResolve(true); showConfirm = false" class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg">Aceptar</button>
          </div>
        </div>
      </div>
    </div>
  </body>
</template>

<script setup>

definePageMeta({ layout: 'default', middleware: 'auth' })
useHead({ title: 'Panel de Ventanilla' })

const { API_BASE_URL } = useConfig()
const { lanzarAlerta } = useToast()
const { logoutWithOverlay, getCurrentUser, getSessionToken } = useAuth()
const { startGuard, stopGuard } = useSessionGuard()
const socket = useSocket()

const currentUser = ref(null)
const currentTicket = ref(null)
const pendientes = ref([])
const showConfirm = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
let confirmResolve = () => {}

const userSectorDisplay = computed(() => {
  if (!currentUser.value) return ''
  if (currentUser.value.ventanilla) return `${currentUser.value.sector} - ${currentUser.value.ventanilla.nombre}`
  return currentUser.value.sector || ''
})
const userName = computed(() => currentUser.value?.username || '')

const isCajaRapidaActiva = ref(false)
const cajaRapidaHoraFin = ref(null)
const tipoCajaFiltro = ref(null) // null = sin filtro, 'rapida' = solo rápida, 'normal' = solo normal

const cajaRapidaVisible = computed(() => isCajaRapidaActiva.value)
const cajaRapidaBannerHora = ref('')

function mostrarConfirmacion(msg, titulo = 'Confirmación') {
  return new Promise((resolve) => {
    confirmTitle.value = titulo
    confirmMessage.value = msg
    showConfirm.value = true
    confirmResolve = resolve
  })
}

async function recuperarTicketActivo() {
  if (!currentUser.value?.ventanilla) return
  try {
    const res = await fetch(`${API_BASE_URL}/api/tickets/activo/${currentUser.value.ventanilla.id}`)
    if (!res.ok) return
    const data = await res.json()
    if (data.activo && data.folio) currentTicket.value = { folio: data.folio }
  } catch {}
}

async function fetchTickets() {
  if (!currentUser.value?.sector) return
  try {
    let url = `${API_BASE_URL}/api/tickets?sector=${encodeURIComponent(currentUser.value.sector)}`
    if (currentUser.value?.id) {
       url += `&id_empleado=${currentUser.value.id}`
    }
    if (tipoCajaFiltro.value) {
      url += `&tipo_caja=${tipoCajaFiltro.value}`
    }
    const res = await fetch(url)
    if (!res.ok) {
      pendientes.value = []
      return
    }
    let tickets = await res.json()
    if (!Array.isArray(tickets)) tickets = tickets.tickets || tickets.data || []

    const norm = String(currentUser.value.sector).trim().toLowerCase()
    const filtered = tickets.filter(t => {
      if (!t || !t.sector) return false
      const isPending = t.estado_id === 1 || t.ID_Estados === 1 || String(t.estado || '').toLowerCase().includes('pendiente')
      const isCorrectSector = String(t.sector).trim().toLowerCase() === norm
      const isCurrent = currentTicket.value && (t.folio || t.ID_Ticket) === currentTicket.value.folio
      return isCorrectSector && isPending && !isCurrent
    })
    
    pendientes.value = filtered
  } catch {
    pendientes.value = []
  }
}

async function llamarSiguiente() {
  if (!currentUser.value?.ventanilla || currentTicket.value) return
  try {
    const bodyData = { id_ventanilla: currentUser.value.ventanilla.id, id_empleado: currentUser.value.id }
    if (tipoCajaFiltro.value) {
      bodyData.tipo_caja = tipoCajaFiltro.value
    }

    const res = await fetch(`${API_BASE_URL}/api/tickets/llamar-siguiente`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyData)
    })
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || e.error || 'Error') }
    const data = await res.json()
    currentTicket.value = { folio: data.folio }
    await fetchTickets()
  } catch (err) { lanzarAlerta(err.message || 'Error', 'error') }
}

async function completarTicket() {
  if (!currentTicket.value) return
  try {
    const res = await fetch(`${API_BASE_URL}/api/tickets/${currentTicket.value.folio}/complete`, { method: 'PUT', headers: { 'Content-Type': 'application/json' } })
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || e.error || 'Error') }
    const f = currentTicket.value.folio
    currentTicket.value = null
    await fetchTickets()
    lanzarAlerta(`Ticket ${f} completado exitosamente`, 'success')

    if (tipoCajaFiltro.value === 'rapida') {
      await checkDrenajeCajaRapida()
    }
  } catch (err) { lanzarAlerta(err.message || 'Error', 'error') }
}

async function cancelarTicket() {
  if (!currentTicket.value) return
  const ok = await mostrarConfirmacion(`¿Cancelar ticket ${currentTicket.value.folio}?`, 'Cancelar Ticket')
  if (!ok) return
  try {
    const res = await fetch(`${API_BASE_URL}/api/tickets/${currentTicket.value.folio}/cancel`, { method: 'PUT', headers: { 'Content-Type': 'application/json' } })
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail || e.error || 'Error') }
    const f = currentTicket.value.folio
    currentTicket.value = null
    await fetchTickets()
    lanzarAlerta(`Ticket ${f} cancelado`, 'success')

    if (tipoCajaFiltro.value === 'rapida') {
      await checkDrenajeCajaRapida()
    }
  } catch (err) { lanzarAlerta(err.message || 'Error', 'error') }
}

function formatHora12(hora24) {
  if (!hora24) return ''
  const [h, m] = hora24.split(':').map(Number)
  const ampm = h >= 12 ? 'PM' : 'AM'
  const h12 = h % 12 || 12
  return `${h12}:${String(m).padStart(2, '0')} ${ampm}`
}

async function checkCajaRapida() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/caja-rapida/estado`)
    const estado = await res.json()

    const miVentanillaId = currentUser.value?.ventanilla ? currentUser.value.ventanilla.id : null

    // Mi ventanilla está en modo rápida (activo O drenando)
    const esMiVentanillaActiva = (estado.activo || estado.expirado) && miVentanillaId &&
        Array.isArray(estado.ventanillas) && estado.ventanillas.includes(miVentanillaId)

    // Caja rápida activa en mi sector pero NO en mi ventanilla
    const cajaRapidaActivaEnMiSector = (estado.activo || estado.expirado) && currentUser.value?.sector &&
        currentUser.value.sector.toLowerCase() === 'cajas'

    if (esMiVentanillaActiva) {
      isCajaRapidaActiva.value = true
      tipoCajaFiltro.value = 'rapida'
      cajaRapidaHoraFin.value = estado.hora_fin
      if (estado.expirado) {
        cajaRapidaBannerHora.value = `Tiempo expirado — atendiendo tickets restantes`
      } else {
        cajaRapidaBannerHora.value = `Hasta las ${formatHora12(estado.hora_fin)}`
      }
    } else if (cajaRapidaActivaEnMiSector) {
      isCajaRapidaActiva.value = false
      tipoCajaFiltro.value = 'normal'
      cajaRapidaHoraFin.value = null
    } else {
      isCajaRapidaActiva.value = false
      tipoCajaFiltro.value = null
      cajaRapidaHoraFin.value = null
    }
  } catch (err) {
    console.error('Error al verificar Caja Rápida:', err)
  }
}

async function checkDrenajeCajaRapida() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/caja-rapida/check-drenaje`, { method: 'POST' })
    const data = await res.json()
    if (!data.drenando) {
      await checkCajaRapida()
      await fetchTickets()
    }
  } catch (err) {
    console.error('Error en check drenaje:', err)
  }
}

function cerrarSesion() {
  socket.emit('ventanilla_disconnect')
  logoutWithOverlay()
}

function handleKeydown(e) {
  if (showConfirm.value) {
    e.preventDefault()
    e.stopPropagation()
    return
  }
  
  if (e.key === 'Enter') {
    if (!currentTicket.value) {
      e.preventDefault()
      llamarSiguiente()
    }
  }
  
  if (e.key === 'f' || e.key === 'F') {
    if (currentTicket.value) {
      e.preventDefault()
      completarTicket()
    }
  }
}




onMounted(async () => {
  const user = getCurrentUser()
  if (!user) { navigateTo('/login'); return }
  currentUser.value = user

  await checkCajaRapida()
  await recuperarTicketActivo()
  await fetchTickets()

  // --- WebSocket Listeners ---
  socket.on('tickets_updated', handleTicketsUpdated)
  socket.on('caja_rapida_updated', handleCajaRapidaUpdated)

  document.addEventListener("keydown", handleKeydown)
  startGuard()

  socket.on('connect', () => {
    if (currentUser.value?.id) socket.emit('ventanilla_register', { id_empleado: currentUser.value.id, session_token: getSessionToken() })
  })
  
  // Si ya está conectado al montar, emitir inmediatamente
  if (socket.connected && currentUser.value?.id) {
    socket.emit('ventanilla_register', { id_empleado: currentUser.value.id, session_token: getSessionToken() })
  }
})

async function handleTicketsUpdated() {
  console.log('🔄 Actualizando tickets por WS...');
  await fetchTickets()
  await recuperarTicketActivo()
}

async function handleCajaRapidaUpdated(data) {
  console.log('⚡ Cambio detectado en Caja Rápida...');
  const wasActive = isCajaRapidaActiva.value
  const prevFiltro = tipoCajaFiltro.value
  
  await checkCajaRapida()
  await fetchTickets()

  if (isCajaRapidaActiva.value && !wasActive) {
    if (data && data.data && data.data.expirado) {
      lanzarAlerta('Tiempo de Caja Rápida expirado — atendiendo tickets restantes', 'warning')
    } else {
      lanzarAlerta(`Modo Caja Rápida activado hasta las ${cajaRapidaHoraFin.value}`, 'warning')
    }
  } else if (!isCajaRapidaActiva.value && wasActive) {
    lanzarAlerta('Modo Caja Rápida desactivado', 'success')
  } else if (prevFiltro === 'normal' && tipoCajaFiltro.value === null) {
    lanzarAlerta('Modo Caja Rápida finalizado', 'success')
  }
}

onUnmounted(() => {
  stopGuard()
  document.removeEventListener("keydown", handleKeydown)
  socket.off('tickets_updated', handleTicketsUpdated)
  socket.off('caja_rapida_updated', handleCajaRapidaUpdated)
  socket.emit('ventanilla_disconnect')
})
</script>
