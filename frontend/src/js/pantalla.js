import Config from './config.js';

document.addEventListener("DOMContentLoaded", function() {
    const API_BASE_URL = Config.API_BASE_URL;

    // Referencias a elementos del DOM
    const tickets = document.getElementById("tickets");
    const contenedor = document.getElementById("contenedor");
    const sinTickets = document.getElementById("sinTickets");

    // Variable para almacenar el estado anterior
    let estadoAnterior = new Map();

    // Función para obtener los tickets desde la API
    async function obtenerTickets() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/tickets/publico`);
            
            if (!response.ok) {
                throw new Error(`Error al obtener tickets: ${response.status}`);
            }

            const data = await response.json();
            console.log("Tickets públicos obtenidos:", data);
            return data;
        } catch (error) {
            console.error("Error al cargar tickets públicos:", error);
            return [];
        }
    }

    // Función para determinar el texto de ventanilla según el estado
    function obtenerTextoVentanilla(ticket) {
        const estado = ticket.estado_id || ticket.ID_Estados || ticket.estado;
        const idVentanilla = ticket.id_ventanilla || ticket.ID_Ventanilla;
        const ventanillaNombre = ticket.ventanilla || ticket.Ventanilla;

        // Si el ticket está completado (estado 4), no debería mostrarse
        if (estado === 4 || estado === 'Completado') {
            return null;
        }
        
        // Si el ticket está siendo atendido (estado 3), mostrar número de ventanilla
        if (estado === 3 || estado === 'Atendiendo') {
            if (ventanillaNombre) {
                return ventanillaNombre;
            } else if (idVentanilla) {
                return `Ventanilla ${idVentanilla}`;
            }
            return "En atención";
        }
        
        // Si el ticket está pendiente (estado 1), mostrar "Por asignar"
        if (estado === 1 || estado === 'Pendiente') {
            return "Por asignar";
        }
        
        // Para cualquier otro caso (incluyendo cancelados)
        if (estado === 2 || estado === 'Cancelado') {
            return null;
        }
        
        return "Por asignar";
    }

    // Función para crear el HTML de una fila
    function crearFilaHTML(ticket, index) {
        const textoVentanilla = obtenerTextoVentanilla(ticket);
        if (textoVentanilla === null) return null;

        const estado = ticket.estado_id || ticket.ID_Estados || ticket.estado;
        const colorFolio = (estado === 3 || estado === 'Atendiendo') ? "text-blue-600" : "text-emerald-700";
        const bgColor = index % 2 === 0 ? "bg-slate-50" : "bg-white";

        return `
            <tr class="${bgColor} border-b border-slate-200 hover:bg-slate-100 transition-colors" data-folio="${ticket.folio}">
                <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 ${colorFolio} font-bold text-xl sm:text-2xl">${ticket.folio}</td>
                <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">${ticket.sector}</td>
                <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">
                    ${textoVentanilla}
                </td>
            </tr>
        `;
    }

    // Función para generar un hash único del estado de un ticket
    function generarHashTicket(ticket) {
        const estado = ticket.estado_id || ticket.ID_Estados || ticket.estado;
        const ventanilla = ticket.ventanilla || ticket.Ventanilla || '';
        return `${ticket.folio}-${estado}-${ventanilla}`;
    }

    // Función para actualizar solo los elementos que cambiaron
    async function cargarTicketsInteligente() {
        try {
            const ticketsData = await obtenerTickets();
            
            if (!ticketsData || ticketsData.length === 0) {
                // No hay tickets
                sinTickets.classList.remove("hidden");
                tickets.classList.add("hidden");
                estadoAnterior.clear();
                return;
            }

            // Filtrar tickets válidos para mostrar
            const ticketsValidos = ticketsData.filter(ticket => 
                obtenerTextoVentanilla(ticket) !== null
            );

            if (ticketsValidos.length === 0) {
                sinTickets.classList.remove("hidden");
                tickets.classList.add("hidden");
                estadoAnterior.clear();
                return;
            }

            // Mostrar tabla
            sinTickets.classList.add("hidden");
            tickets.classList.remove("hidden");

            // Generar nuevo estado
            const nuevoEstado = new Map();
            ticketsValidos.forEach((ticket, index) => {
                nuevoEstado.set(ticket.folio, {
                    html: crearFilaHTML(ticket, index),
                    hash: generarHashTicket(ticket)
                });
            });

            // Si es la primera carga o hay cambios significativos, reconstruir toda la tabla
            if (estadoAnterior.size === 0 || 
                ticketsValidos.length !== estadoAnterior.size ||
                Array.from(nuevoEstado.keys()).some(folio => !estadoAnterior.has(folio))) {
                
                // Reconstruir tabla completa
                let htmlCompleto = '';
                ticketsValidos.forEach((ticket, index) => {
                    const filaHTML = crearFilaHTML(ticket, index);
                    if (filaHTML) {
                        htmlCompleto += filaHTML;
                    }
                });
                contenedor.innerHTML = htmlCompleto;
                
            } else {
                // Actualización incremental - solo modificar lo que cambió
                nuevoEstado.forEach((nuevo, folio) => {
                    const anterior = estadoAnterior.get(folio);
                    
                    if (!anterior || anterior.hash !== nuevo.hash) {
                        // Encontrar la fila existente y actualizarla
                        const filaExistente = contenedor.querySelector(`[data-folio="${folio}"]`);
                        if (filaExistente) {
                            // Reemplazar solo si cambió
                            filaExistente.outerHTML = nuevo.html;
                        } else {
                            // Agregar nueva fila
                            contenedor.innerHTML += nuevo.html;
                        }
                    }
                });

                // Eliminar tickets que ya no existen
                estadoAnterior.forEach((_, folio) => {
                    if (!nuevoEstado.has(folio)) {
                        const filaEliminar = contenedor.querySelector(`[data-folio="${folio}"]`);
                        if (filaEliminar) {
                            filaEliminar.remove();
                        }
                    }
                });
            }

            // Actualizar estado anterior
            estadoAnterior = nuevoEstado;

        } catch (error) {
            console.error("Error al cargar tickets:", error);
            // En caso de error, mostrar estado de no hay tickets
            sinTickets.classList.remove("hidden");
            tickets.classList.add("hidden");
        }
    }

    // Cargar los tickets al iniciar la página
    cargarTicketsInteligente();

    // Actualizar automáticamente cada 3 segundos con transición suave
    setInterval(() => {
        cargarTicketsInteligente();
    }, 1000);

    // Exponer la función si deseas recargar externamente
    window.cargarTickets = cargarTicketsInteligente;
});