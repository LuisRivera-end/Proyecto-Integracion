import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", () => {
  const empleadoForm = document.getElementById("empleadoForm");
  const tablaEmpleados = document.getElementById("tablaEmpleados");

  // Cargar empleados con toda la información
  async function loadEmployees() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees/full`);
      if (!res.ok) throw new Error("Error al cargar empleados");

      const empleados = await res.json();
      renderEmployees(empleados);
    } catch (err) {
      console.error(err);
      alert("Error al cargar empleados");
    }
  }

  async function renderEmployees(empleados) {
    tablaEmpleados.innerHTML = "";

    for (const emp of empleados) {
      // Construir nombre completo
      const nombreCompleto = [
        emp.nombre1,
        emp.nombre2 || '',
        emp.Apellido1,
        emp.Apellido2 || ''
      ].filter(n => n.trim() !== '').join(' ');

      // Determinar clase de estado para el badge
      const getEstadoClass = (idEstado) => {
        switch(idEstado) {
          case 1: return 'bg-green-100 text-green-800';      // Activo
          case 2: return 'bg-yellow-100 text-yellow-800';    // Descanso
          case 3: return 'bg-red-100 text-red-800';          // Despedido
          case 4: return 'bg-gray-100 text-gray-800';        // Inactivo
          default: return 'bg-gray-100 text-gray-800';
        }
      };

      const getEstadoNombre = (idEstado) => {
        switch(idEstado) {
          case 1: return 'Activo';
          case 2: return 'Descanso';
          case 3: return 'Despedido';
          case 4: return 'Inactivo';
          default: return 'Desconocido';
        }
      };

      // Es admin?
      const esAdmin = emp.ID_ROL === 1;

      // Construir celda de estado
      let estadoCell = '';
      
      if (esAdmin) {
        // Admin siempre activo, no editable
        estadoCell = `
          <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getEstadoClass(1)}">
            Activo
          </span>
        `;
      } else if (emp.ID_Estado === 2) {
        // 💤 Si está en descanso, solo mostrar la opción "Descanso" bloqueada
        estadoCell = `
          <select disabled 
            class="w-32 px-2 py-1 text-xs font-medium rounded-lg border bg-yellow-100 text-yellow-800 cursor-not-allowed">
            <option value="2" selected>Descanso</option>
          </select>
        `;
      } else {
        // 🟢 Si no está en descanso, mostrar todas menos "Descanso"
        estadoCell = `
          <select 
            onchange="cambiarEstado(${emp.ID_Empleado}, this.value)"
            class="w-32 px-2 py-1 text-xs font-medium rounded-lg border focus:outline-none focus:ring-2 focus:ring-slate-500 ${getEstadoClass(emp.ID_Estado)}">
            <option value="1" ${emp.ID_Estado === 1 ? 'selected' : ''}>Activo</option>
            <option value="3" ${emp.ID_Estado === 3 ? 'selected' : ''}>Despedido</option>
            <option value="4" ${emp.ID_Estado === 4 ? 'selected' : ''}>Inactivo</option>
          </select>
        `;
      }

      // Función para formatear nombres de ventanillas
      const formatearNombreVentanilla = (nombre) => {
        if (!nombre) return '';
        if (nombre.startsWith('Caja')) {
          return nombre; // Caja1, Caja2, etc.
        } else if (nombre.startsWith('ServiciosEscolares')) {
          const numero = nombre.replace('ServiciosEscolares', '');
          return `Sev ${numero}`;
        } else if (nombre.startsWith('Beca')) {
          return 'Becas 1';
        }
        return nombre;
      };

      // Construir celda de ventanilla
      let ventanillaCell = '';
      
      if (esAdmin) {
        // Admin no tiene ventanilla
        ventanillaCell = '<span class="text-gray-400 text-xs">N/A</span>';
      } else if (emp.ID_ROL === 3) {
        // Operador Becas - mostrar "Becas 1"
        ventanillaCell = emp.Ventanilla 
          ? `<span class="text-sm">${formatearNombreVentanilla(emp.Ventanilla)}</span>`
          : '<span class="text-gray-400 text-xs">Sin asignar</span>';
      } else {
        // Operador Cajas o Servicios Escolares - select para elegir
        const ventanillas = await cargarVentanillasParaRol(emp.ID_ROL);
        
        console.log(`Ventanillas para empleado ${emp.ID_Empleado} (Rol ${emp.ID_ROL}):`, ventanillas);
        
        ventanillaCell = `
          <select 
            onchange="asignarVentanilla(${emp.ID_Empleado}, this.value)"
            class="w-32 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-slate-500">
            <option value="">Seleccionar...</option>
            ${ventanillas.map(v => `
              <option value="${v.ID_Ventanilla}" ${emp.ID_Ventanilla === v.ID_Ventanilla ? 'selected' : ''}>
                ${formatearNombreVentanilla(v.Ventanilla)}
              </option>
            `).join('')}
          </select>
        `;
      }

      const tr = document.createElement("tr");
      tr.className = "hover:bg-gray-50 transition-colors";
      tr.innerHTML = `
        <td class="px-4 py-3 border border-gray-300 text-center font-medium">${emp.ID_Empleado}</td>
        <td class="px-4 py-3 border border-gray-300">${nombreCompleto}</td>
        <td class="px-4 py-3 border border-gray-300">${emp.Usuario}</td>
        <td class="px-4 py-3 border border-gray-300">${emp.Rol || 'N/A'}</td>
        <td class="px-4 py-3 border border-gray-300 text-center">${ventanillaCell}</td>
        <td class="px-4 py-3 border border-gray-300 text-center">${estadoCell}</td>
      `;
      tablaEmpleados.appendChild(tr);
    }
  }

  // Cargar ventanillas según el rol
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

  // Función global para asignar ventanilla
  window.asignarVentanilla = async function(idEmpleado, idVentanilla) {
    if (!idVentanilla) return;
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees/${idEmpleado}/ventanilla`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_ventanilla: parseInt(idVentanilla) })
      });

      if (!res.ok) throw new Error("Error al asignar ventanilla");

      alert("Ventanilla asignada correctamente");
      loadEmployees();
    } catch (err) {
      console.error(err);
      alert("Error al asignar ventanilla");
    }
  };

  // Función global para cambiar estado
  window.cambiarEstado = async function(idEmpleado, nuevoEstado) {
    const estadoNombre = {
      1: 'activar', 
      3: 'despedir', 
      4: 'desactivar'
    };
    
    if (!confirm(`¿Está seguro de ${estadoNombre[nuevoEstado]} este empleado?`)) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/employees/${idEmpleado}/estado`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estado: parseInt(nuevoEstado) })
      });

      const data = await res.json();
      
      if (!res.ok) {
        alert(data.error || `Error al cambiar estado del empleado`);
        return;
      }

      alert(`Estado del empleado actualizado correctamente`);
      loadEmployees();
    } catch (err) {
      console.error(err);
      alert(`Error al cambiar estado del empleado`);
    }
  };

  // Agregar empleado
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
      id_estado: parseInt(document.getElementById("estado").value)
    };

    // Validaciones
    if (!data.nombre1 || !data.apellido1 || !data.usuario || !data.passwd) {
      alert("Por favor complete los campos obligatorios");
      return;
    }

    try {
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
      loadEmployees();
    } catch (err) {
      console.error(err);
      alert(err.message || "Error al agregar empleado");
    }
  });

  // Cargar roles
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

  // Cargar estados
  async function cargarEstados() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/estados_empleado`);
      const estados = await res.json();
      const estadoSelect = document.getElementById("estado");
      
      // ❌ No mostrar "Descanso" al agregar empleado
      estados.forEach(e => {
        if (e.Nombre !== "Descanso") {
          const opt = document.createElement("option");
          opt.value = e.ID_Estado;
          opt.textContent = e.Nombre;
          estadoSelect.appendChild(opt);
        }
      });
    } catch (err) {
      console.error("Error al cargar estados:", err);
    }
  }

  // Inicializar
  cargarRoles();
  cargarEstados();
  loadEmployees();
});
