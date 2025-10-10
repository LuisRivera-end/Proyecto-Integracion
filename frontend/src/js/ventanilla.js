const API_BASE_URL = window.location.hostname === "localhost" 
    ? "http://localhost:5000"
    : "http://backend:5000"; 

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

  // -----------------------------
  // LOGIN con backend
  // -----------------------------
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    try {
      const res = await fetch(`${API_BASE_URL}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json(); // ✅ Primero obtenemos la respuesta
      currentUser = {
        username: data.username,
        sector: data.sector,
        rol: data.rol
      };

      // ✅ Ahora sí, redirigimos según el rol
      if (data.rol === 1) {
        window.location.href = "admin.html";
      } else {
        window.location.href = "ventanilla.html";
      }

      currentUser = { username: data.username, sector: data.sector };

      loginScreen.classList.add("hidden");
      managementScreen.classList.remove("hidden");
      backButton.classList.add("hidden");

      userSector.textContent = currentUser.sector;
      userName.textContent = currentUser.username;

      fetchTickets();
    } catch (err) {
      console.error(err);
      loginError.classList.remove("hidden");
    }
  });

  // -----------------------------
  // LOGOUT
  // -----------------------------
  logoutBtn.addEventListener("click", () => {
    currentUser = null;
    loginForm.reset();
    loginScreen.classList.remove("hidden");
    managementScreen.classList.add("hidden");
    backButton.classList.remove("hidden");
  });

  // -----------------------------
  // OBTENER TICKETS DESDE BACKEND
  // -----------------------------
  async function fetchTickets() {
    if (!currentUser) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/tickets?sector=${encodeURIComponent(currentUser.sector)}`);
      if (!res.ok) throw new Error("No se pudieron obtener tickets");

      const tickets = await res.json();
      renderTickets(tickets);
    } catch (err) {
      console.error("Error al obtener tickets:", err);
    }
  }

  // -----------------------------
  // RENDERIZAR TICKETS
  // -----------------------------
  function renderTickets(tickets) {
    ticketsContainer.innerHTML = "";

    if (!tickets.length) {
      noTicketsMessage.classList.remove("hidden");
      return;
    } else {
      noTicketsMessage.classList.add("hidden");
    }

    tickets.forEach(ticket => {
      const div = document.createElement("div");
      div.className = "flex justify-between items-center p-4 bg-gray-50 border rounded-lg shadow-sm";
      div.innerHTML = `
        <div>
          <p class="font-semibold text-gray-800">Ticket: <span class="text-blue-600">${ticket.folio}</span></p>
          <p class="text-sm text-gray-600">Matrícula: ${ticket.matricula}</p>
        </div>
        <button class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg">Atender</button>
      `;

      div.querySelector("button").addEventListener("click", async () => {
        try {
          const res = await fetch(`${API_BASE_URL}/api/tickets/${ticket.folio}/attend`, {
            method: "POST"
          });
          if (!res.ok) throw new Error("No se pudo atender el ticket");

          fetchTickets(); // refrescar lista
        } catch (err) {
          console.error(err);
        }
      });

      div.querySelector(".complete-btn").addEventListener("click", async () => {
        try {
          const res = await fetch(`${API_BASE_URL}/api/tickets/${ticket.folio}/complete`, {
            method: "PUT"
          });
          if (!res.ok) throw new Error("No se pudo completar el ticket");

          fetchTickets(); // refrescar lista
        } catch (err) {
          console.error(err);
        }
      });

      ticketsContainer.appendChild(div);
    });
  }
});
