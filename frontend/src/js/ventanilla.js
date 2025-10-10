const API_BASE_URL = window.location.hostname === "localhost" 
    ? "http://localhost:5000"
    : "http://backend:5000";

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

  // -----------------------------
  // LOGIN
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
      if (!res.ok) throw new Error("Credenciales incorrectas");
      
      const data = await res.json();
      currentUser = { id: data.id, username: data.nombre, rol: data.rol, sector: data.sector };

      // Admin va directo a admin.html
      if (currentUser.rol === 1) {
        window.location.href = "admin.html";
        return;
      }

      // Si no es admin, mostrar selección de ventanilla
      loginScreen.classList.add("hidden");
      ventanillaSelectionScreen.classList.remove("hidden");
      backButton.classList.add("hidden");

      loginError.classList.add("hidden");

      await cargarVentanillas(currentUser.rol);
    } catch (err) {
      console.error(err);
      loginError.classList.remove("hidden");
    }
  });

  // -----------------------------
  // CARGAR VENTANILLAS LIBRES
  // -----------------------------
async function cargarVentanillas(id_empleado) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/ventanillas/libres/${id_empleado}`);
    if (!res.ok) throw new Error("No se pudieron cargar ventanillas");
    const ventanillas = await res.json();

    const container = ventanillaSelectionScreen.querySelector(".grid");
    container.innerHTML = "";

    ventanillas.forEach(v => {
      const btn = document.createElement("button");
      btn.className = "ventanilla-btn bg-slate-600 hover:bg-slate-700 text-white font-semibold py-3 rounded-xl transition-all duration-300 shadow-md hover:shadow-lg";
      btn.textContent = v.Ventanilla;
      btn.setAttribute("data-ventanilla", v.ID_Ventanilla);

      btn.addEventListener("click", () => iniciarVentanilla(v.ID_Ventanilla, v.Ventanilla));
      container.appendChild(btn);
    });

  } catch (err) {
    console.error("Error al cargar ventanillas:", err);
  }
}


  // -----------------------------
  // INICIAR VENTANILLA
  // -----------------------------
  async function iniciarVentanilla(idVentanilla, nombreVentanilla) {
    try {
      const res = await fetch(`${API_BASE_URL}/api/ventanilla/iniciar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_empleado: currentUser.id, id_ventanilla: idVentanilla })
      });
      if (!res.ok) throw new Error("No se pudo iniciar ventanilla");

      currentUser.ventanilla = { id: idVentanilla, nombre: nombreVentanilla };

      ventanillaSelectionScreen.classList.add("hidden");
      managementScreen.classList.remove("hidden");

      userSector.textContent = `${currentUser.sector} - ${nombreVentanilla}`;
      userName.textContent = currentUser.username;

      fetchTickets();
    } catch (err) {
      console.error(err);
      alert("Ventanilla ocupada o error al iniciar sesión.");
      cargarVentanillas(currentUser.rol);
    }
  }

  // -----------------------------
  // CERRAR SESIÓN
  // -----------------------------
  logoutBtn.addEventListener("click", async () => {
    if (currentUser?.ventanilla) {
      // liberar ventanilla
      try {
        await fetch(`${API_BASE_URL}/api/ventanilla/cerrar`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id_empleado: currentUser.id })
        });
      } catch (err) {
        console.error("Error al liberar ventanilla:", err);
      }
    }

    currentUser = null;
    loginForm.reset();
    managementScreen.classList.add("hidden");
    loginScreen.classList.remove("hidden");
    backButton.classList.remove("hidden");
  });

  // -----------------------------
  // FETCH TICKETS
  // -----------------------------
  async function fetchTickets() {
    if (!currentUser || !currentUser.ventanilla) return;

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
    }
    noTicketsMessage.classList.add("hidden");

    tickets.forEach(ticket => {
      const div = document.createElement("div");
      div.className = "flex justify-between items-center p-4 bg-gray-50 border rounded-lg shadow-sm";
      div.innerHTML = `
        <div>
          <p class="font-semibold text-gray-800">Ticket: <span class="text-blue-600">${ticket.folio}</span></p>
          <p class="text-sm text-gray-600">Matrícula: ${ticket.matricula}</p>
        </div>
        <button class="attend-btn bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg">Atender</button>
      `;

      div.querySelector(".attend-btn").addEventListener("click", async () => {
        try {
          const res = await fetch(`${API_BASE_URL}/api/tickets/${ticket.folio}/attend`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_ventanilla: currentUser.ventanilla.id })
          });
          if (!res.ok) throw new Error("No se pudo atender el ticket");
          fetchTickets();
        } catch (err) {
          console.error(err);
        }
      });

      ticketsContainer.appendChild(div);
    });
  }
});