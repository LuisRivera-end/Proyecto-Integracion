import Config from './config.js';
import { lanzarAlerta } from './alertas/notifier.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", async () => {
  const sectorForm = document.getElementById("sectorForm");
  const tablaSectores = document.getElementById("tablaSectores");
  const editContainer = document.getElementById("editSectorContainer");
  const editPlaceholder = document.getElementById("editPlaceholder");

  // ──────────────────────────────────────────────
  // WEBSOCKET
  // ──────────────────────────────────────────────
  const socket = io(API_BASE_URL);
  let editingSectorId = null;

  socket.on('connect', () => {
    console.log('🟢 Departamentos WebSocket conectado');
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
    if (editingSectorId !== null) {
      refreshVentanillasTable(editingSectorId);
    }
  });

  socket.on('sectores_updated', () => {
    cargarSectores();
    if (editingSectorId !== null) {
      refreshVentanillasTable(editingSectorId);
    }
  });

  // ──────────────────────────────────────────────
  // LOAD & RENDER departamentos
  // ──────────────────────────────────────────────
  async function cargarSectores() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/sectores`);
      if (!res.ok) throw new Error("Error al cargar departamentos");
      const sectores = await res.json();
      renderSectores(sectores);
    } catch (err) {
      console.error(err);
      lanzarAlerta("Error al cargar departamentos", "error");
    }
  }

  function renderSectores(sectores) {
    tablaSectores.innerHTML = "";

    if (sectores.length === 0) {
      tablaSectores.innerHTML = `
        <tr>
          <td colspan="4" class="px-6 py-8 text-center text-slate-400 text-sm font-medium">
            No hay departamentos registrados
          </td>
        </tr>`;
      return;
    }

    sectores.forEach((s, idx) => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition-colors";
      tr.innerHTML = `
        <td class="px-6 py-3.5 text-center font-medium text-slate-500 text-sm">${idx + 1}</td>
        <td class="px-6 py-3.5 font-medium text-slate-800 text-sm">${s.Sector}</td>
        <td class="px-6 py-3.5 text-center font-medium text-slate-600 text-sm">${s.Ventanillas}</td>
        <td class="px-6 py-3.5 text-center">
          <button class="edit-btn" onclick="editarSector(${s.ID_Sector}, '${s.Sector.replace(/'/g, "\\'")}', ${s.Ventanillas})">
            Editar
          </button>
        </td>
      `;
      tablaSectores.appendChild(tr);
    });
  }

  // ──────────────────────────────────────────────
  // ADD departamento form submit
  // ──────────────────────────────────────────────
  sectorForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const nombreInput = document.getElementById("sectorNombre");
    const ventanillasInput = document.getElementById("sectorVentanillas");
    const nombre = nombreInput.value.trim();
    const ventanillas = parseInt(ventanillasInput.value) || 1;

    if (!nombre) {
      lanzarAlerta("El nombre del departamento es obligatorio", "error");
      return;
    }

    if (ventanillas < 1) {
      lanzarAlerta("Debe haber al menos 1 ventanilla", "error");
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/sectores`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sector: nombre, ventanillas: ventanillas })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "No se pudo agregar el departamento");
      }

      lanzarAlerta("Departamento agregado exitosamente", "success");
      sectorForm.reset();
      document.getElementById("sectorVentanillas").value = "1";
      cargarSectores();
    } catch (err) {
      console.error(err);
      lanzarAlerta(err.message || "Error al agregar departamento", "error");
    }
  });

  // ──────────────────────────────────────────────
  // Fetch ventanillas for a sector
  // ──────────────────────────────────────────────
  async function fetchVentanillas(idSector) {
    const res = await fetch(`${API_BASE_URL}/api/sectores/${idSector}/ventanillas`);
    if (!res.ok) throw new Error("Error al cargar ventanillas");
    return await res.json();
  }

  // ──────────────────────────────────────────────
  // Refresh ventanillas table (live update)
  // ──────────────────────────────────────────────
  async function refreshVentanillasTable(idSector) {
    try {
      const ventanillas = await fetchVentanillas(idSector);
      const tbody = document.getElementById('ventanillasTableBody');
      if (!tbody) return;
      renderVentanillasRows(tbody, ventanillas);
    } catch (err) {
      console.error('Error refreshing ventanillas:', err);
    }
  }

  // ──────────────────────────────────────────────
  // Render ventanilla rows inside tbody
  // ──────────────────────────────────────────────
  function renderVentanillasRows(tbody, ventanillas) {
    tbody.innerHTML = '';

    if (ventanillas.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="4" class="px-4 py-6 text-center text-slate-400 text-sm">
            No hay ventanillas en este departamento
          </td>
        </tr>`;
      return;
    }

    ventanillas.forEach(v => {
      const isActive = v.Activa === 1;
      const hasEmployee = !!v.empleado_asignado;
      const tr = document.createElement('tr');
      tr.className = `transition-colors ${isActive ? 'hover:bg-slate-50' : 'bg-slate-100/60'}`;
      tr.dataset.vid = v.ID_Ventanilla;

      tr.innerHTML = `
        <td class="px-4 py-3">
          <input type="text" value="${v.Ventanilla}" 
            data-original="${v.Ventanilla}"
            data-vid="${v.ID_Ventanilla}"
            ${hasEmployee ? 'disabled title="En uso por un empleado"' : ''}
            class="ventanilla-name-input w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-800 text-sm font-medium
              focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all
              ${!isActive ? 'opacity-50' : ''} ${hasEmployee ? 'opacity-50 cursor-not-allowed bg-slate-50' : ''}" />
        </td>
        <td class="px-4 py-3 text-center">
          <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold
            ${isActive 
              ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' 
              : 'bg-red-100 text-red-700 border border-red-200'}">
            <span class="w-1.5 h-1.5 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-red-500'}"></span>
            ${isActive ? 'Activa' : 'Inactiva'}
          </span>
          ${hasEmployee ? `<p class="text-[11px] text-slate-400 mt-1 font-medium">${v.empleado_asignado}</p>` : ''}
        </td>
        <td class="px-4 py-3 text-center">
          <button type="button" 
            data-vid="${v.ID_Ventanilla}" 
            data-action="${isActive ? 'disable' : 'enable'}"
            ${hasEmployee && isActive ? 'disabled title="Empleado asignado"' : ''}
            class="toggle-ventanilla-btn px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-200 
              ${isActive
                ? (hasEmployee 
                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
                    : 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 hover:border-red-300 active:scale-95')
                : 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-200 hover:border-emerald-300 active:scale-95'
              }">
            ${isActive ? 'Deshabilitar' : 'Habilitar'}
          </button>
        </td>
      `;

      tbody.appendChild(tr);
    });

    // Attach event listeners for toggle buttons
    tbody.querySelectorAll('.toggle-ventanilla-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (btn.disabled) return;
        const vid = parseInt(btn.dataset.vid);
        const action = btn.dataset.action;
        const nuevaActiva = action === 'enable' ? 1 : 0;

        try {
          const res = await fetch(`${API_BASE_URL}/api/ventanillas/${vid}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ activa: nuevaActiva })
          });

          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Error al cambiar estado');

          lanzarAlerta(data.message, 'success');
        } catch (err) {
          console.error(err);
          lanzarAlerta(err.message || 'Error al cambiar estado de ventanilla', 'error');
        }
      });
    });
  }

  // ──────────────────────────────────────────────
  // EDIT departamento
  // ──────────────────────────────────────────────
  window.editarSector = async function (id, nombre, ventanillas) {
    editingSectorId = id;

    // Open the edit accordion
    const contentEditar = document.getElementById('content-editar');
    if (!contentEditar.classList.contains('open')) {
      toggleAccordion('editar');
    }

    // Hide placeholder, show edit form
    editPlaceholder.style.display = 'none';

    // Remove existing edit form if any
    const existingForm = editContainer.querySelector('#editSectorForm');
    if (existingForm) existingForm.remove();

    // Fetch ventanillas for this sector
    let ventanillasList = [];
    try {
      ventanillasList = await fetchVentanillas(id);
    } catch (err) {
      console.error(err);
      lanzarAlerta('Error al cargar ventanillas', 'error');
    }

    const formHTML = `
      <form id="editSectorForm" class="space-y-5">
        <p class="text-sm text-slate-500 mb-2 font-medium">Editando: <strong>${nombre}</strong></p>

        <div>
          <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Nombre del departamento *</label>
          <input id="editSectorNombre" type="text" required value="${nombre}"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
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
              <tbody id="ventanillasTableBody" class="divide-y divide-slate-100">
                <!-- rows rendered by JS -->
              </tbody>
            </table>
          </div>
        </div>

        <div class="flex gap-3">
          <button type="submit"
            class="flex-1 bg-slate-800 hover:bg-slate-700 text-white font-bold py-3.5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:scale-95">
            Guardar cambios
          </button>
          <button type="button" onclick="cancelarEdicion()"
            class="px-6 bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold py-3.5 rounded-xl transition-all duration-200">
            Cancelar
          </button>
        </div>
      </form>
    `;

    editContainer.insertAdjacentHTML('beforeend', formHTML);

    // Render ventanillas rows
    const tbody = document.getElementById('ventanillasTableBody');
    renderVentanillasRows(tbody, ventanillasList);

    // Handle edit form submit (save department name + ventanilla renames)
    document.getElementById('editSectorForm').addEventListener('submit', async (e) => {
      e.preventDefault();

      const nuevoNombre = document.getElementById('editSectorNombre').value.trim();

      if (!nuevoNombre) {
        lanzarAlerta("El nombre del departamento es obligatorio", "error");
        return;
      }

      const submitBtn = e.target.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Guardando...';

      try {
        // 1. Save department name
        const resSector = await fetch(`${API_BASE_URL}/api/sectores/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sector: nuevoNombre })
        });

        const dataSector = await resSector.json();
        if (!resSector.ok) {
          throw new Error(dataSector.error || "No se pudo actualizar el departamento");
        }

        // 2. Save individual ventanilla name changes
        const nameInputs = document.querySelectorAll('.ventanilla-name-input');
        let renameErrors = [];

        for (const input of nameInputs) {
          const vid = input.dataset.vid;
          const originalName = input.dataset.original;
          const newName = input.value.trim();

          if (newName && newName !== originalName) {
            try {
              const resV = await fetch(`${API_BASE_URL}/api/ventanillas/${vid}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre: newName })
              });

              const dataV = await resV.json();
              if (!resV.ok) {
                renameErrors.push(`${originalName}: ${dataV.error}`);
              }
            } catch (err) {
              renameErrors.push(`${originalName}: ${err.message}`);
            }
          }
        }

        if (renameErrors.length > 0) {
          lanzarAlerta(`Departamento actualizado. Errores al renombrar: ${renameErrors.join(', ')}`, 'warning');
        } else {
          lanzarAlerta("Departamento actualizado correctamente", "success");
        }

        cancelarEdicion();
        cargarSectores();
      } catch (err) {
        console.error(err);
        lanzarAlerta(err.message || "Error al actualizar departamento", "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Guardar cambios';
      }
    });

    // Scroll to edit panel
    document.getElementById('header-editar').scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  window.cancelarEdicion = function () {
    editingSectorId = null;
    const existingForm = editContainer.querySelector('#editSectorForm');
    if (existingForm) existingForm.remove();
    editPlaceholder.style.display = 'flex';
  };

  // ──────────────────────────────────────────────
  // Init
  // ──────────────────────────────────────────────
  cargarSectores();
});

// ──────────────────────────────────────────────
// Accordion toggle
// ──────────────────────────────────────────────
function toggleAccordion(id) {
  const content = document.getElementById('content-' + id);
  const header = document.getElementById('header-' + id);
  const arrow = header.querySelector('.accordion-arrow');

  const isOpen = content.classList.contains('open');

  if (isOpen) {
    content.classList.remove('open');
    header.classList.remove('open');
    arrow.classList.remove('rotate-180');
  } else {
    content.classList.add('open');
    header.classList.add('open');
    arrow.classList.add('rotate-180');
  }
}
window.toggleAccordion = toggleAccordion;
