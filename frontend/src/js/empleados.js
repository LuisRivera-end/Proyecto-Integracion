import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", async () => {
  const empleadoForm = document.getElementById("empleadoForm");
  const tablaEmpleados = document.getElementById("tablaEmpleados");

  // ──────────────────────────────────────────────
  // Helper: CSS classes for estado badge/select
  // ──────────────────────────────────────────────
  function getEstadoClass(idEstado) {
    switch (idEstado) {
      case 1: return 'bg-green-100 text-green-800 border-green-200';   // Activo
      case 2: return 'bg-yellow-100 text-yellow-800 border-yellow-200'; // Descanso
      case 3: return 'bg-red-100 text-red-800 border-red-200';          // Despedido
      case 4: return 'bg-gray-100 text-gray-600 border-gray-200';       // Inactivo
      default: return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  }

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
  // Cache: sectores
  // ──────────────────────────────────────────────
  let cachedSectores = null;
  async function obtenerSectores() {
    if (cachedSectores) return cachedSectores;
    try {
      const res = await fetch(`${API_BASE_URL}/api/sectores`);
      cachedSectores = await res.json();
      return cachedSectores;
    } catch (err) {
      console.error("Error al cargar sectores:", err);
      return [];
    }
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
  // LOAD & RENDER employees
  // ──────────────────────────────────────────────
  async function loadEmployees() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees/full`);
      if (!res.ok) throw new Error("Error al cargar empleados");
      const empleados = await res.json();
      await renderEmployees(empleados);
    } catch (err) {
      console.error(err);
      alert("Error al cargar empleados");
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
  // Inline state change (from table select)
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
      alert(err.message);
    }
  };

  // ──────────────────────────────────────────────
  // Inline ventanilla assignment (from table select)
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
      alert(err.message);
    }
  };

  // ──────────────────────────────────────────────
  // Inline sector assignment (from table select)
  // ──────────────────────────────────────────────
  window.asignarSector = async function (idEmpleado, idSector) {
    if (idSector === undefined || idSector === null) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees/${idEmpleado}/sector`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_sector: idSector === "0" ? null : parseInt(idSector) })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Error al asignar sector");
      loadEmployees();
    } catch (err) {
      console.error(err);
      alert(err.message);
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

      // Determine if Jefe de Departamento (Rol 6)
      const esJefe = emp.ID_ROL === 6;

      let locationFieldHtml = '';

      if (esJefe) {
        // Fetch sectors
        const sectores = await obtenerSectores();
        const sectorOptions = [
          `<option value="0" ${emp.ID_Sector_Jefe === null ? 'selected' : ''}>Sin sector</option>`,
          ...sectores.map(s =>
            `<option value="${s.ID_Sector}" ${emp.ID_Sector_Jefe === s.ID_Sector ? 'selected' : ''}>${s.Sector}</option>`
          )
        ].join('');

        locationFieldHtml = `
          <div>
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Sector</label>
            <select id="edit-sector"
              class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all appearance-none cursor-pointer font-medium">
              ${sectorOptions}
            </select>
          </div>
        `;
      } else {
        // Fetch ventanillas for their role (Operador, etc)
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

    // Check fields based on existence
    const elVentanilla = document.getElementById('edit-ventanilla');
    const elSector = document.getElementById('edit-sector');

    if (!nombre1 || !apellido1 || !usuario) {
      alert("Primer nombre, primer apellido y usuario son obligatorios.");
      return;
    }

    if (password) {
      if (password.length < 8) {
        alert("La contraseña debe tener al menos 8 caracteres");
        return;
      }
      if (!/[A-Z]/.test(password)) {
        alert("La contraseña debe contener al menos una letra mayúscula");
        return;
      }
      if (!/[0-9]/.test(password)) {
        alert("La contraseña debe contener al menos un número");
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

      // 2b) Update Sector IF exists
      if (elSector) {
        const idSecNum = parseInt(elSector.value);
        await fetch(`${API_BASE_URL}/api/employees/${idEmpleado}/sector`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id_sector: idSecNum === 0 ? null : idSecNum })
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

      alert("Empleado actualizado correctamente");
      cancelarEdicion();
      loadEmployees();
    } catch (err) {
      console.error(err);
      alert(err.message || "Error al guardar cambios");
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
      id_sector: document.getElementById("rol").value === "6"
        ? (parseInt(document.getElementById("sector-form").value) || null)
        : null
    };

    if (!data.nombre1 || !data.apellido1 || !data.usuario || !data.passwd) {
      alert("Por favor complete los campos obligatorios");
      return;
    }

    const password = data.passwd;
    if (password.length < 8) {
      alert("La contraseña debe tener al menos 8 caracteres");
      return;
    }
    if (!/[A-Z]/.test(password)) {
      alert("La contraseña debe contener al menos una letra mayúscula");
      return;
    }
    if (!/[0-9]/.test(password)) {
      alert("La contraseña debe contener al menos un número");
      return;
    }

    try {
      const verificarUsuario = await fetch(`${API_BASE_URL}/api/employees/exists/${encodeURIComponent(data.usuario)}`);
      const existe = await verificarUsuario.json();
      if (existe.exists) {
        alert("El nombre de usuario ya existe. Por favor elija otro.");
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

      alert("Empleado agregado exitosamente");
      empleadoForm.reset();
      document.getElementById("sector-container").classList.add("hidden");
      loadEmployees();
    } catch (err) {
      console.error(err);
      alert(err.message || "Error al agregar empleado");
    }
  });

  // ──────────────────────────────────────────────
  // Load sectors into add-employee form
  // ──────────────────────────────────────────────
  async function cargarSectoresEnForm() {
    const sectores = await obtenerSectores();
    const sectorSelect = document.getElementById("sector-form");
    if (!sectorSelect) return;
    sectorSelect.innerHTML = '<option value="0">Sin sector</option>';
    sectores.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.ID_Sector;
      opt.textContent = s.Sector;
      sectorSelect.appendChild(opt);
    });
  }

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
  // Rol select → show/hide sector field
  // ──────────────────────────────────────────────
  const rolSelect = document.getElementById("rol");
  if (rolSelect) {
    rolSelect.addEventListener("change", function () {
      const sectorContainer = document.getElementById("sector-container");
      const sectorForm = document.getElementById("sector-form");
      if (this.value === "6") {
        sectorContainer.classList.remove("hidden");
        if (sectorForm) sectorForm.required = true;
      } else {
        sectorContainer.classList.add("hidden");
        if (sectorForm) sectorForm.required = false;
      }
    });
  }

  // ──────────────────────────────────────────────
  // Init
  // ──────────────────────────────────────────────
  cargarRoles();
  cargarSectoresEnForm();
  loadEmployees();
});
