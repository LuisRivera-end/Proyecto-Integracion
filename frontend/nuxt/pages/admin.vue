<template>
  <div class="p-6 md:p-10 lg:p-14 max-w-7xl mx-auto w-full flex flex-col items-center">
    <!-- Gestión de Departamentos -->
    <div class="w-full mt-8 bg-white/95 backdrop-blur-sm shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl border border-white/60">
      <div class="flex flex-col sm:flex-row justify-between sm:items-center border-b border-slate-100 p-6 md:p-8 gap-4 sm:gap-0">
        <div>
          <h1 class="text-2xl sm:text-3xl font-bold text-slate-800 tracking-tight">Gestión de Departamentos</h1>
          <p class="text-slate-500 mt-1 font-medium">Administra los departamentos del sistema</p>
        </div>
      </div>

      <!-- Accordion Panels Container -->
      <div class="p-6 md:p-8 flex flex-col gap-4">

        <!-- Panel 1: Agregar Departamento -->
        <AdminAccordionPanel id="agregar" title="Agregar Departamento" icon-bg-class="bg-emerald-100">
          <template #icon>
            <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </template>
          <div class="p-6 sm:p-8 bg-white">
            <p class="text-sm text-slate-500 mb-6 font-medium">Ingrese el nombre del nuevo departamento</p>
            <form @submit.prevent="agregarSector" class="space-y-5">
              <div>
                <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Nombre del departamento *</label>
                <input v-model="nuevoNombre" type="text" required placeholder="Ej: Recursos Humanos"
                  class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Cantidad de ventanillas *</label>
                <input v-model.number="nuevaVentanillas" type="number" required min="1" max="5" placeholder="Ej: 4"
                  class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
              </div>
              <button type="submit"
                class="w-full bg-slate-800 hover:bg-slate-700 text-white font-bold py-3.5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:-translate-y-0.5 mt-2 active:scale-95">
                Agregar departamento
              </button>
            </form>
          </div>
        </AdminAccordionPanel>

        <!-- Panel 2: Lista de Departamentos -->
        <AdminAccordionPanel id="lista" title="Departamentos Existentes" icon-bg-class="bg-sky-100" :default-open="true">
          <template #icon>
            <svg class="w-4 h-4 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
          </template>
          <div class="bg-white overflow-x-auto">
            <table class="w-full text-sm text-left">
              <thead class="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs text-center">#</th>
                  <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs">Nombre del Departamento</th>
                  <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs text-center">Ventanillas</th>
                  <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs text-center">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-if="sectores.length === 0">
                  <td colspan="4" class="px-6 py-8 text-center text-slate-400 text-sm font-medium">No hay departamentos registrados</td>
                </tr>
                <tr v-for="(s, idx) in sectores" :key="s.ID_Sector" class="hover:bg-slate-50 transition-colors">
                  <td class="px-6 py-3.5 text-center font-medium text-slate-500 text-sm">{{ idx + 1 }}</td>
                  <td class="px-6 py-3.5 font-medium text-slate-800 text-sm">{{ s.Sector }}</td>
                  <td class="px-6 py-3.5 text-center font-medium text-slate-600 text-sm">{{ s.Ventanillas }}</td>
                  <td class="px-6 py-3.5 text-center">
                    <button class="edit-btn" @click="editarSector(s.ID_Sector, s.Sector, s.Ventanillas)">Editar</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </AdminAccordionPanel>

        <!-- Panel 3: Editar Departamento -->
        <AdminAccordionPanel ref="editAccordion" id="editar" title="Editar Departamento" icon-bg-class="bg-amber-100">
          <template #icon>
            <svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15.232 5.232l3.536 3.536M9 13l6.586-6.586a2 2 0 012.828 2.828L11.828 15.828a4 4 0 01-1.414.943l-3 1 1-3a4 4 0 01.943-1.414z" />
            </svg>
          </template>
          <div class="p-6 sm:p-8 bg-white">
            <div v-if="!editando" class="flex flex-col items-center justify-center py-10 text-slate-400">
              <svg class="w-12 h-12 mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <p class="font-medium text-sm">Selecciona un departamento en la lista para editarlo</p>
            </div>

            <!-- Edit form -->
            <form v-if="editando" @submit.prevent="guardarEdicion" class="space-y-5">
              <p class="text-sm text-slate-500 mb-2 font-medium">Editando: <strong>{{ editNombreOriginal }}</strong></p>

              <div>
                <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Nombre del departamento *</label>
                <input v-model="editNombre" type="text" required
                  class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
              </div>

              <!-- Caja Rápida toggle (solo para Cajas) -->
              <div v-if="esSectorCajas" class="mt-6 mb-2">
                <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Modo Caja Rápida</label>
                <div class="rounded-xl border border-amber-200 bg-amber-50 p-5">
                  <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
                        <svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                      </div>
                      <span class="font-bold text-slate-700 text-sm">Caja Rápida</span>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" v-model="cajaRapidaActiva" class="sr-only peer">
                      <div class="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-amber-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
                    </label>
                  </div>
                  
                  <div v-if="cajaRapidaActiva" class="space-y-3 mt-4 border-t border-amber-200/60 pt-4">
                    <div class="relative group">
                      <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
                        Hora de finalización *
                      </label>
                      <input 
                        v-model="cajaRapidaHoraFin"
                        type="time"
                        class="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all font-medium"
                      />
                      <div class="absolute left-0 -bottom-8 hidden group-hover:block bg-slate-800 text-white text-xs px-2 py-1 rounded shadow z-10">
                        Selecciona hora y minutos de finalización Ejemplo: 03:30 PM
                      </div>
                    </div>
                    
                    <div>
                      <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Selecciona las ventanillas *</label>
                      <div class="space-y-2 max-h-40 overflow-y-auto">
                        <div v-for="v in editVentanillas" :key="v.ID_Ventanilla" 
                          :class="['flex items-center gap-2 rounded-lg px-3 py-2 border transition-colors', v.Activa === 1 ? 'bg-white border-slate-200' : 'bg-slate-100 border-slate-200 opacity-60']">
                          <input type="checkbox" :id="'cr-v-'+v.ID_Ventanilla" :value="v.ID_Ventanilla" v-model="cajaRapidaVentanillasSeleccionadas"
                            class="w-4 h-4 text-amber-500 border-gray-300 rounded focus:ring-amber-400"
                            :disabled="v.Activa !== 1">
                          <label :for="'cr-v-'+v.ID_Ventanilla" 
                            :class="['text-sm font-medium cursor-pointer flex-1', v.Activa === 1 ? 'text-slate-700' : 'text-slate-400 cursor-not-allowed']">
                            {{ v.Ventanilla }} {{ v.Activa !== 1 ? '(Inactiva)' : '' }}
                          </label>
                        </div>
                      </div>
                    </div>
                    
                    <p v-if="cajaRapidaMensajeEstado" class="text-xs text-amber-700 font-medium">{{ cajaRapidaMensajeEstado }}</p>
                    
                    <button type="button" @click="guardarAccionCajaRapida"
                      :class="['w-full text-white font-bold py-2.5 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg text-sm mt-3', currentEstadoCajaRapida ? 'bg-red-500 hover:bg-red-600' : 'bg-amber-500 hover:bg-amber-600']">
                      {{ currentEstadoCajaRapida ? 'Desactivar Caja Rápida' : 'Activar Caja Rápida' }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- Ventanillas Table -->
              <div>
                <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Ventanillas del departamento</label>
                <div class="rounded-xl border border-slate-200 overflow-hidden">
                  <table class="w-full text-sm">
                    <thead class="bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Nombre</th>
                        <th class="px-4 py-3 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Estado</th>
                        <th class="px-4 py-3 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Acción</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                      <tr v-for="v in editVentanillas" :key="v.ID_Ventanilla"
                        :class="['transition-colors', v.Activa === 1 ? 'hover:bg-slate-50' : 'bg-slate-100/60']">
                        <td class="px-4 py-3">
                          <input v-model="v.nuevoNombre" type="text"
                            :disabled="!!v.nombre_empleado"
                            :title="v.nombre_empleado ? 'En uso por un empleado: ' + v.nombre_empleado : ''"
                            :class="[
                              'w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all',
                              v.Activa !== 1 ? 'opacity-50' : '',
                              v.nombre_empleado ? 'opacity-50 cursor-not-allowed bg-slate-50' : ''
                            ]" />
                        </td>
                        <td class="px-4 py-3 text-center">
                          <span :class="[
                            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold',
                            v.Activa === 1 ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' : 'bg-red-100 text-red-700 border border-red-200'
                          ]">
                            <span :class="['w-1.5 h-1.5 rounded-full', v.Activa === 1 ? 'bg-emerald-500' : 'bg-red-500']"></span>
                            {{ v.Activa === 1 ? 'Activa' : 'Inactiva' }}
                          </span>
                          <p v-if="v.nombre_empleado" class="text-[11px] text-slate-400 mt-1 font-medium">{{ v.nombre_empleado }}</p>
                        </td>
                        <td class="px-4 py-3 text-center">
                          <button type="button"
                            :disabled="v.nombre_empleado && v.Activa === 1"
                            @click="toggleVentanilla(v)"
                            :class="[
                              'px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-200',
                              v.Activa === 1
                                ? (v.nombre_empleado
                                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
                                    : 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 hover:border-red-300 active:scale-95')
                                : 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-200 hover:border-emerald-300 active:scale-95'
                            ]">
                            {{ v.Activa === 1 ? 'Deshabilitar' : 'Habilitar' }}
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div class="flex gap-3">
                <button type="submit" :disabled="guardando"
                  class="flex-1 bg-slate-800 hover:bg-slate-700 text-white font-bold py-3.5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:scale-95">
                  {{ guardando ? 'Guardando...' : 'Guardar cambios' }}
                </button>
                <button type="button" @click="cancelarEdicion"
                  class="px-6 bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold py-3.5 rounded-xl transition-all duration-200">
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </AdminAccordionPanel>

      </div>
    </div>
  </div>
</template>

<script setup>

definePageMeta({ layout: 'admin', middleware: 'auth' })
useHead({ title: 'Administrador — Departamentos' })

const { API_BASE_URL } = useConfig()
const { lanzarAlerta } = useToast()
const socket = useSocket()
const { getCurrentUser, getSessionToken } = useAuth()

// Sector list
const sectores = ref([])

// Add form
const nuevoNombre = ref('')
const nuevaVentanillas = ref(1)

// Edit form
const editando = ref(false)
const editSectorId = ref(null)
const editNombre = ref('')
const editNombreOriginal = ref('')
const editVentanillas = ref([])
const guardando = ref(false)
const editAccordion = ref(null)

// --- Caja Rapida ---
const esSectorCajas = computed(() => editNombreOriginal.value?.trim().toLowerCase() === 'cajas')
const cajaRapidaActiva = ref(false)
const currentEstadoCajaRapida = ref(false)
const cajaRapidaHoraFin = ref('')
const cajaRapidaVentanillasSeleccionadas = ref([])
const cajaRapidaMensajeEstado = ref('')




onMounted(() => {
  cargarSectores()

  socket.on('connect', () => {
    console.log('🟢 Departamentos WebSocket conectado')
    const currentUser = getCurrentUser()
    if (currentUser?.id) socket.emit('ventanilla_register', { id_empleado: currentUser.id, session_token: getSessionToken() })
  })

  socket.on('ventanilla_status_changed', () => {
    if (editSectorId.value) refreshVentanillas()
  })

  socket.on('sectores_updated', () => {
    cargarSectores()
    if (editSectorId.value) refreshVentanillas()
  })

  socket.on('caja_rapida_updated', () => {
    if (editSectorId.value && esSectorCajas.value) {
      cargarEstadoCajaRapida()
    }
  })



  // Semester cleanup
  verificarLimpiezaSemestral()
})

onUnmounted(() => {
  socket.off('ventanilla_status_changed')
  socket.off('sectores_updated')
  socket.off('caja_rapida_updated')

})

// Load sectors
async function cargarSectores() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/sectores`)
    if (!res.ok) throw new Error('Error al cargar departamentos')
    sectores.value = await res.json()
  } catch (err) {
    console.error(err)
    lanzarAlerta('Error al cargar departamentos', 'error')
  }
}

// Add sector
async function agregarSector() {
  if (!nuevoNombre.value.trim()) {
    lanzarAlerta('El nombre del departamento es obligatorio', 'error')
    return
  }
  try {
    const res = await fetch(`${API_BASE_URL}/api/sectores`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sector: nuevoNombre.value.trim(), ventanillas: nuevaVentanillas.value || 1 }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'No se pudo agregar')
    lanzarAlerta('Departamento agregado exitosamente', 'success')
    nuevoNombre.value = ''
    nuevaVentanillas.value = 1
    cargarSectores()
  } catch (err) {
    lanzarAlerta(err.message || 'Error al agregar departamento', 'error')
  }
}

// Edit sector
async function editarSector(id, nombre) {
  editSectorId.value = id
  editNombre.value = nombre
  editNombreOriginal.value = nombre
  editando.value = true

  // Open accordion
  editAccordion.value?.open()

  try {
    const res = await fetch(`${API_BASE_URL}/api/sectores/${id}/ventanillas`)
    if (!res.ok) throw new Error('Error al cargar ventanillas')
    const data = await res.json()
    editVentanillas.value = data.map(v => ({ ...v, nuevoNombre: v.Ventanilla }))
    
    // Check if es sector cajas
    if (nombre.trim().toLowerCase() === 'cajas') {
      await cargarEstadoCajaRapida()
    }
  } catch (err) {
    lanzarAlerta('Error al cargar ventanillas', 'error')
    editVentanillas.value = []
  }
}

async function refreshVentanillas() {
  if (!editSectorId.value) return
  try {
    const res = await fetch(`${API_BASE_URL}/api/sectores/${editSectorId.value}/ventanillas`)
    if (!res.ok) return
    const data = await res.json()
    editVentanillas.value = data.map(v => ({ ...v, nuevoNombre: v.Ventanilla }))
  } catch {}
}

async function toggleVentanilla(v) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/ventanillas/${v.ID_Ventanilla}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ activa: v.Activa === 1 ? 0 : 1 }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Error')
    lanzarAlerta(data.message, 'success')
    // Se deja que el socket recargue las ventanillas
  } catch (err) {
    lanzarAlerta(err.message || 'Error al cambiar estado', 'error')
  }
}

async function cargarEstadoCajaRapida() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/caja-rapida/estado`)
    const estado = await res.json()

    if (estado.activo && estado.id_sector === editSectorId.value) {
      cajaRapidaActiva.value = true
      currentEstadoCajaRapida.value = true
      cajaRapidaHoraFin.value = estado.hora_fin || ''
      cajaRapidaVentanillasSeleccionadas.value = estado.ventanillas || []
      const count = (estado.ventanillas || []).length
      cajaRapidaMensajeEstado.value = `Activo desde ${estado.hora_inicio} hasta ${estado.hora_fin} (${count} ventanilla${count !== 1 ? 's' : ''})`
    } else {
      cajaRapidaActiva.value = false
      currentEstadoCajaRapida.value = false
      cajaRapidaHoraFin.value = ''
      cajaRapidaVentanillasSeleccionadas.value = []
      cajaRapidaMensajeEstado.value = ''
    }
  } catch (err) {
    console.error('Error al cargar estado Caja Rápida:', err)
  }
}

async function guardarAccionCajaRapida() {
  try {
    if (currentEstadoCajaRapida.value) {
      // Desactivar
      const res = await fetch(`${API_BASE_URL}/api/caja-rapida/desactivar`, { method: 'POST' })
      if (res.ok) {
        lanzarAlerta('Caja Rápida desactivada', 'success')
        await cargarEstadoCajaRapida()
      }
    } else {
      // Activar
      if (!cajaRapidaHoraFin.value) {
        lanzarAlerta('Debes ingresar la hora de finalización', 'error')
        return
      }
      
      const ahora = new Date()
      const [h, m] = cajaRapidaHoraFin.value.split(':').map(Number)
      const horaFinDate = new Date()
      horaFinDate.setHours(h, m, 0, 0)
      if (horaFinDate <= ahora) {
        lanzarAlerta('La hora de finalización ya pasó. Selecciona una hora futura.', 'error')
        return
      }
      if (cajaRapidaVentanillasSeleccionadas.value.length === 0) {
        lanzarAlerta('Debes seleccionar al menos una ventanilla', 'error')
        return
      }
      
      const res = await fetch(`${API_BASE_URL}/api/caja-rapida/activar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          id_sector: editSectorId.value, 
          hora_fin: cajaRapidaHoraFin.value, 
          ventanillas: cajaRapidaVentanillasSeleccionadas.value 
        })
      })
      if (res.ok) {
        lanzarAlerta('Caja Rápida activada', 'success')
        await cargarEstadoCajaRapida()
      } else {
        const data = await res.json()
        lanzarAlerta(data.error || 'Error al activar', 'error')
      }
    }
  } catch (err) {
    lanzarAlerta('Error de conexión', 'error')
    console.error(err)
  }
}

async function guardarEdicion() {
  if (!editNombre.value.trim()) {
    lanzarAlerta('El nombre del departamento es obligatorio', 'error')
    return
  }
  guardando.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/api/sectores/${editSectorId.value}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sector: editNombre.value.trim() }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'No se pudo actualizar')

    // Save ventanilla name changes
    const renameErrors = []
    for (const v of editVentanillas.value) {
      if (v.nuevoNombre && v.nuevoNombre !== v.Ventanilla) {
        try {
          const resV = await fetch(`${API_BASE_URL}/api/ventanillas/${v.ID_Ventanilla}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre: v.nuevoNombre }),
          })
          const dataV = await resV.json()
          if (!resV.ok) renameErrors.push(`${v.Ventanilla}: ${dataV.error}`)
        } catch (err) {
          renameErrors.push(`${v.Ventanilla}: ${err.message}`)
        }
      }
    }

    if (renameErrors.length > 0) {
      lanzarAlerta(`Departamento actualizado. Errores al renombrar: ${renameErrors.join(', ')}`, 'warning')
    } else {
      lanzarAlerta('Departamento actualizado correctamente', 'success')
    }
    cancelarEdicion()
    cargarSectores()
  } catch (err) {
    lanzarAlerta(err.message || 'Error al actualizar', 'error')
  } finally {
    guardando.value = false
  }
}

function cancelarEdicion() {
  editando.value = false
  editSectorId.value = null
  editNombre.value = ''
  editNombreOriginal.value = ''
  editVentanillas.value = []
}

// Semester cleanup
async function verificarLimpiezaSemestral() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/reporte/limpieza-semestral`)
    if (response.status === 204) return
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'reporte_semestral_limpieza.pdf'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    }
  } catch {}
}
</script>

<style scoped>
.edit-btn {
  padding: 4px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 8px;
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.edit-btn:hover {
  background: #e0f2fe;
  color: #0369a1;
  border-color: #7dd3fc;
}
</style>
