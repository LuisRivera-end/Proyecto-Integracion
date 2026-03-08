<template>
  <div
    class="bg-gradient-to-br from-slate-600 via-slate-500 to-emerald-300 min-h-screen flex flex-col bg-fixed w-full"
  >
    <LoadingOverlay />

    <div class="flex-1 flex items-center justify-center p-4 py-8 max-w-7xl mx-auto w-full">
      <NuxtLink
        to="/login"
        class="fixed top-6 right-6 bg-slate-600 hover:bg-slate-700 text-white p-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 z-50"
        title="Iniciar Sesión"
      >
        <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
          />
        </svg>
      </NuxtLink>

      <div class="w-full relative">
        <!-- Form Container -->
        <div
          v-show="!ticketVisible"
          id="form-container"
          class="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-10 border border-slate-200"
        >
          <div class="text-center mb-10">
            <div class="inline-flex items-center justify-center w-40 h-35">
              <img src="/ual_no_fondo.png" alt="Logo UAL" class="w-full h-full object-contain" />
            </div>
            <h1 class="text-3xl font-bold text-slate-800 mb-2 mt-2">Sistema de tickets</h1>
            <p class="text-slate-600 text-base">Genera tu ticket de atención</p>
          </div>

          <div class="space-y-4">
            <label class="block text-lg font-semibold text-slate-700 mb-2 text-center">
              Departamento de Atención
            </label>
            <div id="sector-buttons" class="grid grid-cols-2 gap-4">
              <button
                v-for="sector in sectores"
                :key="sector.id"
                @click="generarTicket(sector.id, sector.nombre)"
                class="bg-gradient-to-br from-slate-600 to-emerald-600 hover:from-slate-700 hover:to-emerald-700 text-white font-bold py-5 px-4 rounded-2xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 active:scale-95"
              >
                {{ sector.nombre }}
              </button>
            </div>
          </div>
        </div>

        <!-- Ticket Result -->
        <div
          v-show="ticketVisible"
          id="ticket-result"
          class="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-10 border border-slate-200 max-w-md mx-auto"
        >
          <div class="text-center">
            <div class="mb-6">
              <div class="inline-flex items-center justify-center w-20 h-20 bg-emerald-100 rounded-full">
                <svg class="w-12 h-12 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>

            <h2 class="text-2xl font-bold text-slate-800 mb-2">Ticket Generado</h2>

            <div class="my-6">
              <span class="text-7xl font-black text-emerald-700 drop-shadow-sm">{{ ticketFolio }}</span>
            </div>

            <div class="bg-gradient-to-br from-slate-50 to-emerald-50 rounded-2xl p-6 mb-6 space-y-4 border border-slate-200">
              <div class="flex justify-between items-center py-2 border-b border-slate-200">
                <span class="text-slate-600 font-medium text-sm">Sector:</span>
                <span class="text-slate-900 font-bold text-base">{{ ticketSector }}</span>
              </div>
              <div class="flex justify-between items-center py-2">
                <span class="text-slate-600 font-medium text-sm">Fecha:</span>
                <span class="text-slate-900 font-bold text-lg">{{ ticketFecha }}</span>
              </div>
            </div>

            <p class="text-slate-600 mb-6 text-sm">Por favor, espera a que tu número sea llamado</p>

            <div class="space-y-3">
              <button
                @click="imprimir"
                class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3.5 rounded-xl transition-all duration-300 shadow-md hover:shadow-lg flex items-center justify-center gap-2 cursor-pointer"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                Imprimir Ticket
              </button>
              <button
                @click="resetForm"
                class="w-full bg-slate-600 hover:bg-slate-700 text-white font-semibold py-3.5 rounded-xl transition-all duration-300 shadow-md hover:shadow-lg cursor-pointer"
              >
                Finalizar
              </button>
            </div>
          </div>
        </div>

        <div v-if="errorMessage" class="mt-4 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-xl">
          <p>{{ errorMessage }}</p>
        </div>
      </div>

      <ClientOnly>
        <GTranslateWidget />
      </ClientOnly>
    </div>
  </div>
</template>

<script setup>
import Toastify from 'toastify-js'

definePageMeta({ layout: 'default' })

useHead({ title: 'Alumno' })

const { API_BASE_URL } = useConfig()
const socket = useSocket()

const sectores = ref([])
const ticketVisible = ref(false)
const ticketFolio = ref('')
const ticketSector = ref('')
const ticketFecha = ref('')
const errorMessage = ref('')
let lastTicketData = null

// Load sectors
const cargarSectores = async () => {
  let exito = false
  while (!exito) {
    try {
      const res = await fetch(`${API_BASE_URL}/api/sectores`, { credentials: 'include' })
      if (!res.ok) throw new Error('Servidor no listo')
      const data = await res.json()
      sectores.value = data.map((s) => ({ id: s.ID_Sector, nombre: s.Sector }))
      exito = true
    } catch (err) {
      console.error('Error cargando sectores, reintentando...', err)
      await new Promise(r => setTimeout(r, 2000))
    }
  }
}

const generarTicket = async (sectorId, sectorNombre) => {
  try {
    const res = await fetch(`${API_BASE_URL}/api/ticket`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sector: sectorNombre }),
      credentials: 'include',
    })
    const data = await res.json()

    if (res.ok) {
      ticketFolio.value = data.folio
      ticketSector.value = sectorNombre
      ticketFecha.value = new Date().toLocaleString('es-MX')
      ticketVisible.value = true
      errorMessage.value = ''
      lastTicketData = { folio: data.folio, sector: sectorNombre, id: data.id }

      Toastify({
        text: `Ticket ${data.folio} generado exitosamente`,
        duration: 3000,
        gravity: 'top',
        position: 'right',
        style: { background: 'linear-gradient(to right, #059669, #10b981)' },
      }).showToast()
    } else {
      errorMessage.value = data.error || 'Error al generar ticket'
    }
  } catch (err) {
    errorMessage.value = 'Error de conexión con el servidor'
  }
}

const imprimir = () => {
  if (!lastTicketData) return
  const printUrl = `${API_BASE_URL}/api/ticket/print`
  fetch(printUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      numero_ticket: lastTicketData.folio,
      sector: lastTicketData.sector,
      fecha: ticketFecha.value,
    }),
    credentials: 'include',
  })
    .then((res) => {
      if (res.ok) {
        Toastify({
          text: 'Ticket enviado a impresión',
          duration: 3000,
          gravity: 'top',
          position: 'right',
          style: { background: 'linear-gradient(to right, #059669, #10b981)' },
        }).showToast()
      }
    })
    .catch(() => {
      Toastify({
        text: 'Error al imprimir',
        duration: 3000,
        gravity: 'top',
        position: 'right',
        style: { background: 'linear-gradient(to right, #dc2626, #ef4444)' },
      }).showToast()
    })
}

const resetForm = () => {
  ticketVisible.value = false
  ticketFolio.value = ''
  ticketSector.value = ''
  ticketFecha.value = ''
  errorMessage.value = ''
  lastTicketData = null
}

onMounted(() => {
  cargarSectores()

  socket.on('sectores_updated', () => {
    console.log('Actualización de sectores por WebSocket')
    cargarSectores()
  })
})

onUnmounted(() => {
  socket.off('sectores_updated')
})
</script>
