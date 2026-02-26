import Config from './config.js';
import { lanzarAlerta } from './alertas/notifier.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", async () => {
  const sectorForm = document.getElementById("sectorForm");
  const tablaSectores = document.getElementById("tablaSectores");

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
          <td colspan="2" class="px-6 py-8 text-center text-slate-400 text-sm font-medium">
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
    const nombre = nombreInput.value.trim();

    if (!nombre) {
      lanzarAlerta("El nombre del sector es obligatorio", "error");
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/sectores`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sector: nombre })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "No se pudo agregar el sector");
      }

      lanzarAlerta("Sector agregado exitosamente", "success");
      sectorForm.reset();
      cargarSectores();
    } catch (err) {
      console.error(err);
      lanzarAlerta(err.message || "Error al agregar sector", "error");
    }
  });

  // ──────────────────────────────────────────────
  // Init
  // ──────────────────────────────────────────────
  cargarSectores();
});

// ──────────────────────────────────────────────
// Logout (moved from admin.js)
// ──────────────────────────────────────────────
async function logout() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/logout`, {
      method: "POST",
      credentials: "include"
    });
    const data = await res.json();
    alert(data.message);
    window.location.href = "/login.html";
  } catch (error) {
    console.error("Error al cerrar sesión:", error);
  }
}
window.logout = logout;

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
