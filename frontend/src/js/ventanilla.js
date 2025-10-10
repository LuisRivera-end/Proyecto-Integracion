document.addEventListener("DOMContentLoaded", () => {
  const loginScreen = document.getElementById("login-screen");
  const ventanillaSelectionScreen = document.getElementById("ventanilla-selection-screen");
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
          <button class="bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 rounded-lg">Atender</button>
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
      if (username === "admin") {
        window.location.href = "admin.html";
        return;
      }

      currentUser = { username, sector: users[username].sector };
      loginError.classList.add("hidden");
      loginScreen.classList.add("hidden");
      backButton.classList.add("hidden");

      if (username === "becas") {
        managementScreen.classList.remove("hidden");
        userSector.textContent = currentUser.sector;
        userName.textContent = currentUser.username;
        renderTickets(currentUser.sector);
      } else {
        ventanillaSelectionScreen.classList.remove("hidden");
      }

    } else {
      loginError.classList.remove("hidden");
    }
  });

  // seleccionar ventanilla
  document.querySelectorAll(".ventanilla-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const ventanilla = btn.getAttribute("data-ventanilla");
      currentUser.ventanilla = ventanilla;

      ventanillaSelectionScreen.classList.add("hidden");
      managementScreen.classList.remove("hidden");

      userSector.textContent = `${currentUser.sector} - Ventanilla ${ventanilla}`;
      userName.textContent = currentUser.username;

      renderTickets(currentUser.sector);
    });
  });

  // logout
  logoutBtn.addEventListener("click", () => {
    currentUser = null;
    loginForm.reset();
    managementScreen.classList.add("hidden");
    ventanillaSelectionScreen.classList.add("hidden");
    loginScreen.classList.remove("hidden");
    backButton.classList.remove("hidden");
  });
});
