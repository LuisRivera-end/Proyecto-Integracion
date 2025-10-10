const API_BASE_URL = window.location.hostname === "localhost" 
    ? "http://localhost:5000"
    : "http://backend:5000";

document.addEventListener("DOMContentLoaded", () => {
  const empleadoForm = document.getElementById("empleadoForm");
  const tablaEmpleados = document.getElementById("tablaEmpleados");

  // Cargar empleados existentes
  async function loadEmployees() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees`);
      if (!res.ok) throw new Error("Error al cargar empleados");

      const empleados = await res.json();
      renderEmployees(empleados);
    } catch (err) {
      console.error(err);
    }
  }

  function renderEmployees(empleados) {
    tablaEmpleados.innerHTML = "";
    empleados.forEach((emp, i) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="px-4 py-2 border border-gray-300">${i + 1}</td>
        <td class="px-4 py-2 border border-gray-300">${emp.name}</td>
        <td class="px-4 py-2 border border-gray-300">${emp.sector}</td>
      `;
      tablaEmpleados.appendChild(tr);
    });
  }

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

    try {
      const res = await fetch(`${API_BASE_URL}/api/employees`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      if (!res.ok) throw new Error("No se pudo agregar empleado");

      empleadoForm.reset();
      loadEmployees();
    } catch (err) {
      console.error(err);
      alert("Error al agregar empleado");
    }
  });

  loadEmployees();
});

document.addEventListener("DOMContentLoaded", () => {
  const rolSelect = document.getElementById("rol");
  const estadoSelect = document.getElementById("estado");

  // Cargar roles
  async function cargarRoles() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/roles`);
      const roles = await res.json();
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
      estados.forEach(e => {
        const opt = document.createElement("option");
        opt.value = e.ID_Estado;
        opt.textContent = e.Nombre;
        estadoSelect.appendChild(opt);
      });
    } catch (err) {
      console.error("Error al cargar estados:", err);
    }
  }

  // Ejecutar ambas al cargar la página
  cargarRoles();
  cargarEstados();
});