const API_BASE_URL = "https://localhost:4443";

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

        // VERIFICAR SI YA TIENE VENTANILLA ASIGNADA Y ACTIVA
        const ventanillaActivaRes = await fetch(`${API_BASE_URL}/api/empleado/${currentUser.id}/ventanilla-activa`);
        
        if (ventanillaActivaRes.ok) {
            const ventanillaActiva = await ventanillaActivaRes.json();
            
            if (ventanillaActiva && ventanillaActiva.ID_Ventanilla) {
                // YA TIENE VENTANILLA ASIGNADA - USAR ESA
                console.log("Usando ventanilla asignada:", ventanillaActiva);
                currentUser.ventanilla = {
                    id: ventanillaActiva.ID_Ventanilla,
                    nombre: ventanillaActiva.Ventanilla
                };
                
                // Ir directamente a la pantalla de gestión
                loginScreen.classList.add("hidden");
                managementScreen.classList.remove("hidden");
                backButton.classList.add("hidden");
                loginError.classList.add("hidden");
                
                userSector.textContent = `${currentUser.sector} - ${currentUser.ventanilla.nombre}`;
                userName.textContent = currentUser.username;
                startTicketPolling();
                return;
            }
        }

        // SI NO TIENE VENTANILLA ASIGNADA, buscar una automáticamente
        loginScreen.classList.add("hidden");
        managementScreen.classList.remove("hidden");
        backButton.classList.add("hidden");
        loginError.classList.add("hidden");

        await iniciarVentanilla(); // Asignación automática
        
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
async function iniciarVentanilla() {
    try {
        console.log("Buscando ventanilla libre para empleado:", currentUser.id);

        // PRIMERO: Obtener una ventanilla libre para este empleado
        const ventanillasRes = await fetch(`${API_BASE_URL}/api/ventanillas/libres/${currentUser.id}`);
        
        if (!ventanillasRes.ok) {
            throw new Error("No se pudieron obtener ventanillas libres");
        }

        const ventanillasLibres = await ventanillasRes.json();
        console.log("Ventanillas libres:", ventanillasLibres);

        if (!ventanillasLibres || ventanillasLibres.length === 0) {
            throw new Error("No hay ventanillas disponibles para tu rol. Contacta al administrador.");
        }

        // Tomar la primera ventanilla libre disponible
        const ventanillaAsignada = ventanillasLibres[0];
        const idVentanilla = ventanillaAsignada.ID_Ventanilla;

        console.log("Asignando ventanilla automáticamente:", {
            empleado: currentUser.id,
            ventanilla: idVentanilla
        });

        // SEGUNDO: Iniciar la ventanilla seleccionada
        const res = await fetch(`${API_BASE_URL}/api/ventanilla/iniciar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                id_empleado: currentUser.id, 
                id_ventanilla: idVentanilla 
            })
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.error || "No se pudo iniciar ventanilla");
        }

        console.log("Ventanilla iniciada:", data);

        // Usar la información que devuelve el backend
        currentUser.ventanilla = { 
            id: data.ID_Ventanilla || idVentanilla, 
            nombre: data.Nombre_Ventanilla || ventanillaAsignada.Ventanilla
        };

        // Actualizar la interfaz
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
      
      renderTickets(tickets, currentUser.sector);
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
function renderTickets(tickets, sector) {
  ticketsContainer.innerHTML = "";

  // Normalizamos el sector del usuario para comparar
  const normSector = String(sector ?? "").trim().toLowerCase();

  // Aceptamos varias estructuras de respuesta: array directo o { tickets: [...] } o { data: [...] }
  let list = [];
  if (Array.isArray(tickets)) {
    list = tickets;
  } else if (tickets && Array.isArray(tickets.tickets)) {
    list = tickets.tickets;
  } else if (tickets && Array.isArray(tickets.data)) {
    list = tickets.data;
  } else {
    console.warn("renderTickets: estructura de 'tickets' inesperada:", tickets);
  }

  console.log("renderTickets -> lista normalizada:", list);
  console.log("renderTickets -> sector usuario normalizado:", normSector);

  // Filtramos por sector (normalizado: string, trim, lowercase)
  const visibles = list.filter(t => {
    if (!t) return false;
    // Si no tiene sector, lo descartamos (puedes cambiar la lógica si quieres incluirlos)
    if (t.sector == null) return false;
    return String(t.sector).trim().toLowerCase() === normSector;
  });

  console.log("Tickets visibles tras filtrar:", visibles);

  if (!visibles.length) {
    // no hay tickets para este sector
    noTicketsMessage.classList.remove("hidden");
    return;
  }

  noTicketsMessage.classList.add("hidden");

  visibles.forEach(ticket => {
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
        <p class="text-xs text-gray-500 mt-1">
          Sector: ${ticket.sector || 'N/A'}
        </p>
      </div>
      <button class="attend-btn bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors font-medium">
        Atender
      </button>
    `;

    const ticketId = ticket.folio || ticket.ID_Ticket;

    const btn = div.querySelector(".attend-btn");
    if (btn) {
      btn.addEventListener("click", async () => {
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
    } else {
      console.warn("No se encontró el botón attend-btn en ticket:", ticket);
    }

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