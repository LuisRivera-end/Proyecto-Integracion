document.addEventListener("DOMContentLoaded", () => {
  const loginScreen = document.getElementById("login-screen");
  const managementScreen = document.getElementById("management-screen");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const userSector = document.getElementById("user-sector");
  const userName = document.getElementById("user-name");
  const logoutBtn = document.getElementById("logout-btn");
  const ticketsContainer = document.getElementById("tickets-container");
  const noTicketsMessage = document.getElementById("no-tickets-message");
  const backButton = document.getElementById("back-Button");

  let currentUser = null;

  // usuarios normales
  const users = {
    servicios: { password: "servicios123", sector: "Servicios Escolares" },
    becas: { password: "becas123", sector: "Becas" },
    cajas: { password: "cajas123", sector: "Cajas" },
    admin: { password: "admin123", sector: "Administración" }
  };

  // tickets de ejemplo
  let exampleTickets = [
    { folio: "A001", matricula: "21783", sector: "Servicios Escolares" },
    { folio: "B002", matricula: "69696", sector: "Becas" },
    { folio: "C003", matricula: "12345", sector: "Cajas" },
    { folio: "A004", matricula: "54321", sector: "Servicios Escolares" },
    { folio: "B005", matricula: "67891", sector: "Becas" },
  ];

  // renderizar tickets en ventanilla
  function renderTickets(sector) {
    ticketsContainer.innerHTML = "";
    const filtered = exampleTickets.filter(t => t.sector === sector);

    if (filtered.length === 0) {
      noTicketsMessage.classList.remove("hidden");
    } else {
      noTicketsMessage.classList.add("hidden");
      filtered.forEach(ticket => {
        const div = document.createElement("div");
        div.className = "flex justify-between items-center p-4 bg-gray-50 border rounded-lg shadow-sm";
        div.innerHTML = `
          <div>
            <p class="font-semibold text-gray-800">Ticket: 
              <span class="text-blue-600">${ticket.folio}</span>
            </p>
            <p class="text-sm text-gray-600">Matrícula: ${ticket.matricula}</p>
          </div>
          <button class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg">Atender</button>
        `;
        div.querySelector("button").addEventListener("click", () => {
          exampleTickets = exampleTickets.filter(t => t.folio !== ticket.folio);
          renderTickets(sector);
        });
        ticketsContainer.appendChild(div);
      });
    }
  }

  // login
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (users[username] && users[username].password === password) {
      // si es admin → redirigir
      if (username === "admin") {
        window.location.href = "admin.html";
        return;
      }

      currentUser = { username, sector: users[username].sector };
      loginScreen.classList.add("hidden");
      loginError.classList.add("hidden");
      managementScreen.classList.remove("hidden");
      backButton.classList.add("hidden");

      userSector.textContent = currentUser.sector;
      userName.textContent = currentUser.username;
      renderTickets(currentUser.sector);
    } else {
      loginError.classList.remove("hidden");
    }
  });

  // logout
  logoutBtn.addEventListener("click", () => {
    currentUser = null;
    loginForm.reset();
    loginScreen.classList.remove("hidden");
    managementScreen.classList.add("hidden");
    backButton.classList.remove("hidden");
  });
});

/* 
document.addEventListener("DOMContentLoaded", () => {
  const loginScreen = document.getElementById("login-screen");
  const managementScreens = document.querySelectorAll("#management-screen"); // hay dos divs con el mismo id
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const userSector = document.getElementById("user-sector");
  const userName = document.getElementById("user-name");
  const logoutBtns = document.querySelectorAll("#logout-btn, [onclick='logout()']");
  const ticketsContainer = document.getElementById("tickets-container");
  const noTicketsMessage = document.getElementById("no-tickets-message");
  const backButton = document.getElementById("back-Button")

  let descansosCount = 0;
  let currentUser = null;

  // usuarios normales
  const users = {
    servicios: { password: "servicios123", sector: "Servicios Escolares" },
    becas: { password: "becas123", sector: "Becas" },
    cajas: { password: "cajas123", sector: "Cajas" },
    admin: { password: "admin123", sector: "Administración" }
  };

  // tickets esto se eliminara
  let exampleTickets = [
    { folio: "A001", matricula: "21783", sector: "Servicios Escolares" },
    { folio: "B002", matricula: "69696", sector: "Becas" },
    { folio: "C003", matricula: "12345", sector: "Cajas" },
    { folio: "A004", matricula: "54321", sector: "Servicios Escolares" },
    { folio: "B005", matricula: "67891", sector: "Becas" },
  ];

  // renderizar tickets en ventanilla
  function renderTickets(sector) {
    if (!ticketsContainer) return;
    ticketsContainer.innerHTML = "";
    const filtered = exampleTickets.filter((t) => t.sector === sector);

    if (filtered.length === 0) {
      noTicketsMessage?.classList.remove("hidden");
    } else {
      noTicketsMessage?.classList.add("hidden");
      filtered.forEach((ticket) => {
        const div = document.createElement("div");
        div.className =
          "flex justify-between items-center p-4 bg-gray-50 border rounded-lg shadow-sm";
        div.innerHTML = `
          <div>
            <p class="font-semibold text-gray-800">Ticket: 
              <span class="text-blue-600">${ticket.folio}</span>
            </p>
            <p class="text-sm text-gray-600">Matrícula: ${ticket.matricula}</p>
          </div>
          <button class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg">
            Atender
          </button>
        `;
        div.querySelector("button").addEventListener("click", () => {
          exampleTickets = exampleTickets.filter((t) => t.folio !== ticket.folio);
          renderTickets(sector);
        });
        ticketsContainer.appendChild(div);
      });
    }
  }

  // login
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (users[username] && users[username].password === password) {
      currentUser = { username, sector: users[username].sector };

      loginScreen.classList.add("hidden");
      loginError.classList.add("hidden");

      // mostrar pantalla correcta
      if (username === "admin") {
        managementScreens[1].classList.remove("hidden"); // admin
        backButton.classList.add("hidden");
      } else {
        userSector.textContent = currentUser.sector;
        userName.textContent = currentUser.username;
        managementScreens[0].classList.remove("hidden"); // ventanilla
        backButton.classList.add("hidden");
        renderTickets(currentUser.sector);
      }
    } else {
      loginError.classList.remove("hidden");
    }
  });

  // logout
  function logout() {
    currentUser = null;
    loginForm.reset();
    loginScreen.classList.remove("hidden");
    backButton.classList.remove("hidden")
    managementScreens.forEach((s) => s.classList.add("hidden"));
  }
  logoutBtns.forEach((btn) => btn.addEventListener("click", logout));

  //   ADMINISTRADOR

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

  // select empleado
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

*/