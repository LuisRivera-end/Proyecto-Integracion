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
  
    // usuarios 
    const users = {
      servicios: { password: "servicios123", sector: "Servicios Escolares" },
      becas: { password: "becas123", sector: "Becas" },
      cajas: { password: "cajas123", sector: "Cajas" },
    };
  
    // tickets echos para dar ejemplo se quitaran en un futurp
    let exampleTickets = [
      { folio: "A001", matricula: "21783", sector: "Servicios Escolares" },
      { folio: "B002", matricula: "69696", sector: "Becas" },
      { folio: "C003", matricula: "12345", sector: "Cajas" },
      { folio: "A004", matricula: "54321", sector: "Servicios Escolares" },
      { folio: "B005", matricula: "67891", sector: "Becas" },
    ];
  
    let currentUser = null;
  
    // renderizar tickets
    function renderTickets(sector) {
      ticketsContainer.innerHTML = "";
      const filtered = exampleTickets.filter((t) => t.sector === sector);
  
      if (filtered.length === 0) {
        noTicketsMessage.classList.remove("hidden");
      } else {
        noTicketsMessage.classList.add("hidden");
  
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
        userSector.textContent = currentUser.sector;
        userName.textContent = currentUser.username;
  
        loginScreen.classList.add("hidden");
        managementScreen.classList.remove("hidden");
        loginError.classList.add("hidden");
  
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
    });
  });
  
