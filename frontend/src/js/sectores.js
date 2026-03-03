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
  let editingSectorId = null; // sector actualmente en edición

  socket.on('connect', () => {
    console.log('🟢 Sectores WebSocket conectado');
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

  // Cuando cambia el status de alguna ventanilla, re-verificar
  socket.on('ventanilla_status_changed', () => {
    if (editingSectorId !== null) {
      socket.emit('check_sector_ventanillas', { id_sector: editingSectorId });
    }
  });

  // Cuando se actualizan sectores, recargar tabla
  socket.on('sectores_updated', () => {
    cargarSectores();
    // Si estamos editando, re-verificar el status
    if (editingSectorId !== null) {
      socket.emit('check_sector_ventanillas', { id_sector: editingSectorId });
    }
  });

  // Respuesta del check de ventanillas
  socket.on('sector_ventanillas_status', (data) => {
    if (data.id_sector !== editingSectorId) return;

    const nombreInput = document.getElementById('editSectorNombre');
    const ventanillasInput = document.getElementById('editSectorVentanillas');
    const warningEl = document.getElementById('ventanillaWarning');

    if (!ventanillasInput) return;

    if (data.puede_modificar) {
      // Habilitar nombre y cantidad de ventanillas
      if (nombreInput) {
        nombreInput.disabled = false;
        nombreInput.classList.remove('opacity-50', 'cursor-not-allowed');
      }
      ventanillasInput.disabled = false;
      ventanillasInput.classList.remove('opacity-50', 'cursor-not-allowed');
      if (warningEl) warningEl.style.display = 'none';
    } else {
      // Deshabilitar solo nombre y cantidad de ventanillas
      if (nombreInput) {
        nombreInput.disabled = true;
        nombreInput.classList.add('opacity-50', 'cursor-not-allowed');
      }
      ventanillasInput.disabled = true;
      ventanillasInput.classList.add('opacity-50', 'cursor-not-allowed');
      if (warningEl) {
        const nombres = (data.empleados_con_ventanilla || [])
          .map(e => `${e.nombre} (${e.Ventanilla})`)
          .join(', ');
        warningEl.innerHTML = `⚠️ No se puede modificar el nombre ni la cantidad de ventanillas. Empleados con ventanilla asignada: <strong>${nombres}</strong>`;
        warningEl.style.display = 'block';
      }
    }
  });

  // ──────────────────────────────────────────────
  // LOAD & RENDER sectores
  // ──────────────────────────────────────────────
  async function cargarSectores() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/sectores`);
      if (!res.ok) throw new Error("Error al cargar sectores");
      const sectores = await res.json();
      renderSectores(sectores);
    } catch (err) {
      console.error(err);
      lanzarAlerta("Error al cargar sectores", "error");
    }
  }

  function renderSectores(sectores) {
    tablaSectores.innerHTML = "";

    if (sectores.length === 0) {
      tablaSectores.innerHTML = `
        <tr>
          <td colspan="4" class="px-6 py-8 text-center text-slate-400 text-sm font-medium">
            No hay sectores registrados
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
  // ADD sector form submit
  // ──────────────────────────────────────────────
  sectorForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const nombreInput = document.getElementById("sectorNombre");
    const ventanillasInput = document.getElementById("sectorVentanillas");
    const nombre = nombreInput.value.trim();
    const ventanillas = parseInt(ventanillasInput.value) || 1;

    if (!nombre) {
      lanzarAlerta("El nombre del sector es obligatorio", "error");
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
        throw new Error(data.error || "No se pudo agregar el sector");
      }

      lanzarAlerta("Sector agregado exitosamente", "success");
      sectorForm.reset();
      document.getElementById("sectorVentanillas").value = "1";
      cargarSectores();
    } catch (err) {
      console.error(err);
      lanzarAlerta(err.message || "Error al agregar sector", "error");
    }
  });

  // ──────────────────────────────────────────────
  // EDIT sector
  // ──────────────────────────────────────────────
  window.editarSector = function (id, nombre, ventanillas) {
    editingSectorId = id;

    // Open the edit accordion
    const contentEditar = document.getElementById('content-editar');
    const headerEditar = document.getElementById('header-editar');
    if (!contentEditar.classList.contains('open')) {
      toggleAccordion('editar');
    }

    // Hide placeholder, show edit form
    editPlaceholder.style.display = 'none';

    // Remove existing edit form if any
    const existingForm = editContainer.querySelector('#editSectorForm');
    if (existingForm) existingForm.remove();

    const formHTML = `
      <form id="editSectorForm" class="space-y-5">
        <p class="text-sm text-slate-500 mb-2 font-medium">Editando: <strong>${nombre}</strong></p>

        <div id="ventanillaWarning" style="display:none"
          class="px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-700 text-sm font-medium">
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Nombre del sector *</label>
          <input id="editSectorNombre" type="text" required value="${nombre}"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Cantidad de ventanillas *</label>
          <input id="editSectorVentanillas" type="number" required min="0" max="5" value="${ventanillas}"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all font-medium" />
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Deshabilitar / Habilitar ventanilla por número</label>
          <div class="flex gap-2">
            <input id="toggleVentanillaNum" type="number" min="1" placeholder="Ej: 3"
              class="flex-1 px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500/20 focus:border-slate-500 transition-all font-medium" />
            <button type="button" id="disableVentanillaBtn"
              class="px-4 bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:scale-95 text-sm">
              Deshabilitar
            </button>
            <button type="button" id="enableVentanillaBtn"
              class="px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:scale-95 text-sm">
              Habilitar
            </button>
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

    // Verificar status de ventanillas vía WebSocket
    socket.emit('check_sector_ventanillas', { id_sector: id });

    // Handle toggle ventanilla (disable/enable)
    async function toggleVentanilla(accion) {
      const numInput = document.getElementById('toggleVentanillaNum');
      const numero = parseInt(numInput.value);

      if (!numero || numero < 1) {
        lanzarAlerta("Ingrese un número de ventanilla válido", "error");
        return;
      }

      try {
        const res = await fetch(`${API_BASE_URL}/api/sectores/${id}/ventanilla/toggle`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ numero, accion })
        });

        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.error || "No se pudo cambiar el estado de la ventanilla");
        }

        lanzarAlerta(data.message, "success");
        numInput.value = '';
        cargarSectores();
      } catch (err) {
        console.error(err);
        lanzarAlerta(err.message || "Error al cambiar estado de ventanilla", "error");
      }
    }

    document.getElementById('disableVentanillaBtn').addEventListener('click', () => toggleVentanilla('deshabilitar'));
    document.getElementById('enableVentanillaBtn').addEventListener('click', () => toggleVentanilla('habilitar'));

    // Handle edit form submit
    document.getElementById('editSectorForm').addEventListener('submit', async (e) => {
      e.preventDefault();

      const nuevoNombre = document.getElementById('editSectorNombre').value.trim();
      const nuevasVentanillas = parseInt(document.getElementById('editSectorVentanillas').value) ?? 0;

      if (!nuevoNombre) {
        lanzarAlerta("El nombre del sector es obligatorio", "error");
        return;
      }

      try {
        const res = await fetch(`${API_BASE_URL}/api/sectores/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sector: nuevoNombre, ventanillas: nuevasVentanillas })
        });

        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.error || "No se pudo actualizar el sector");
        }

        // Check if there were ventanillas that couldn't be deleted
        if (data.ventanillas_en_uso) {
          lanzarAlerta(`Sector actualizado. No se eliminaron: ${data.ventanillas_en_uso.join(', ')} (en uso)`, "warning");
        } else {
          lanzarAlerta("Sector actualizado correctamente", "success");
        }

        cancelarEdicion();
        cargarSectores();
      } catch (err) {
        console.error(err);
        lanzarAlerta(err.message || "Error al actualizar sector", "error");
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

