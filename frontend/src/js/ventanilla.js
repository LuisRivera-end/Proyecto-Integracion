import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", async () => {
    // Verificar sesión
    const storedUser = localStorage.getItem('currentUser');
    if (!storedUser) {
        window.location.href = "login.html";
        return;
    }

    let currentUser = null;
    try {
        currentUser = JSON.parse(storedUser);
    } catch (e) {
        console.error("Error parsing stored user", e);
        window.location.href = "login.html";
        return;
    }

    // Elementos de la UI
    const managementScreen = document.getElementById("management-screen"); // En gestion.html el id es management-screen
    const userSector = document.getElementById("user-sector");
    const userName = document.getElementById("user-name");
    const logoutBtn = document.getElementById("logout-btn");
    
    // Variables de estado
    let callNextBtn, completeCurrentBtn, cancelCurrentBtn, currentTicketSection;
    let currentTicketFolio, currentTicketMatricula, currentTicketAlumno, ticketsContainer, noTicketsMessage;
    let normalTicketLayout, invitadoTicketLayout, currentTicketFolioInvitado, currentTicketInvitado;
    
    let refreshInterval = null;
    let currentTicket = null;

    // Inicializar UI
    if (managementScreen) {
        managementScreen.classList.remove("hidden");
    }
    
    // Inicializar referencias a elementos
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
        
        // ELEMENTOS PARA INVITADOS
        normalTicketLayout = document.getElementById("normal-ticket-layout");
        invitadoTicketLayout = document.getElementById("invitado-ticket-layout");
        currentTicketFolioInvitado = document.getElementById("current-ticket-folio-invitado");
        currentTicketInvitado = document.getElementById("current-ticket-invitado");

        // Verificar existencia
        if (!callNextBtn || !ticketsContainer) {
            console.error("No se pudieron encontrar algunos elementos de la interfaz");
            return false;
        }
        return true;
    }

    if (initializeManagementElements()) {
        // Mostrar info del usuario
        if (userSector) {
            if (currentUser.ventanilla) {
                userSector.textContent = `${currentUser.sector} - ${currentUser.ventanilla.nombre}`;
            } else {
                userSector.textContent = currentUser.sector;
                // Si es jefe y no tiene ventanilla, ocultar botón de llamar
                if (currentUser.rol === 6 && callNextBtn) {
                   callNextBtn.classList.add("hidden");
                }
            }
        }
        if (userName) {
            userName.textContent = currentUser.username;
        }
        
        setupEventListeners();
        startTicketPolling();
    }

    // -----------------------------
    // CONFIGURAR EVENT LISTENERS
    // -----------------------------
    function setupEventListeners() {
        if (callNextBtn) callNextBtn.addEventListener("click", llamarSiguienteTicket);
        if (completeCurrentBtn) completeCurrentBtn.addEventListener("click", completarTicketActual);
        if (cancelCurrentBtn) cancelCurrentBtn.addEventListener("click", cancelarTicketActual);
        if (logoutBtn) logoutBtn.addEventListener("click", cerrarSesion);
    }

    // -----------------------------
    // LLAMAR SIGUIENTE TICKET
    // -----------------------------
    async function llamarSiguienteTicket() {
        if (!currentUser?.ventanilla) return;
        
        if (currentTicket) {
            alert("Debes completar o cancelar el ticket actual antes de llamar al siguiente.");
            return;
        }

        try {
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
            
            currentTicket = {
                folio: data.folio,
            };
            
            console.log("Ticket actual establecido:", currentTicket);
            updateCurrentTicketUI();
            
            // Actualizar estado botones
            callNextBtn.disabled = true;
            callNextBtn.classList.add("opacity-50", "cursor-not-allowed");
            completeCurrentBtn.classList.remove("hidden");
            cancelCurrentBtn.classList.remove("hidden");
            currentTicketSection.classList.remove("hidden");
            
            await fetchTickets();
            
        } catch (err) {
            console.error("Error al llamar siguiente ticket:", err);
            alert(err.message || "Error al llamar siguiente ticket");
        }
    }

    // -----------------------------
    // ACTUALIZAR UI DEL TICKET ACTUAL
    // -----------------------------
    function updateCurrentTicketUI() {
        if (!currentTicket) return;
        
        if (currentTicketFolio) currentTicketFolio.textContent = currentTicket.folio;
        
        // Show/hide layouts only if elements exist
        if (normalTicketLayout) normalTicketLayout.classList.remove("hidden");
        if (invitadoTicketLayout) invitadoTicketLayout.classList.add("hidden");
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
    // CANCELAR TICKET ACTUAL
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
    // RESET UI DEL TICKET ACTUAL
    // -----------------------------
    function resetCurrentTicketUI() {
        callNextBtn.disabled = false;
        callNextBtn.classList.remove("opacity-50", "cursor-not-allowed");
        completeCurrentBtn.classList.add("hidden");
        cancelCurrentBtn.classList.add("hidden");
        currentTicketSection.classList.add("hidden");
        
        if (normalTicketLayout) normalTicketLayout.classList.add("hidden");
        if (invitadoTicketLayout) invitadoTicketLayout.classList.add("hidden");
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

    async function getAllTickets() {
        try {
            const res = await fetch(`${API_BASE_URL}/api/tickets?sector=${encodeURIComponent(currentUser.sector)}`);
            if (!res.ok) return [];
            
            const tickets = await res.json();
            if (Array.isArray(tickets)) return tickets;
            else if (tickets && Array.isArray(tickets.tickets)) return tickets.tickets;
            else if (tickets && Array.isArray(tickets.data)) return tickets.data;
            return [];
        } catch (err) {
            console.error("Error en getAllTickets:", err);
            return [];
        }
    }

    async function fetchTickets() {
        if (!currentUser || !currentUser.sector || !ticketsContainer) return;

        try {
            const allTickets = await getAllTickets();
            renderTickets(allTickets, currentUser.sector);
        } catch (err) {
            console.error("Error al obtener tickets:", err);
            if (ticketsContainer) {
                ticketsContainer.innerHTML = `<div class="text-center py-8 text-red-600"><p>Error al cargar tickets</p></div>`;
            }
        }
    }

    function renderTickets(tickets, sector) {
        if (!ticketsContainer || !noTicketsMessage) return;

        ticketsContainer.innerHTML = "";
        const normSector = String(sector ?? "").trim().toLowerCase();
        
        const pendientes = tickets.filter(t => {
            if (!t || t.sector == null) return false;
            const ticketSector = String(t.sector).trim().toLowerCase();
            const isCorrectSector = ticketSector === normSector;
            const isPending = t.estado_id === 1 || t.ID_Estados === 1 || String(t.estado || '').toLowerCase().includes('pendiente');
            const isCurrentTicket = currentTicket && (t.folio || t.ID_Ticket) === currentTicket.folio;
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
    function cerrarSesion() {
        stopTicketPolling();
        localStorage.removeItem('currentUser');
        window.location.href = "login.html";
    }
});