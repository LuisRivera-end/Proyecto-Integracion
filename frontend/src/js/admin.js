const API_BASE_URL = window.location.hostname === "localhost" 
      ? "http://localhost:5000"
      : "http://backend:5000"; 

    // -----------------------------
    // FUNCIÓN PARA SELECCIONAR SECTOR
    // -----------------------------
    function selectSector(sector) {
      console.log("Sector seleccionado:", sector);

      // Cambiar estilo de botón activo
      document.querySelectorAll(".sector-tab").forEach(btn => {
        btn.classList.remove("bg-gradient-to-r", "from-slate-600", "to-emerald-600", "text-white");
        btn.classList.add("bg-slate-200", "text-slate-600");
      });

      const activeBtn = document.getElementById(`tab-${sector}`);
      if (activeBtn) {
        activeBtn.classList.add("bg-gradient-to-r", "from-slate-600", "to-emerald-600", "text-white");
        activeBtn.classList.remove("bg-slate-200", "text-slate-600");
      }

      // Aquí puedes agregar lógica para mostrar/ocultar contenido según el sector
    }

    document.addEventListener("DOMContentLoaded", () => {

      // -----------------------------
      // CARGAR EMPLEADOS DESDE BACKEND
      // -----------------------------
      async function loadEmployees() {
        try {
          const res = await fetch(`${API_BASE_URL}/api/employees`);
          if (!res.ok) throw new Error("No se pudieron cargar los empleados");

          const empleados = await res.json();
          populateEmployeeSelect(empleados);
        } catch (err) {
          console.error(err);
          alert("Error al cargar empleados");
        }
      }

      function populateEmployeeSelect(empleados) {
        const contenedor = document.getElementById("contenedor");
        const select = document.createElement("select");
        select.className =
          "w-full max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg px-3 sm:px-4 py-2.5 sm:py-3 border border-gray-300 rounded-xl bg-white text-sm sm:text-base focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition duration-300 ease-in-out shadow-sm";

        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "Seleccionar empleado";
        select.appendChild(defaultOption);

        empleados.forEach(emp => {
          const option = document.createElement("option");
          option.value = emp.id;
          option.textContent = emp.name;
          select.appendChild(option);
        });

        contenedor.appendChild(select);
      }

      // -----------------------------
      // AGREGAR DESCANSOS
      // -----------------------------
      let descansosCount = 0;
      window.addDescanso = function (inicio = "", fin = "") {
        const container = document.getElementById("descansos-container");
        const id = descansosCount++;
        const hoy = new Date().toISOString().split("T")[0];
        const manana = new Date();
        manana.setDate(manana.getDate() + 1);
        const mananaStr = manana.toISOString().split("T")[0];

        const html = `
          <div id="descanso-${id}" class="flex flex-col md:flex-row md:items-end gap-4 bg-white p-4 rounded-lg border shadow-sm">
            <div class="flex flex-col flex-1">
              <label for="inicio-${id}">Fecha de Inicio</label>
              <input type="date" id="inicio-${id}" value="${inicio}" min="${hoy}" onchange="updateMinFin(${id})">
            </div>
            <div class="flex flex-col flex-1">
              <label for="fin-${id}">Fecha de Fin</label>
              <input type="date" id="fin-${id}" value="${fin}" min="${mananaStr}">
            </div>
            <button type="button" onclick="removeDescanso(${id})">✕</button>
          </div>
        `;

        container.insertAdjacentHTML("beforeend", html);
      };

      window.updateMinFin = function(id) {
        const inicioInput = document.getElementById(inicio-`${id}`);
        const finInput = document.getElementById(fin-`${id}`);
        if (!inicioInput || !finInput) return;

        const fechaInicio = new Date(inicioInput.value);
        fechaInicio.setDate(fechaInicio.getDate() + 1);
        const minFin = fechaInicio.toISOString().split("T")[0];

        finInput.min = minFin;
        if (finInput.value && finInput.value < minFin) finInput.value = minFin;
      };

      window.removeDescanso = function(id) {
        const elem = document.getElementById(descanso-`${id}`);
        if (elem) elem.remove();
      };

      // -----------------------------
      // GUARDAR AGENDA EN BACKEND
      // -----------------------------
      const agendaForm = document.getElementById("agenda-form");
      if (agendaForm) {
        agendaForm.addEventListener("submit", async (e) => {
          e.preventDefault();

          const select = document.querySelector("#contenedor select");
          if (!select || !select.value) {
            alert("Selecciona un empleado");
            return;
          }

          const employeeId = select.value;

          const descansosElems = document.querySelectorAll("[id^='descanso-']");
          const descansos = Array.from(descansosElems).map(d => {
            return {
              inicio: d.querySelector("[id^='inicio-']").value,
              fin: d.querySelector("[id^='fin-']").value
            };
          });

          try {
            const res = await fetch(`${API_BASE_URL}/api/agenda`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ employeeId, descansos })
            });

            if (!res.ok) throw new Error("Error al guardar agenda");

            document.getElementById("success-message").classList.remove("hidden");
            setTimeout(() => {
              document.getElementById("success-message").classList.add("hidden");
            }, 5000);
          } catch (err) {
            console.error(err);
            alert("No se pudo guardar la agenda");
          }
        });
      }

      // -----------------------------
      // INICIALIZAR
      // -----------------------------
      loadEmployees();
    });