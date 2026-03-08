<template>
  <div class="p-6 md:p-10 lg:p-14 max-w-7xl mx-auto w-full flex flex-col gap-4">
    <div class="bg-white/95 backdrop-blur-sm shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl border border-white/60">
      <div class="flex flex-col sm:flex-row justify-between sm:items-center border-b border-slate-100 p-6 md:p-8 gap-4 sm:gap-0">
        <div>
          <h1 class="text-2xl sm:text-3xl font-bold text-slate-800 tracking-tight">Gestión de Empleados</h1>
          <p class="text-slate-500 mt-1 font-medium">Administra los empleados del sistema</p>
        </div>
      </div>

      <div class="p-6 md:p-8 flex flex-col gap-4">
        <!-- Panel 1: Agregar Empleado -->
        <AdminAccordionPanel id="agregar" title="Agregar Empleado" icon-bg-class="bg-emerald-100">
          <template #icon>
            <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </template>
          <div class="p-6 sm:p-8 bg-white">
            <p class="text-sm text-slate-500 mb-6 font-medium">Complete la información del nuevo empleado</p>
            <form @submit.prevent="agregarEmpleado" class="space-y-5">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Primer nombre *</label>
                  <input v-model="form.nombre1" type="text" required placeholder="Ej: Juan" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Segundo nombre</label>
                  <input v-model="form.nombre2" type="text" placeholder="Opcional" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
                </div>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Primer apellido *</label>
                  <input v-model="form.apellido1" type="text" required placeholder="Ej: Pérez" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Segundo apellido</label>
                  <input v-model="form.apellido2" type="text" placeholder="Opcional" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
                </div>
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Usuario *</label>
                <input v-model="form.usuario" type="text" required placeholder="Nombre de usuario" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Contraseña *</label>
                <input v-model="form.passwd" type="password" required placeholder="••••••••" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Rol *</label>
                  <select v-model.number="form.id_rol" required @change="onRolChange" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all appearance-none cursor-pointer font-medium">
                    <option value="">Seleccionar</option>
                    <option v-for="r in roles" :key="r.ID_Rol" :value="r.ID_Rol">{{ r.Rol }}</option>
                  </select>
                </div>
                <div v-if="form.id_rol === 6">
                  <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Sector</label>
                  <select v-model.number="form.id_sector" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all appearance-none cursor-pointer font-medium">
                    <option :value="0">Sin sector</option>
                    <option v-for="s in sectoresForm" :key="s.ID_Sector" :value="s.ID_Sector" :disabled="s.ocupado">{{ s.Sector }}{{ s.ocupado ? ' (Ocupado)' : '' }}</option>
                  </select>
                </div>
              </div>
              <button type="submit" class="w-full bg-slate-800 hover:bg-slate-700 text-white font-bold py-3.5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:-translate-y-0.5 mt-6 active:scale-95">Agregar empleado</button>
            </form>
          </div>
        </AdminAccordionPanel>

        <!-- Panel 2: Lista -->
        <AdminAccordionPanel id="lista" title="Lista de Empleados" icon-bg-class="bg-sky-100" :default-open="true">
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
                  <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs">Nombre</th>
                  <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs">Usuario</th>
                  <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs">Rol</th>
                  <th class="px-6 py-4 font-bold text-slate-600 uppercase tracking-wider text-xs text-center">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="emp in empleados" :key="emp.ID_Empleado" class="hover:bg-slate-50 transition-colors">
                  <td class="px-6 py-3.5 text-center font-medium text-slate-500 text-sm">{{ emp.ID_Empleado }}</td>
                  <td class="px-6 py-3.5 font-medium text-slate-800 text-sm">{{ nombreCompleto(emp) }}</td>
                  <td class="px-6 py-3.5 text-slate-600 text-sm">{{ emp.Usuario }}</td>
                  <td class="px-6 py-3.5 text-slate-600 text-sm">{{ emp.Rol || 'N/A' }}</td>
                  <td class="px-6 py-3.5 text-center">
                    <span v-if="emp.ID_ROL === 1" class="text-slate-300 text-xs italic">Sin acciones</span>
                    <span v-else-if="activosSet.has(emp.ID_Empleado)" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-green-100 text-green-700 border border-green-200">
                      <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span> En ventanilla
                    </span>
                    <button v-else class="edit-btn" @click="abrirEdicion(emp.ID_Empleado)">Editar</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </AdminAccordionPanel>

        <!-- Panel 3: Editar Empleado -->
        <AdminAccordionPanel ref="editAccordion" id="editar" title="Editar Empleado" icon-bg-class="bg-amber-100">
          <template #icon>
            <svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536M9 13l6.586-6.586a2 2 0 012.828 2.828L11.828 15.828a4 4 0 01-1.414.943l-3 1 1-3a4 4 0 01.943-1.414z" />
            </svg>
          </template>
          <div class="p-6 sm:p-8 bg-white">
            <div v-if="!editEmpleado" class="flex flex-col items-center justify-center py-10 text-slate-400">
              <svg class="w-12 h-12 mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              <p class="font-medium text-sm">Selecciona un empleado en la lista para editarlo</p>
            </div>
            <div v-else>
              <div class="mb-6 pb-4 border-b border-slate-100 flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-700 font-bold text-lg">{{ (editEmpleado.nombre1 || '?')[0].toUpperCase() }}</div>
                <div>
                  <p class="font-bold text-slate-800">{{ editEmpleado.nombre1 }} {{ editEmpleado.Apellido1 }}</p>
                  <p class="text-xs text-slate-400 uppercase tracking-wider font-semibold">{{ editEmpleado.Rol || 'N/A' }} · ID {{ editEmpleado.ID_Empleado }}</p>
                </div>
              </div>
              <div class="space-y-5">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div><label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Primer Nombre *</label><input v-model="editForm.nombre1" type="text" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium" /></div>
                  <div><label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Segundo Nombre</label><input v-model="editForm.nombre2" type="text" placeholder="Opcional" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium" /></div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div><label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Primer Apellido *</label><input v-model="editForm.apellido1" type="text" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium" /></div>
                  <div><label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Segundo Apellido</label><input v-model="editForm.apellido2" type="text" placeholder="Opcional" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium" /></div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div><label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Usuario *</label><input v-model="editForm.usuario" type="text" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium" /></div>
                  <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Contraseña <span class="normal-case font-normal text-slate-400">(dejar vacío para no cambiar)</span></label>
                    <input v-model="editForm.password" type="password" placeholder="••••••••" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium" />
                  </div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div v-if="editEmpleado.ID_ROL === 6">
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Sector</label>
                    <select v-model.number="editForm.sector" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all appearance-none cursor-pointer font-medium">
                      <option :value="0">Sin sector</option>
                      <option v-for="s in editSectoresDisp" :key="s.ID_Sector" :value="s.ID_Sector" :disabled="s.ocupado && s.ID_Sector !== editEmpleado.ID_Sector_Jefe">{{ s.Sector }}{{ s.ocupado && s.ID_Sector !== editEmpleado.ID_Sector_Jefe ? ' (Ocupado)' : '' }}</option>
                    </select>
                  </div>
                  <div v-else>
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Ventanilla</label>
                    <select v-model.number="editForm.ventanilla" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all appearance-none cursor-pointer font-medium">
                      <option :value="0">Sin ventanilla</option>
                      <option v-for="v in editVentanillasDisp" :key="v.ID_Ventanilla" :value="v.ID_Ventanilla">{{ v.Ventanilla }}</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Estado</label>
                    <select v-model.number="editForm.estado" class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all appearance-none cursor-pointer font-medium">
                      <option :value="1">Activo</option>
                      <option :value="3">Despedido</option>
                      <option :value="4">Inactivo</option>
                    </select>
                  </div>
                </div>
                <div class="flex gap-3 pt-2">
                  <button @click="guardarEdicion" class="flex-1 bg-amber-500 hover:bg-amber-400 text-white font-bold py-3.5 rounded-xl transition-all duration-200 shadow hover:shadow-md hover:-translate-y-0.5 active:scale-95">Guardar cambios</button>
                  <button @click="cancelarEdicion" class="px-6 py-3.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold transition-all duration-200">Cancelar</button>
                </div>
              </div>
            </div>
          </div>
        </AdminAccordionPanel>
      </div>
    </div>
  </div>
</template>

<script setup>
import { io } from 'socket.io-client'

definePageMeta({ layout: 'admin', middleware: 'auth' })
useHead({ title: 'Administración — Empleados' })

const { API_BASE_URL } = useConfig()
const { lanzarAlerta } = useToast()

const empleados = ref([])
const activosSet = ref(new Set())
const roles = ref([])
const sectoresForm = ref([])
const editAccordion = ref(null)

// Add form
const form = reactive({ nombre1: '', nombre2: '', apellido1: '', apellido2: '', usuario: '', passwd: '', id_rol: '', id_sector: 0 })

// Edit
const editEmpleado = ref(null)
const editForm = reactive({ nombre1: '', nombre2: '', apellido1: '', apellido2: '', usuario: '', password: '', ventanilla: 0, sector: 0, estado: 1 })
const editVentanillasDisp = ref([])
const editSectoresDisp = ref([])

let socket = null

const nombreCompleto = (emp) => [emp.nombre1, emp.nombre2 || '', emp.Apellido1, emp.Apellido2 || ''].filter(n => n.trim() !== '').join(' ')

async function loadEmployees() {
  try {
    const [empRes, activosRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/employees/full`),
      fetch(`${API_BASE_URL}/api/employees/activos`)
    ])
    if (!empRes.ok) throw new Error()
    empleados.value = await empRes.json()
    const activos = activosRes.ok ? await activosRes.json() : []
    activosSet.value = new Set(activos)
  } catch { lanzarAlerta('Error al cargar empleados', 'error') }
}

async function cargarRoles() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/roles`)
    const data = await res.json()
    roles.value = data.filter(r => r.ID_Rol !== 1)
  } catch {}
}

async function onRolChange() {
  if (form.id_rol === 6) {
    const [sectores, ocupados] = await Promise.all([
      fetch(`${API_BASE_URL}/api/sectores`).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/sectores/ocupados`).then(r => r.ok ? r.json() : [])
    ])
    const ocSet = new Set(ocupados)
    sectoresForm.value = sectores.map(s => ({ ...s, ocupado: ocSet.has(s.ID_Sector) }))
  }
}

async function agregarEmpleado() {
  if (!form.nombre1 || !form.apellido1 || !form.usuario || !form.passwd) { lanzarAlerta('Complete los campos obligatorios', 'error'); return }
  if (form.passwd.length < 8) { lanzarAlerta('La contraseña debe tener al menos 8 caracteres', 'error'); return }
  if (!/[A-Z]/.test(form.passwd)) { lanzarAlerta('La contraseña debe contener al menos una mayúscula', 'error'); return }
  if (!/[0-9]/.test(form.passwd)) { lanzarAlerta('La contraseña debe contener al menos un número', 'error'); return }

  try {
    const existsRes = await fetch(`${API_BASE_URL}/api/employees/exists/${encodeURIComponent(form.usuario)}`)
    const exists = await existsRes.json()
    if (exists.exists) { lanzarAlerta('El usuario ya existe', 'error'); return }

    const body = { ...form, id_sector: form.id_rol === 6 ? (form.id_sector || null) : null }
    const res = await fetch(`${API_BASE_URL}/api/employees/add`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (!res.ok) { const e = await res.json(); throw new Error(e.error) }
    lanzarAlerta('Empleado agregado exitosamente', 'success')
    Object.assign(form, { nombre1: '', nombre2: '', apellido1: '', apellido2: '', usuario: '', passwd: '', id_rol: '', id_sector: 0 })
    loadEmployees()
  } catch (err) { lanzarAlerta(err.message || 'Error', 'error') }
}

async function abrirEdicion(id) {
  try {
    const activosRes = await fetch(`${API_BASE_URL}/api/employees/activos`)
    if (activosRes.ok) {
      const activos = await activosRes.json()
      if (activos.includes(id)) { lanzarAlerta('No se puede editar, el empleado está en ventanilla', 'warning'); return }
    }
  } catch {}

  editAccordion.value?.open()

  try {
    const res = await fetch(`${API_BASE_URL}/api/employees/full`)
    const todos = await res.json()
    const emp = todos.find(e => e.ID_Empleado === id)
    if (!emp) throw new Error('No encontrado')
    editEmpleado.value = emp
    Object.assign(editForm, { nombre1: emp.nombre1 || '', nombre2: emp.nombre2 || '', apellido1: emp.Apellido1 || '', apellido2: emp.Apellido2 || '', usuario: emp.Usuario || '', password: '', ventanilla: emp.ID_Ventanilla || 0, sector: emp.ID_Sector_Jefe || 0, estado: emp.ID_Estado || 1 })

    if (emp.ID_ROL === 6) {
      const [sectores, ocupados] = await Promise.all([
        fetch(`${API_BASE_URL}/api/sectores`).then(r => r.json()),
        fetch(`${API_BASE_URL}/api/sectores/ocupados`).then(r => r.ok ? r.json() : [])
      ])
      const ocSet = new Set(ocupados)
      editSectoresDisp.value = sectores.map(s => ({ ...s, ocupado: ocSet.has(s.ID_Sector) }))
    } else {
      const vRes = await fetch(`${API_BASE_URL}/api/ventanillas/disponibles/${emp.ID_ROL}?excluir_empleado=${emp.ID_Empleado}`)
      editVentanillasDisp.value = vRes.ok ? await vRes.json() : []
    }
  } catch { lanzarAlerta('Error al cargar datos', 'error') }
}

async function guardarEdicion() {
  if (!editEmpleado.value) return
  const id = editEmpleado.value.ID_Empleado
  if (!editForm.nombre1 || !editForm.apellido1 || !editForm.usuario) { lanzarAlerta('Campos obligatorios', 'error'); return }
  if (editForm.password) {
    if (editForm.password.length < 8) { lanzarAlerta('Mínimo 8 caracteres', 'error'); return }
    if (!/[A-Z]/.test(editForm.password)) { lanzarAlerta('Necesita una mayúscula', 'error'); return }
    if (!/[0-9]/.test(editForm.password)) { lanzarAlerta('Necesita un número', 'error'); return }
  }
  try {
    const body = { nombre1: editForm.nombre1, nombre2: editForm.nombre2, apellido1: editForm.apellido1, apellido2: editForm.apellido2, usuario: editForm.usuario }
    if (editForm.password) body.passwd = editForm.password
    let res = await fetch(`${API_BASE_URL}/api/employees/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (!res.ok) { const e = await res.json(); throw new Error(e.error) }

    if (editEmpleado.value.ID_ROL === 6) {
      await fetch(`${API_BASE_URL}/api/employees/${id}/sector`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id_sector: editForm.sector === 0 ? null : editForm.sector }) })
    } else {
      await fetch(`${API_BASE_URL}/api/employees/${id}/ventanilla`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id_ventanilla: editForm.ventanilla === 0 ? null : editForm.ventanilla }) })
    }
    await fetch(`${API_BASE_URL}/api/employees/${id}/estado`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ estado: editForm.estado }) })

    lanzarAlerta('Empleado actualizado correctamente', 'success')
    cancelarEdicion()
    loadEmployees()
  } catch (err) { lanzarAlerta(err.message || 'Error', 'error') }
}

function cancelarEdicion() { editEmpleado.value = null }

onMounted(() => {
  loadEmployees()
  cargarRoles()

  socket = io(API_BASE_URL, { transports: ['websocket', 'polling'], rejectUnauthorized: false })
  socket.on('connect', () => {
    const u = JSON.parse(localStorage.getItem('currentUser') || 'null')
    if (u?.id) socket.emit('ventanilla_register', { id_empleado: u.id })
  })
  socket.on('ventanilla_status_changed', () => loadEmployees())
})
onUnmounted(() => { if (socket) socket.disconnect() })
</script>

<style scoped>
.edit-btn { padding: 4px 12px; font-size: 0.75rem; font-weight: 600; border-radius: 8px; background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; cursor: pointer; transition: background 0.15s, color 0.15s; }
.edit-btn:hover { background: #e0f2fe; color: #0369a1; border-color: #7dd3fc; }
</style>
