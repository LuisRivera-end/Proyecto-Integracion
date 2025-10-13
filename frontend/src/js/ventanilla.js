const API_BASE_URL = window.location.hostname === "localhost" 
    ? "http://localhost:5000"
    : "http://backend:5000";

document.addEventListener("DOMContentLoaded", () => {
  const loginScreen = document.getElementById("login-screen");
  //const ventanillaSelectionScreen = document.getElementById("ventanilla-selection-screen"); // ELIMINADA
  const managementScreen = document.getElementById("management-screen");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const userSector = document.getElementById("user-sector");
  const userName = document.getElementById("user-name");
  const logoutBtn = document.getElementById("logout-btn");
  const callNextBtn = document.getElementById("call-next-btn");
  const ticketsContainer = document.getElementById("tickets-container");
  const noTicketsMessage = document.getElementById("no-tickets-message");
  const backButton = document.getElementById("back-Button");

  let currentUser = null;
  let refreshInterval = null;

  // -----------------------------
  // LOGIN - CORREGIDO
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
        
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.error || "Credenciales incorrectas");
        }
        
        const data = await res.json();
        currentUser = { 
            id: data.id, 
            username: data.nombre, 
            rol: data.rol, 
            sector: data.sector 
        };

        // Admin va directo a admin.html
        if (currentUser.rol === 1) {
            window.location.href = "admin.html";
            return;
        }

        // Si no es admin, ir directamente a iniciar la ventanilla
        loginScreen.classList.add("hidden");
        managementScreen.classList.remove("hidden"); // Muestra directamente la gestión
        backButton.classList.add("hidden");
        loginError.classList.add("hidden");

        // Llama a iniciarVentanilla con ID 0 para asignación automática
        await iniciarVentanilla(0, "Automática");
        
    } catch (err) {
        console.error("Error en login:", err);
        loginError.textContent = err.message;
        loginError.classList.remove("hidden");
    }
});

  // -----------------------------
  // CARGAR VENTANILLAS LIBRES - ELIMINADA
  // -----------------------------
  /* La función cargarVentanillas se elimina por completo */
  
// -----------------------------
// INICIAR VENTANILLA - CORREGIDO
// -----------------------------
// Se eliminó la línea "iniciarVentanilla(ventanilla.id, ventanilla.nombre);"
async function iniciarVentanilla(idVentanilla, nombreVentanilla) {
    try {
        console.log("Intentando iniciar ventanilla:", {
            empleado: currentUser.id,
            ventanilla: idVentanilla,
            nombre: nombreVentanilla
        });

        const res = await fetch(`${API_BASE_URL}/api/ventanilla/iniciar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                id_empleado: currentUser.id, 
                id_ventanilla: idVentanilla 
            })
        });
        
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.error || "No se pudo iniciar ventanilla");
        }

        const data = await res.json();
        console.log("Ventanilla iniciada:", data.message);

        // **MODIFICACIÓN CLAVE: Obtener ID y Nombre de la ventanilla asignada del backend**
        const assignedVentanillaId = data.ID_Ventanilla; 
        const assignedVentanillaNombre = data.Nombre_Ventanilla; 
        
        if (!assignedVentanillaId) {
             throw new Error("El sistema no pudo asignar una ventanilla disponible. El backend no devolvió una asignación válida.");
        }
        
        currentUser.ventanilla = { 
            id: assignedVentanillaId, 
            nombre: assignedVentanillaNombre
        };

        // Ya se mostró managementScreen en el login

        userSector.textContent = `${currentUser.sector} - ${currentUser.ventanilla.nombre}`;
        userName.textContent = currentUser.username;

        // Iniciar polling para actualizar tickets automáticamente
        startTicketPolling();

    } catch (err) {
        console.error("Error al iniciar ventanilla:", err);
        alert(`Error al iniciar ventanilla: ${err.message}. Por favor, cierra sesión e intenta de nuevo.`);
        
        // Regresar a la pantalla de login si falla la inicialización
        managementScreen.classList.add("hidden");
        loginScreen.classList.remove("hidden");
        backButton.classList.remove("hidden");
    }
}

  // -----------------------------
  // LLAMAR SIGUIENTE TICKET
  // -----------------------------
  callNextBtn.addEventListener("click", async () => {
    if (!currentUser?.ventanilla) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/tickets/llamar-siguiente`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          id_ventanilla: currentUser.ventanilla.id,
          id_empleado: currentUser.id 
        })
      });

      if (!res.ok) throw new Error("No se pudo llamar siguiente ticket");
      
      // Recargar tickets después de llamar
      await fetchTickets();
      
    } catch (err) {
      console.error("Error al llamar siguiente ticket:", err);
      alert("Error al llamar siguiente ticket");
    }
  });

  // -----------------------------
  // POLLING PARA TICKETS
  // -----------------------------
  function startTicketPolling() {
    // Cargar tickets inmediatamente
    fetchTickets();
    
    // Actualizar cada 5 segundos
    refreshInterval = setInterval(fetchTickets, 1000);
  }

  function stopTicketPolling() {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  }

  // -----------------------------
  // FETCH TICKETS
  // -----------------------------
  async function fetchTickets() {
    if (!currentUser || !currentUser.sector) {
      console.error("Usuario o sector no definido");
      return;
    }

    try {
      console.log("Buscando tickets para sector:", currentUser.sector);
      
      const res = await fetch(`${API_BASE_URL}/api/tickets?sector=${encodeURIComponent(currentUser.sector)}`);
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const tickets = await res.json();
      console.log("Tickets recibidos:", tickets);
      
      renderTickets(tickets);
    } catch (err) {
      console.error("Error al obtener tickets:", err);
      // Mostrar mensaje de error en la interfaz
      ticketsContainer.innerHTML = `
        <div class="text-center py-8 text-red-600">
          <p>Error al cargar tickets: ${err.message}</p>
        </div>
      `;
      noTicketsMessage.classList.add("hidden");
    }
  }

  // -----------------------------
  // RENDERIZAR TICKETS
  // -----------------------------
  function renderTickets(tickets) {
    ticketsContainer.innerHTML = "";

    if (!tickets || !tickets.length) {
      noTicketsMessage.classList.remove("hidden");
      return;
    }
    
    noTicketsMessage.classList.add("hidden");

    tickets.forEach(ticket => {
      const div = document.createElement("div");
      div.className = "flex justify-between items-center p-4 bg-gray-50 border rounded-lg shadow-sm hover:shadow-md transition-shadow";
      div.innerHTML = `
        <div class="flex-1">
          <p class="font-semibold text-gray-800">
            Ticket: <span class="text-blue-600">${ticket.folio || ticket.ID_Ticket}</span>
          </p>
          <p class="text-sm text-gray-600 mt-1">
            Matrícula: ${ticket.matricula || 'N/A'}
          </p>
          <p class="text-xs text-gray-500 mt-1">
            Estado: ${ticket.estado || 'Pendiente'}
          </p>
        </div>
        <button class="attend-btn bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors font-medium">
          Atender
        </button>
      `;

      const ticketId = ticket.folio || ticket.ID_Ticket;
      
      div.querySelector(".attend-btn").addEventListener("click", async () => {
        try {
          const res = await fetch(`${API_BASE_URL}/api/tickets/${ticketId}/attend`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
              id_ventanilla: currentUser.ventanilla.id,
              id_empleado: currentUser.id 
            })
          });
          
          if (!res.ok) throw new Error("No se pudo atender el ticket");
          
          await fetchTickets(); // Recargar lista después de atender
          
        } catch (err) {
          console.error("Error al atender ticket:", err);
          alert("Error al atender el ticket");
        }
      });

      ticketsContainer.appendChild(div);
    });
  }

  // -----------------------------
  // CERRAR SESIÓN - CORREGIDO
  // -----------------------------
logoutBtn.addEventListener("click", async () => {
    // Detener el polling de tickets
    stopTicketPolling();

    if (currentUser?.ventanilla) {
        try {
            console.log("Cerrando ventanilla para empleado:", currentUser.id);
            
            const res = await fetch(`${API_BASE_URL}/api/ventanilla/cerrar`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_empleado: currentUser.id })
            });

            if (!res.ok) {
                const errorData = await res.json();
                console.error("Error del servidor al cerrar ventanilla:", errorData);
                // Aún así continuamos con el cierre de sesión en el frontend
            } else {
                const data = await res.json();
                console.log("Ventanilla cerrada:", data.message);
            }
        } catch (err) {
            console.error("Error al liberar ventanilla:", err);
            // Aún así continuamos con el cierre de sesión en el frontend
        }
    }

    // Limpiar el estado local
    currentUser = null;
    loginForm.reset();
    managementScreen.classList.add("hidden");
    // ventanillaSelectionScreen.classList.add("hidden"); // ELIMINADA
    loginScreen.classList.remove("hidden");
    backButton.classList.remove("hidden");
    
    console.log("Sesión cerrada en el frontend");
  });
});