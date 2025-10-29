import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", async () => {
  const loginScreen = document.getElementById("login-screen");
   try {
        // Llamada POST para actualizar los estados según descansos activos hoy
        await fetch(`${API_BASE_URL}/api/employees/update-status`, { method: "POST" });
        console.log("Estados de empleados actualizados al abrir login");
    } catch (err) {
        console.error("No se pudieron actualizar los estados al abrir login:", err);
    }

  const managementScreen = document.getElementById("management-screen");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const userSector = document.getElementById("user-sector");
  const userName = document.getElementById("user-name");
  const logoutBtn = document.getElementById("logout-btn");
  const backButton = document.getElementById("back-Button");

  // Estos elementos se inicializarán cuando managementScreen esté visible
  let callNextBtn, completeCurrentBtn, cancelCurrentBtn, currentTicketSection, currentTicketFolio, currentTicketMatricula, currentTicketAlumno, ticketsContainer, noTicketsMessage;
  let normalTicketLayout, invitadoTicketLayout, currentTicketFolioInvitado, currentTicketInvitado; // NUEVAS VARIABLES

  let currentUser = null;
  let refreshInterval = null;
  let currentTicket = null;
 // -----------------------------
// INICIALIZAR ELEMENTOS DE MANAGEMENT SCREEN
// -----------------------------
function initializeManagementElements() {
    callNextBtn = document.getElementById("call-next-btn");
    completeCurrentBtn = document.getElementById("complete-current-btn");
    cancelCurrentBtn = document.getElementById("cancel-current-btn");
    currentTicketSection = document.getElementById("current-ticket-section");
    currentTicketFolio = document.getElementById("current-ticket-folio");
    currentTicketMatricula = document.getElementById("current-ticket-matricula");
    currentTicketAlumno = document.getElementById("current-ticket-alumno");
    ticketsContainer = document.getElementById("tickets-container");
    noTicketsMessage = document.getElementById("no-tickets-message");
    
    // NUEVOS ELEMENTOS PARA INVITADOS
    normalTicketLayout = document.getElementById("normal-ticket-layout");
    invitadoTicketLayout = document.getElementById("invitado-ticket-layout");
    currentTicketFolioInvitado = document.getElementById("current-ticket-folio-invitado");
    currentTicketInvitado = document.getElementById("current-ticket-invitado");

    // Verificar que todos los elementos existan
    if (!callNextBtn || !completeCurrentBtn || !cancelCurrentBtn || !currentTicketSection || 
        !currentTicketFolio || !currentTicketMatricula || !ticketsContainer || !currentTicketAlumno || 
        !noTicketsMessage || !normalTicketLayout || !invitadoTicketLayout || !currentTicketFolioInvitado || 
        !currentTicketInvitado) {
      console.error("No se pudieron encontrar todos los elementos de management screen");
      return false;
    }
    
    return true;
}

  // -----------------------------
  // LOGIN - CORREGIDO
  // -----------------------------
  const originalTitle = document.title;
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
          if (!ventanillaActivaRes.ok) {
              throw new Error("Error al verificar ventanilla del empleado");
          }

          const ventanillaActiva = await ventanillaActivaRes.json();
          if (ventanillaActiva && ventanillaActiva.ID_Ventanilla) {
              console.log("Usando ventanilla asignada:", ventanillaActiva);
              currentUser.ventanilla = {
                  id: ventanillaActiva.ID_Ventanilla,
                  nombre: ventanillaActiva.Ventanilla
              };

              loginScreen.classList.add("hidden");
              managementScreen.classList.remove("hidden");
              backButton.classList.add("hidden");
              loginError.classList.add("hidden");

              if (initializeManagementElements()) {
                  if (currentUser.rol !== 1) {
                    document.title = `${currentUser.sector} - ${currentUser.username}`;
                  }
                  userSector.textContent = `${currentUser.sector} - ${currentUser.ventanilla.nombre}`;
                  userName.textContent = currentUser.username;
                  setupEventListeners();
                  startTicketPolling();
              } else {
                  throw new Error("Error al inicializar la interfaz");
              }
              return;
          }

          alert("No tienes una ventanilla asignada. Contacta al administrador.");
          return;

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
  // CONFIGURAR EVENT LISTENERS
  // -----------------------------
  function setupEventListeners() {
    if (callNextBtn) {
      callNextBtn.addEventListener("click", llamarSiguienteTicket);
    }
    
    if (completeCurrentBtn) {
      completeCurrentBtn.addEventListener("click", completarTicketActual);
    }
    
    // NUEVO EVENT LISTENER PARA CANCELAR TICKET
    if (cancelCurrentBtn) {
      cancelCurrentBtn.addEventListener("click", cancelarTicketActual);
    }
    
    if (logoutBtn) {
      logoutBtn.addEventListener("click", cerrarSesion);
    }
  }

// -----------------------------
// LLAMAR SIGUIENTE TICKET - VERSIÓN CORREGIDA CON SOPORTE PARA INVITADOS
// -----------------------------
async function llamarSiguienteTicket() {
    if (!currentUser?.ventanilla) return;
    
    if (currentTicket) {
      alert("Debes completar o cancelar el ticket actual antes de llamar al siguiente.");
      return;
    }

    try {
      // Llamar al ticket directamente
      const res = await fetch(`${API_BASE_URL}/api/tickets/llamar-siguiente`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          id_ventanilla: currentUser.ventanilla.id,
          id_empleado: currentUser.id
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "No se pudo llamar siguiente ticket");
      }
      
      const data = await res.json();
      
      // USAR LA INFORMACIÓN COMPLETA QUE DEVUELVE EL BACKEND
      currentTicket = {
        folio: data.folio,
        matricula: data.matricula || null,
        nombre_alumno: data.nombre_alumno || 'Invitado',
        tipo: data.tipo || 'normal' // 'normal' o 'invitado'
      };
      
      console.log("Ticket actual establecido:", currentTicket);
      
      // Actualizar interfaz
      updateCurrentTicketUI();
      callNextBtn.disabled = true;
      callNextBtn.classList.add("opacity-50", "cursor-not-allowed");
      completeCurrentBtn.classList.remove("hidden");
      cancelCurrentBtn.classList.remove("hidden");
      currentTicketSection.classList.remove("hidden");
      
      // Recargar lista de tickets pendientes
      await fetchTickets();
      
    } catch (err) {
      console.error("Error al llamar siguiente ticket:", err);
      alert(err.message || "Error al llamar siguiente ticket");
    }
}

// -----------------------------
// OBTENER INFORMACIÓN DEL SIGUIENTE TICKET - NUEVA FUNCIÓN
// -----------------------------
async function getNextTicketInfo() {
  try {
    const allTickets = await getAllTickets();
    // El primer ticket de la lista es el siguiente en ser atendido (ordenado por fecha más antigua)
    return allTickets.length > 0 ? allTickets[0] : null;
  } catch (err) {
    console.error("Error al obtener siguiente ticket:", err);
    return null;
  }
}

  // -----------------------------
  // OBTENER INFORMACIÓN DEL TICKET
  // -----------------------------
  async function getTicketInfo(folio) {
    try {
      const allTickets = await getAllTickets();
      const ticket = allTickets.find(t => {
        const ticketFolio = t.folio || t.Folio || t.ID_Ticket;
        return ticketFolio === folio;
      });
      return ticket || null;
    } catch (err) {
      console.error("Error al obtener info del ticket:", err);
      return null;
    }
  }

  async function getAllTickets() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/tickets?sector=${encodeURIComponent(currentUser.sector)}`);
      
      if (!res.ok) {
        console.error("Error al obtener tickets:", res.status);
        return [];
      }
      
      const tickets = await res.json();
      console.log("Respuesta de tickets:", tickets);
      
      if (Array.isArray(tickets)) {
        return tickets;
      } else if (tickets && Array.isArray(tickets.tickets)) {
        return tickets.tickets;
      } else if (tickets && Array.isArray(tickets.data)) {
        return tickets.data;
      }
      
      return [];
      
    } catch (err) {
      console.error("Error en getAllTickets:", err);
      return [];
    }
  }

// -----------------------------
// ACTUALIZAR UI DEL TICKET ACTUAL - MODIFICADO PARA INVITADOS
// -----------------------------
function updateCurrentTicketUI() {
    if (!currentTicket) return;
    
    // Mostrar información según el tipo de ticket
    if (currentTicket.tipo === 'invitado' || currentTicket.nombre_alumno === 'Invitado') {
        // Es un turno invitado - Mostrar layout de 2 columnas
        normalTicketLayout.classList.add("hidden");
        invitadoTicketLayout.classList.remove("hidden");
        
        currentTicketFolioInvitado.textContent = currentTicket.folio;
        currentTicketInvitado.textContent = 'Invitado';
        
    } else {
        // Es un turno normal - Mostrar layout de 3 columnas
        invitadoTicketLayout.classList.add("hidden");
        normalTicketLayout.classList.remove("hidden");
        
        currentTicketFolio.textContent = currentTicket.folio;
        currentTicketMatricula.textContent = currentTicket.matricula || 'N/A';
        currentTicketAlumno.textContent = currentTicket.nombre_alumno;
    }
}


  // -----------------------------
  // COMPLETAR TICKET ACTUAL
  // -----------------------------
  async function completarTicketActual() {
    if (!currentTicket) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/tickets/${currentTicket.folio}/complete`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" }
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "No se pudo completar el ticket");
      }

      const completedFolio = currentTicket.folio;
      currentTicket = null;
      
      resetCurrentTicketUI();
      await fetchTickets();
      
      alert(`Ticket ${completedFolio} completado exitosamente`);
      
    } catch (err) {
      console.error("Error al completar ticket:", err);
      alert(err.message || "Error al completar el ticket");
    }
  }

   // -----------------------------
  // CANCELAR TICKET ACTUAL - NUEVA FUNCIÓN
  // -----------------------------
  async function cancelarTicketActual() {
    if (!currentTicket) return;

    if (!confirm(`¿Estás seguro de que deseas cancelar el ticket ${currentTicket.folio}?`)) {
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/tickets/${currentTicket.folio}/cancel`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" }
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "No se pudo cancelar el ticket");
      }

      const canceledFolio = currentTicket.folio;
      currentTicket = null;
      
      resetCurrentTicketUI();
      await fetchTickets();
      
      alert(`Ticket ${canceledFolio} cancelado exitosamente`);
      
    } catch (err) {
      console.error("Error al cancelar ticket:", err);
      alert(err.message || "Error al cancelar el ticket");
    }
  }

 // -----------------------------
// RESET UI DEL TICKET ACTUAL - MODIFICADO
// -----------------------------
function resetCurrentTicketUI() {
    callNextBtn.disabled = false;
    callNextBtn.classList.remove("opacity-50", "cursor-not-allowed");
    completeCurrentBtn.classList.add("hidden");
    cancelCurrentBtn.classList.add("hidden");
    currentTicketSection.classList.add("hidden");
    
    // Ocultar ambos layouts
    normalTicketLayout.classList.add("hidden");
    invitadoTicketLayout.classList.add("hidden");
}


  // -----------------------------
  // POLLING PARA TICKETS
  // -----------------------------
  function startTicketPolling() {
    fetchTickets();
    refreshInterval = setInterval(fetchTickets, 5000);
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

    if (!ticketsContainer) {
      console.error("ticketsContainer no disponible");
      return;
    }

    try {
      const allTickets = await getAllTickets();
      renderTickets(allTickets, currentUser.sector);
    } catch (err) {
      console.error("Error al obtener tickets:", err);
      if (ticketsContainer) {
        ticketsContainer.innerHTML = `
          <div class="text-center py-8 text-red-600">
            <p>Error al cargar tickets: ${err.message}</p>
          </div>
        `;
      }
      if (noTicketsMessage) {
        noTicketsMessage.classList.add("hidden");
      }
    }
  }

 // -----------------------------
// RENDERIZAR TICKETS - MODIFICADO PARA INVITADOS
// -----------------------------
function renderTickets(tickets, sector) {
    if (!ticketsContainer || !noTicketsMessage) {
      console.error("Elementos del DOM no disponibles");
      return;
    }

    ticketsContainer.innerHTML = "";

    const normSector = String(sector ?? "").trim().toLowerCase();
    const pendientes = tickets.filter(t => {
      if (!t) return false;
      if (t.sector == null) return false;
      
      const ticketSector = String(t.sector).trim().toLowerCase();
      const isCorrectSector = ticketSector === normSector;
      const isPending = t.estado_id === 1 || t.ID_Estados === 1 || 
                        String(t.estado || '').toLowerCase().includes('pendiente');
      
      const isCurrentTicket = currentTicket && (t.folio || t.Folio || t.ID_Ticket) === currentTicket.folio;
      
      return isCorrectSector && isPending && !isCurrentTicket;
    });

    if (!pendientes.length) {
      noTicketsMessage.classList.remove("hidden");
      ticketsContainer.classList.add("hidden");
    } else {
      noTicketsMessage.classList.add("hidden");
      ticketsContainer.classList.remove("hidden");
      
      pendientes.forEach(ticket => {
        const div = document.createElement("div");
        div.className = "p-4 bg-gray-50 border rounded-lg shadow-sm";
        
        const ticketId = ticket.folio || ticket.Folio || ticket.ID_Ticket;
        const esInvitado = ticket.tipo === 'invitado' || ticket.nombre_alumno === 'Invitado' || !ticket.matricula;
        
        div.innerHTML = `
          <div class="text-center">
            <p class="font-semibold text-gray-800">
              Ticket: <span class="text-blue-600">${ticketId}</span>
            </p>
            <p class="text-sm ${esInvitado ? 'text-blue-600 font-semibold' : 'text-gray-600'} mt-1">
              ${esInvitado ? 'Turno Invitado' : `Matrícula: ${ticket.matricula}`}
            </p>
            <p class="text-xs text-gray-500 mt-1">
              Estado: <span class="text-orange-500">${ticket.estado || 'Pendiente'}</span>
            </p>
          </div>
        `;

        ticketsContainer.appendChild(div);
      });
    }
}


  // -----------------------------
  // CERRAR SESIÓN
  // -----------------------------
  async function cerrarSesion() {
    stopTicketPolling();
    document.title = originalTitle;

    currentUser = null;
    currentTicket = null;
    loginForm.reset();
    managementScreen.classList.add("hidden");
    loginScreen.classList.remove("hidden");
    backButton.classList.remove("hidden");
    
    console.log("Sesión cerrada en el frontend");
  }
});