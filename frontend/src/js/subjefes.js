import Config from './config.js';
import { lanzarAlerta } from './alertas/notifier.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", async () => {
    const empleadoForm = document.getElementById("empleadoForm");
    const tablaEmpleados = document.getElementById("tablaEmpleados");

    // ──────────────────────────────────────────────
    // Obtener datos del usuario logueado (Jefe)
    // ──────────────────────────────────────────────
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    if (!currentUser || currentUser.rol !== 6) {
        window.location.href = 'login.html';
        return;
    }

    const jefeNombre = currentUser.username || 'Jefe';
    const jefeSector = currentUser.sector || 'Sin Sector';
    const jefeInicial = jefeNombre.charAt(0).toUpperCase();

    // Llenar dinámicamente la UI con info del Jefe
    document.getElementById('page-subtitle').textContent = `Sector: ${jefeSector}`;
    document.getElementById('header-avatar').textContent = jefeInicial;
    document.getElementById('sidebar-avatar').textContent = jefeInicial;
    document.getElementById('sidebar-username').textContent = jefeNombre;
    document.getElementById('sidebar-sector').textContent = jefeSector;
    document.getElementById('add-sector-label').textContent = `— Sector: ${jefeSector}`;
    document.getElementById('sector-display').value = jefeSector;

    // ──────────────────────────────────────────────
    // Helper: format ventanilla name
    // ──────────────────────────────────────────────
    function formatearNombreVentanilla(nombre) {
        if (!nombre) return '';
        if (nombre.startsWith('ServiciosEscolares')) {
            const num = nombre.replace('ServiciosEscolares', '');
            return `Sev ${num}`;
        }
        return nombre;
    }

    // ──────────────────────────────────────────────
    // Helper: load ventanillas available for a role
    // ──────────────────────────────────────────────
    async function cargarVentanillasParaRol(idRol) {
        try {
            const res = await fetch(`${API_BASE_URL}/api/ventanillas/disponibles/${idRol}`);
            if (!res.ok) return [];
            return await res.json();
        } catch (err) {
            console.error("Error al cargar ventanillas:", err);
            return [];
        }
    }

    // ──────────────────────────────────────────────
    // LOAD & RENDER employees (ya filtrados por sector en backend)
    // ──────────────────────────────────────────────
    async function loadEmployees() {
        try {
            const res = await fetch(`${API_BASE_URL}/api/employees/full`);
            if (!res.ok) throw new Error("Error al cargar empleados");
            const empleados = await res.json();
            await renderEmployees(empleados);
        } catch (err) {
            console.error(err);
            lanzarAlerta("Error al cargar empleados", "error");
        }
    }

    async function renderEmployees(empleados) {
        tablaEmpleados.innerHTML = "";

        for (const emp of empleados) {
            const nombreCompleto = [
                emp.nombre1,
                emp.nombre2 || '',
                emp.Apellido1,
                emp.Apellido2 || ''
            ].filter(n => n.trim() !== '').join(' ');

            const esAdmin = emp.ID_ROL === 1;

            // ── Acciones cell ──
            const accionesCell = esAdmin
                ? `<span class="text-slate-300 text-xs italic">Sin acciones</span>`
                : `<button class="edit-btn" onclick="abrirEdicion(${emp.ID_Empleado})">Editar</button>`;

            const tr = document.createElement("tr");
            tr.className = "hover:bg-slate-50 transition-colors";
            tr.innerHTML = `
        <td class="px-6 py-3.5 text-center font-medium text-slate-500 text-sm">${emp.ID_Empleado}</td>
        <td class="px-6 py-3.5 font-medium text-slate-800 text-sm">${nombreCompleto}</td>
        <td class="px-6 py-3.5 text-slate-600 text-sm">${emp.Usuario}</td>
        <td class="px-6 py-3.5 text-slate-600 text-sm">${emp.Rol || 'N/A'}</td>
        <td class="px-6 py-3.5 text-center">${accionesCell}</td>
      `;
            tablaEmpleados.appendChild(tr);
        }
    }

    // ──────────────────────────────────────────────
    // Inline state change
    // ──────────────────────────────────────────────
    window.cambiarEstado = async function (idEmpleado, idEstado) {
        try {
            const res = await fetch(`${API_BASE_URL}/api/employees/${idEmpleado}/estado`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ estado: parseInt(idEstado) })
            });
            if (!res.ok) throw new Error("Error al cambiar estado");
            loadEmployees();
        } catch (err) {
            console.error(err);
            lanzarAlerta(err.message, "error");
        }
    };

    // ──────────────────────────────────────────────
    // Inline ventanilla assignment
    // ──────────────────────────────────────────────
    window.asignarVentanilla = async function (idEmpleado, idVentanilla) {
        try {
            const idVentNum = parseInt(idVentanilla);
            const res = await fetch(`${API_BASE_URL}/api/employees/${idEmpleado}/ventanilla`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id_ventanilla: idVentNum === 0 ? null : idVentNum })
            });
            if (!res.ok) throw new Error("Error al asignar ventanilla");
            loadEmployees();
        } catch (err) {
            console.error(err);
            lanzarAlerta(err.message, "error");
        }
    };

    // ──────────────────────────────────────────────
    // OPEN EDIT panel for a specific employee
    // ──────────────────────────────────────────────
    window.abrirEdicion = async function (idEmpleado) {
        // Open the edit accordion panel
        const content = document.getElementById('content-editar');
        const header = document.getElementById('header-editar');
        const arrow = header ? header.querySelector('.accordion-arrow') : null;
        if (content && !content.classList.contains('open')) {
            content.classList.add('open');
            if (header) header.classList.add('open');
            if (arrow) arrow.classList.add('rotate-180');
        }
        if (content) content.scrollIntoView({ behavior: 'smooth', block: 'start' });

        const container = document.getElementById('editEmpleadoContainer');
        container.innerHTML = `<p class="text-slate-400 text-sm text-center py-6">Cargando datos...</p>`;

        try {
            const res = await fetch(`${API_BASE_URL}/api/employees/full`);
            if (!res.ok) throw new Error();
            const todos = await res.json();
            const emp = todos.find(e => e.ID_Empleado === idEmpleado);
            if (!emp) throw new Error("Empleado no encontrado");

            // Determine if the employee being edited is a Jefe de Departamento
            const esJefe = emp.ID_ROL === 6;

            let locationFieldHtml = '';

            if (esJefe) {
                // Show sector (read-only for jefe editing another jefe)
                locationFieldHtml = `
          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Sector</label>
            <input type="text" value="${jefeSector}" readonly disabled
              class="w-full px-4 py-3 bg-slate-100 border border-slate-200 rounded-xl text-slate-600 font-medium cursor-not-allowed" />
          </div>
        `;
            } else {
                // Fetch ventanillas for their role
                let ventanillas = [];
                try {
                    const vRes = await fetch(`${API_BASE_URL}/api/ventanillas/disponibles/${emp.ID_ROL}?excluir_empleado=${emp.ID_Empleado}`);
                    if (vRes.ok) ventanillas = await vRes.json();
                } catch (_) { }

                const ventanillaOptions = [
                    `<option value="0" ${emp.ID_Ventanilla === null ? 'selected' : ''}>Sin ventanilla</option>`,
                    ...ventanillas.map(v =>
                        `<option value="${v.ID_Ventanilla}" ${emp.ID_Ventanilla === v.ID_Ventanilla ? 'selected' : ''}>${formatearNombreVentanilla(v.Ventanilla)}</option>`
                    )
                ].join('');

                locationFieldHtml = `
          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Ventanilla</label>
            <select id="edit-ventanilla"
              class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all appearance-none cursor-pointer font-medium">
              ${ventanillaOptions}
            </select>
          </div>
        `;
            }

            const estadoOptions = `
        <option value="1" ${emp.ID_Estado === 1 ? 'selected' : ''}>Activo</option>
        <option value="3" ${emp.ID_Estado === 3 ? 'selected' : ''}>Despedido</option>
        <option value="4" ${emp.ID_Estado === 4 ? 'selected' : ''}>Inactivo</option>
      `;

            container.innerHTML = `
        <div class="mb-6 pb-4 border-b border-slate-100 flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-700 font-bold text-lg">
            ${(emp.nombre1 || '?')[0].toUpperCase()}
          </div>
          <div>
            <p class="font-bold text-slate-800">${[emp.nombre1, emp.Apellido1].join(' ')}</p>
            <p class="text-xs text-slate-400 uppercase tracking-wider font-semibold">${emp.Rol || 'N/A'} · ID ${emp.ID_Empleado}</p>
          </div>
        </div>

        <div class="space-y-5">
          <input type="hidden" id="edit-rol-id" value="${emp.ID_ROL}">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Primer Nombre *</label>
              <input id="edit-nombre1" type="text" value="${emp.nombre1 || ''}"
                class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium"/>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Segundo Nombre</label>
              <input id="edit-nombre2" type="text" value="${emp.nombre2 || ''}" placeholder="Opcional"
                class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium"/>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Primer Apellido *</label>
              <input id="edit-apellido1" type="text" value="${emp.Apellido1 || ''}"
                class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium"/>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Segundo Apellido</label>
              <input id="edit-apellido2" type="text" value="${emp.Apellido2 || ''}" placeholder="Opcional"
                class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium"/>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Usuario *</label>
              <input id="edit-usuario" type="text" value="${emp.Usuario || ''}"
                class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium"/>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Contraseña <span class="normal-case font-normal text-slate-400">(dejar vacío para no cambiar)</span></label>
              <input id="edit-password" type="password" placeholder="••••••••"
                class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all font-medium"/>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            ${locationFieldHtml}
            <div>
              <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Estado</label>
              <select id="edit-estado"
                class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all appearance-none cursor-pointer font-medium">
                ${estadoOptions}
              </select>
            </div>
          </div>

          <div class="flex gap-3 pt-2">
            <button onclick="guardarEdicion(${emp.ID_Empleado})"
              class="flex-1 bg-amber-500 hover:bg-amber-400 text-white font-bold py-3.5 rounded-xl transition-all duration-200 shadow hover:shadow-md hover:-translate-y-0.5 active:scale-95">
              Guardar cambios
            </button>
            <button onclick="cancelarEdicion()"
              class="px-6 py-3.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold transition-all duration-200">
              Cancelar
            </button>
          </div>
        </div>
      `;
        } catch (err) {
            console.error(err);
            container.innerHTML = `<p class="text-red-500 text-sm text-center py-6">Error al cargar los datos del empleado.</p>`;
        }
    };

    // ──────────────────────────────────────────────
    // SAVE edits
    // ──────────────────────────────────────────────
    window.guardarEdicion = async function (idEmpleado) {
        const nombre1 = document.getElementById('edit-nombre1')?.value.trim();
        const nombre2 = document.getElementById('edit-nombre2')?.value.trim();
        const apellido1 = document.getElementById('edit-apellido1')?.value.trim();
        const apellido2 = document.getElementById('edit-apellido2')?.value.trim();
        const usuario = document.getElementById('edit-usuario')?.value.trim();
        const password = document.getElementById('edit-password')?.value.trim();
        const idEstado = document.getElementById('edit-estado')?.value;

        const elVentanilla = document.getElementById('edit-ventanilla');

        if (!nombre1 || !apellido1 || !usuario) {
            lanzarAlerta("Primer nombre, primer apellido y usuario son obligatorios.", "error");
            return;
        }

        if (password) {
            if (password.length < 8) {
                lanzarAlerta("La contraseña debe tener al menos 8 caracteres", "error");
                return;
            }
            if (!/[A-Z]/.test(password)) {
                lanzarAlerta("La contraseña debe contener al menos una letra mayúscula", "error");
                return;
            }
            if (!/[0-9]/.test(password)) {
                lanzarAlerta("La contraseña debe contener al menos un número", "error");
                return;
            }
        }

        try {
            // 1) Update basic data
            const bodyData = { nombre1, nombre2, apellido1, apellido2, usuario };
            if (password) bodyData.passwd = password;

            const res = await fetch(`${API_BASE_URL}/api/employees/${idEmpleado}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bodyData)
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error || "Error al actualizar empleado");
            }

            // 2) Update ventanilla IF exists
            if (elVentanilla) {
                const idVentNum = parseInt(elVentanilla.value);
                await fetch(`${API_BASE_URL}/api/employees/${idEmpleado}/ventanilla`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id_ventanilla: idVentNum === 0 ? null : idVentNum })
                });
            }

            // 3) Update estado
            if (idEstado !== undefined) {
                await fetch(`${API_BASE_URL}/api/employees/${idEmpleado}/estado`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ estado: parseInt(idEstado) })
                });
            }

            lanzarAlerta("Empleado actualizado correctamente", "success");
            cancelarEdicion();
            loadEmployees();
        } catch (err) {
            console.error(err);
            lanzarAlerta(err.message || "Error al guardar cambios", "error");
        }
    };

    // ──────────────────────────────────────────────
    // CANCEL edit — restore placeholder
    // ──────────────────────────────────────────────
    window.cancelarEdicion = function () {
        const container = document.getElementById('editEmpleadoContainer');
        container.innerHTML = `
      <div id="editPlaceholder" class="flex flex-col items-center justify-center py-10 text-slate-400">
        <svg class="w-12 h-12 mb-3 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
        <p class="font-medium text-sm">Selecciona un empleado en la lista para editarlo</p>
      </div>
    `;
    };

    // ──────────────────────────────────────────────
    // ADD employee form submit
    // El sector se asigna automáticamente al del Jefe
    // ──────────────────────────────────────────────
    empleadoForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const data = {
            nombre1: document.getElementById("nombre1").value.trim(),
            nombre2: document.getElementById("nombre2").value.trim(),
            apellido1: document.getElementById("apellido1").value.trim(),
            apellido2: document.getElementById("apellido2").value.trim(),
            usuario: document.getElementById("usuario").value.trim(),
            passwd: document.getElementById("password").value.trim(),
            id_rol: parseInt(document.getElementById("rol").value),
            // El backend forzará el sector del jefe, pero lo enviamos por consistencia
            id_sector: null
        };

        if (!data.nombre1 || !data.apellido1 || !data.usuario || !data.passwd) {
            lanzarAlerta("Por favor complete los campos obligatorios", "error");
            return;
        }

        if (!data.id_rol) {
            lanzarAlerta("Por favor seleccione un rol", "error");
            return;
        }

        const password = data.passwd;
        if (password.length < 8) {
            lanzarAlerta("La contraseña debe tener al menos 8 caracteres", "error");
            return;
        }
        if (!/[A-Z]/.test(password)) {
            lanzarAlerta("La contraseña debe contener al menos una letra mayúscula", "error");
            return;
        }
        if (!/[0-9]/.test(password)) {
            lanzarAlerta("La contraseña debe contener al menos un número", "error");
            return;
        }

        try {
            const verificarUsuario = await fetch(`${API_BASE_URL}/api/employees/exists/${encodeURIComponent(data.usuario)}`);
            const existe = await verificarUsuario.json();
            if (existe.exists) {
                lanzarAlerta("El nombre de usuario ya existe. Por favor elija otro.", "error");
                return;
            }

            const res = await fetch(`${API_BASE_URL}/api/employees/add`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });

            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.error || "No se pudo agregar empleado");
            }

            lanzarAlerta("Empleado agregado exitosamente", "success");
            empleadoForm.reset();
            document.getElementById('sector-display').value = jefeSector;
            loadEmployees();
        } catch (err) {
            console.error(err);
            lanzarAlerta(err.message || "Error al agregar empleado", "error");
        }
    });

    // ──────────────────────────────────────────────
    // Load roles for the add-employee form
    // ──────────────────────────────────────────────
    async function cargarRoles() {
        try {
            const res = await fetch(`${API_BASE_URL}/api/roles`);
            const roles = await res.json();
            const rolSelect = document.getElementById("rol");
            roles.forEach(r => {
                const opt = document.createElement("option");
                opt.value = r.ID_Rol;
                opt.textContent = r.Rol;
                rolSelect.appendChild(opt);
            });
        } catch (err) {
            console.error("Error al cargar roles:", err);
        }
    }

    // ──────────────────────────────────────────────
    // WEBSOCKET (Session Lock & Updates)
    // ──────────────────────────────────────────────
    if (typeof io !== 'undefined') {
        const socket = io(API_BASE_URL);

        socket.on('connect', () => {
            console.log('🟢 Subjefes WebSocket conectado');
            // Registrar usuario activo para mantener su sesion viva
            const storedUser = localStorage.getItem('currentUser');
            if (storedUser) {
                try {
                    const currentUser = JSON.parse(storedUser);
                    if (currentUser.id) {
                        socket.emit('ventanilla_register', { id_empleado: currentUser.id });
                    }
                } catch (e) { }
            }
        });

        socket.on('ventanilla_status_changed', () => {
            console.log('Cambio de estado en ventanilla, refrescando lista...');
            loadEmployees();
        });
    }

    // ──────────────────────────────────────────────
    // Init
    // ──────────────────────────────────────────────
    cargarRoles();
    loadEmployees();
});
