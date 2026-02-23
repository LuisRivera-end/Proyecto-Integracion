import Config from './config.js';

document.addEventListener("DOMContentLoaded", function () {
    const API_BASE_URL = Config.API_BASE_URL;

    // Referencias a elementos del DOM
    const tickets = document.getElementById("tickets");
    const contenedor = document.getElementById("contenedor");
    const sinTickets = document.getElementById("sinTickets");

    // Variable para almacenar el estado anterior
    let estadoAnterior = new Map();
    let audioHabilitado = false;
    let audioContext = null;

    // Botón para habilitar audio (recomendado en pantallas)
    const activarAudioBtn = document.getElementById("activarAudio");
    if (activarAudioBtn) {
        activarAudioBtn.addEventListener("click", () => {
            audioHabilitado = true;

            // Crear y desbloquear AudioContext con gesto del usuario (requerido por iOS Safari)
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            audioContext = new AudioCtx();

            // En iOS Safari, el contexto inicia en "suspended" hasta un gesto del usuario
            if (audioContext.state === "suspended") {
                audioContext.resume();
            }

            // Reproducir un buffer silencioso para desbloquear completamente en iOS
            const silentBuffer = audioContext.createBuffer(1, 1, 22050);
            const source = audioContext.createBufferSource();
            source.buffer = silentBuffer;
            source.connect(audioContext.destination);
            source.start(0);

            activarAudioBtn.textContent = "🔊 Audio activado";
            activarAudioBtn.disabled = true;
            activarAudioBtn.classList.add("opacity-60", "cursor-not-allowed");
        });
    }

    async function reproducirAudio(url) {
        if (!audioHabilitado || !audioContext) return;

        try {
            // Asegurar que el contexto esté activo
            if (audioContext.state === "suspended") {
                await audioContext.resume();
            }

            // Descargar el audio como ArrayBuffer y decodificarlo
            const response = await fetch(url);
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

            // Crear un nodo fuente y reproducir
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.start(0);
        } catch (err) {
            console.error("🔇 Error al reproducir audio:", err);
        }
    }

    async function llamarTicket(folio, ventanilla) {
        try {
            const res = await fetch(`${API_BASE_URL}/api/turno/llamar`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ folio, ventanilla })
            });

            if (!res.ok) {
                throw new Error(`Error backend: ${res.status}`);
            }

            const data = await res.json();

            if (data.audio_url) {
                // Si la URL es relativa, construir la URL absoluta con la IP correcta
                const audioUrl = data.audio_url.startsWith('http')
                    ? data.audio_url
                    : `${API_BASE_URL}${data.audio_url}`;
                reproducirAudio(audioUrl);
            } else if (data.texto) {
                // fallback si usas Web Speech API
                hablar(data.texto);
            }

        } catch (error) {
            console.error("❌ Error al llamar ticket:", error);
        }
    }



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

    // Función para crear el HTML de una fila (Tailwind)
    function crearFilaHTML(ticket, index) {
        const textoVentanilla = obtenerTextoVentanilla(ticket);
        if (textoVentanilla === null) return null;

        const estado = ticket.estado_id || ticket.ID_Estados || ticket.estado;
        const esAtendiendo = (estado === 3 || estado === 'Atendiendo');

        // Chip de color por sector
        const sector = (ticket.sector || '').toLowerCase();
        let chipClass = 'inline-block px-4 py-1.5 rounded-full text-base font-bold';
        if (sector.includes('caja')) chipClass += ' chip-cajas';
        else if (sector.includes('serv') || sector.includes('escolar')) chipClass += ' chip-servicios';
        else if (sector.includes('beca')) chipClass += ' chip-becas';
        else if (sector.includes('tesorer')) chipClass += ' chip-tesoreria';
        else chipClass += ' bg-slate-200 text-slate-700';

        const ventanillaDisplay = textoVentanilla.replace(/ventanilla\s*/i, '') || textoVentanilla;

        if (index === 0) {
            return `
                <div class="grid grid-cols-3 items-center px-8 py-5 bg-green-700 border-b-2 border-green-900" data-folio="${ticket.folio}">
                    <span class="text-4xl font-black text-white tracking-tight">${ticket.folio}</span>
                    <span><span class="${chipClass} text-sm px-3 py-1">${ticket.sector}</span></span>
                    <span class="text-4xl font-black text-white">${esAtendiendo ? ventanillaDisplay : '—'}</span>
                </div>
            `;
        }

        return `
            <div class="grid grid-cols-3 items-center px-8 py-4 border-b border-white/10 hover:bg-white/5 transition-colors" data-folio="${ticket.folio}">
                <span class="text-2xl font-extrabold text-white">${ticket.folio}</span>
                <span><span class="${chipClass}">${ticket.sector}</span></span>
                <span class="text-2xl font-extrabold text-white">${esAtendiendo ? ventanillaDisplay : '—'}</span>
            </div>
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
                sinTickets.style.display = 'flex';
                contenedor.innerHTML = '';
                estadoAnterior.clear();
                return;
            }

            // Filtrar tickets válidos para mostrar
            const ticketsValidos = ticketsData.filter(ticket =>
                obtenerTextoVentanilla(ticket) !== null
            );

            if (ticketsValidos.length === 0) {
                sinTickets.style.display = 'flex';
                contenedor.innerHTML = '';
                estadoAnterior.clear();
                return;
            }

            // Mostrar tablero
            sinTickets.style.display = 'none';

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
                        const ticketActual = ticketsValidos.find(t => t.folio === folio);
                        const estadoActual = ticketActual.estado_id || ticketActual.ID_Estados || ticketActual.estado;
                        const estadoAnteriorTicket = anterior ? anterior.hash.split('-')[1] : null;

                        const estadoNormalizado = String(estadoActual);
                        const estadoAnteriorNormalizado = String(estadoAnteriorTicket);

                        if ((estadoNormalizado === '3' || estadoNormalizado === 'Atendiendo') &&
                            estadoAnteriorNormalizado !== estadoNormalizado) {
                            const pantalla = true;
                            if (pantalla) {
                                llamarTicket(ticketActual.folio, ticketActual.ventanilla);
                            }

                        }

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
            sinTickets.style.display = 'flex';
            contenedor.innerHTML = '';
        }
    }

    // Cargar los tickets al iniciar la página
    cargarTicketsInteligente();

    // Configurar Socket.IO para escuchar actualizaciones en tiempo real
    if (typeof io !== 'undefined') {
        const socket = io(API_BASE_URL);

        socket.on('connect', () => {
            console.log('Conectado al servidor de WebSockets');
        });

        socket.on('tickets_updated', () => {
            console.log('Actualización de tickets recibida por WebSocket');
            cargarTicketsInteligente();
        });

        socket.on('disconnect', () => {
            console.error('Desconectado del servidor de WebSockets');
        });
    } else {
        console.error('No se pudo conectar al WebSocket');
    }
    // Exponer la función si deseas recargar externamente
    window.cargarTickets = cargarTicketsInteligente;
});
document.addEventListener("DOMContentLoaded", async () => {
    const dropdownMenu = document.getElementById("dropdownMenu");
    const dropdownButton = document.getElementById("dropdownButton");

    try {
        const res = await fetch("/api/check_session");
        if (!res.ok) throw new Error("No autenticado");

        const data = await res.json();
        if (!data.logged_in) {
            // Oculta y deshabilita
            dropdownMenu.style.display = "none";
            dropdownButton.disabled = true;
            dropdownButton.style.pointerEvents = "none";
        }
    } catch (err) {
        // En caso de error, aplicamos la misma medida
        dropdownMenu.style.display = "none";
        dropdownButton.disabled = true;
        dropdownButton.style.pointerEvents = "none";
        console.log("Usuario no autenticado:", err);
    }
});