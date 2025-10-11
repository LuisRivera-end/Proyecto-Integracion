document.addEventListener("DOMContentLoaded", function() {
    const API_BASE_URL = window.location.hostname === "localhost"
        ? "http://localhost:5000"
        : "http://backend:5000";

    // Referencias a elementos del DOM
    const tickets = document.getElementById("tickets");
    const contenedor = document.getElementById("contenedor");
    const sinTickets = document.getElementById("sinTickets");

    // Función para obtener los tickets desde la API
    async function obtenerTickets() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/tickets`);
            
            if (!response.ok) {
                throw new Error(`Error al obtener tickets: ${response.status}`);
            }

            const data = await response.json();
            console.log("Tickets obtenidos:", data); // Debug

            return data;
        } catch (error) {
            console.error("Error al cargar tickets:", error);
            return []; // Devuelve vacío si hay error
        }
    }

    // Función para cargar los tickets en la tabla
    async function cargarTickets() {
        // Limpia el contenedor antes de agregar nuevos tickets
        contenedor.innerHTML = "";

        // Obtener datos reales de la base de datos
        const ticketsData = await obtenerTickets();

        // Si no hay tickets, mostrar mensaje y ocultar tabla
        if (ticketsData.length === 0) {
            sinTickets.classList.remove("hidden");
            tickets.classList.add("hidden");
            return;
        }

        // Mostrar tabla y ocultar mensaje
        sinTickets.classList.add("hidden");
        tickets.classList.remove("hidden");

        // Recorrer los datos y crear las filas
        ticketsData.forEach((ticket, index) => {
            const fila = document.createElement("tr");

            // Alternar colores de fondo
            fila.classList.add(
                index % 2 === 0 ? "bg-slate-50" : "bg-white",
                "border-b", "border-slate-200",
                "hover:bg-slate-100", "transition-colors"
            );

            // Crear el contenido de la fila
            fila.innerHTML = `
                <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-emerald-700 font-bold text-xl sm:text-2xl">${ticket.folio}</td>
                <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">${ticket.sector}</td>
                <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">
                    ${ticket.id_turno ? `Ventanilla ${ticket.id_turno}` : "Por asignar"}
                </td>
            `;

            // Agregar la fila al contenedor
            contenedor.appendChild(fila);
        });
    }

    // Cargar los tickets al iniciar la página
    cargarTickets();

    // Exponer la función si deseas recargar externamente
    window.cargarTickets = cargarTickets;
});

