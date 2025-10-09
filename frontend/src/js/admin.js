document.addEventListener("DOMContentLoaded", () => {

    window.selectEmployee = function () {
    const contenedor = document.getElementById("contenedor");
    const select = document.createElement("select");
    select.className =
      "w-full max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg px-3 sm:px-4 py-2.5 sm:py-3 border border-gray-300 rounded-xl bg-white text-sm sm:text-base focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition duration-300 ease-in-out shadow-sm";
      
    const opciones = [
      { value: "", text: "Seleccionar empleado" },
      { value: "empleado1", text: "Empleado 1" },
      { value: "empleado2", text: "Empleado 2" },
      { value: "empleado3", text: "Empleado 3" },
      { value: "empleado4", text: "Empleado 4" }
    ];

    opciones.forEach((op) => {
      const option = document.createElement("option");
      option.value = op.value;
      option.textContent = op.text;
      select.appendChild(option);
    });
    contenedor.appendChild(select);
  };

    // tabs
  window.selectSector = (sector) => {
    document.querySelectorAll(".sector-tab").forEach((tab) => {
      // 1. Quitar clases de gradiente verde de la pestaña activa previa
      tab.classList.remove("bg-gradient-to-r", "from-slate-600", "to-emerald-600", "text-white", "shadow-md");
      // 2. Aplicar el estilo inactivo (gris) a todas las pestañas
      tab.classList.add("bg-slate-200", "text-slate-600", "hover:bg-slate-300");
    });
    
    const activeTab = document.getElementById(`tab-${sector}`);
    
    if (activeTab) {
      // 3. Quitar el estilo inactivo (gris) de la pestaña activa
      activeTab.classList.remove("bg-slate-200", "text-slate-600", "hover:bg-slate-300");
      // 4. Aplicar el estilo activo (gradiente verde) a la pestaña seleccionada
      activeTab.classList.add("bg-gradient-to-r", "from-slate-600", "to-emerald-600", "text-white", "shadow-md");
    }
  }

  let descansosCount = 0;
  // función agregar descanso
  window.addDescanso = function (inicio = "", fin = "") {
    const container = document.getElementById("descansos-container");
    const id = descansosCount++;

    // obtener fecha de hoy en formato yyyy-mm-dd 
    const hoy = new Date().toISOString().split("T")[0];

    // calcular mañana
    const manana = new Date();
    manana.setDate(manana.getDate() + 1);
    const mananaStr = manana.toISOString().split("T")[0];

    const html = `
      <div id="descanso-${id}" 
          class="flex flex-col md:flex-row md:items-end gap-4 bg-white p-4 rounded-lg border shadow-sm">
        <div class="flex flex-col flex-1">
          <label for="inicio-${id}" class="text-gray-700 text-sm font-medium mb-1">
            Fecha de Inicio
          </label>
          <input 
            type="date" 
            id="inicio-${id}" 
            class="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            value="${inicio}" 
            min="${hoy}"
            onchange="updateMinFin(${id})"
          >
        </div>
        <div class="flex flex-col flex-1">
          <label for="fin-${id}" class="text-gray-700 text-sm font-medium mb-1">
            Fecha de Fin
          </label>
          <input 
            type="date" 
            id="fin-${id}" 
            class="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            value="${fin}" 
            min="${mananaStr}"
          >
        </div>

        <!-- Botón eliminar -->
        <button type="button" 
                onclick="removeDescanso(${id})"
                class="self-start md:self-center bg-red-600 hover:bg-red-700 text-white font-medium px-3 py-2 rounded-lg transition-colors">
          ✕
        </button>
      </div>`;
  

    container.insertAdjacentHTML("beforeend", html);
  };


   // función para actualizar la fecha mínima del fin
  window.updateMinFin = function (id) {
    const inicioInput = document.getElementById(`inicio-${id}`);
    const finInput = document.getElementById(`fin-${id}`);

    if (inicioInput && finInput) {
      // convertir la fecha de inicio a Date
      const fechaInicio = new Date(inicioInput.value);

      // calcular el día siguiente
      fechaInicio.setDate(fechaInicio.getDate() + 1);
      const minFin = fechaInicio.toISOString().split("T")[0];

      finInput.min = minFin;

      // si la fecha de fin actual es menor que la mínima, resetearla
      if (finInput.value && finInput.value < minFin) {
        finInput.value = minFin;
      }
    }
  };

  // función para eliminar descanso
  window.removeDescanso = function (id) {
    const elem = document.getElementById(`descanso-${id}`);
    if (elem) elem.remove();
  };


  // guardar agenda
  const agendaForm = document.getElementById("agenda-form");
  if (agendaForm) {
    agendaForm.addEventListener("submit", (e) => {
      e.preventDefault();
      document.getElementById("success-message").classList.remove("hidden");
      setTimeout(() => {
        document.getElementById("success-message").classList.add("hidden");
      }, 5000);
    });
  }
  // iniciar empleado select
  window.selectEmployee();
});
