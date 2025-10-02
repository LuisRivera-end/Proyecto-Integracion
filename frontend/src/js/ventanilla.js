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
  window.selectSector = function (sector) {
    document.querySelectorAll(".sector-tab").forEach((tab) => {
      tab.classList.remove("bg-cyan-400", "text-white");
      tab.classList.add("bg-gray-500", "text-gray-400", "hover:bg-gray-700");
    });
    const activeTab = document.getElementById(`tab-${sector}`);
    if (activeTab) {
      activeTab.classList.remove("bg-gray-500", "text-gray-400", "hover:bg-gray-700");
      activeTab.classList.add("bg-cyan-400", "text-white");
    }
  };

  // select empleado
  window.selectEmployee = function () {
    const contenedor = document.getElementById("contenedor");
    const select = document.createElement("select");
    select.className =
      "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition";
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

  // descansos
  window.addDescanso = function (inicio = "", fin = "") {
    const container = document.getElementById("descansos-container");
    const id = descansosCount++;
    const html = `
      <div id="descanso-${id}" class="flex flex-col md:flex-row gap-3 items-center bg-gray-50 p-4 rounded-lg border">
        <input type="time" class="flex-1 border rounded px-2 py-1" value="${inicio}">
        <input type="time" class="flex-1 border rounded px-2 py-1" value="${fin}">
        <button type="button" onclick="removeDescanso(${id})"
                class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded">X</button>
      </div>`;
    container.insertAdjacentHTML("beforeend", html);
  };

  window.removeDescanso = function (id) {
    document.getElementById(`descanso-${id}`).remove();
  };

  // guardar agenda
  const agendaForm = document.getElementById("agenda-form");
  if (agendaForm) {
    agendaForm.addEventListener("submit", (e) => {
      e.preventDefault();
      document.getElementById("success-message").classList.remove("hidden");
      setTimeout(() => {
        document.getElementById("success-message").classList.add("hidden");
      }, 2000);
    });
  }
  // iniciar empleado select
  window.selectEmployee();
});
