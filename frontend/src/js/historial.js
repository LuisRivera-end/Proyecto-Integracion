import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

// Variables para controlar el estado
let estadoAnteriorHistorial = new Map();
let primeraCargaCompletada = false;

// Configuración de Socket.IO
const socket = io(API_BASE_URL);

// Función para mostrar la fecha actual
function mostrarFecha() {
    const fecha = new Date();
    const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('fecha-actual').textContent = fecha.toLocaleDateString('es-ES', opciones);
}

// Mostrar total de tickets del día actual
async function totalTickets() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/total_tickets`);

        if (!response.ok) {
            throw new Error(`Error al obtener tickets: ${response.status}`);
        }

        const data = await response.json();
        console.log("📊 Respuesta de total_tickets:", data);

        let cantidad = 0;

        if (Array.isArray(data) && data.length > 0) {
            cantidad = data[0].cantidad || 0;
        } else if (typeof data === 'object' && data.cantidad !== undefined) {
            cantidad = data.cantidad;
        } else if (typeof data === 'number') {
            cantidad = data;
        }

        console.log("🎫 Tickets obtenidos:", cantidad);
        return cantidad;

    } catch (error) {
        console.error("Error al cargar tickets:", error);
        return 0;
    }
}

function animarNumero(elemento, valorFinal, duracion = 1000) {
    const valorInicial = 0;
    const incremento = valorFinal / (duracion / 16);
    let valorActual = valorInicial;

    const intervalo = setInterval(() => {
        valorActual += incremento;
        if (valorActual >= valorFinal) {
            valorActual = valorFinal;
            clearInterval(intervalo);
        }
        elemento.textContent = Math.round(valorActual);
    }, 16);
}



async function actualizarDatosCabecera() {
    try {
        const datos = await totalTickets();
        const total = document.getElementById('total-tickets');

        animarNumero(total, datos);
        console.log("Datos actualizados:", datos);
    } catch (error) {
        console.error("Error al actualizar datos:", error);
        document.getElementById('total-tickets').textContent = "Error";
    }
}

// Cargar historial real
async function cargarHistorialReal() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/tickets/historial`);
        if (!response.ok) throw new Error(`Error: ${response.status}`);
        const historial = await response.json();

        return historial.map(ticket => ({
            ...ticket,
            creado: new Date(ticket.fecha_ticket),
            finalizado: ticket.fecha_ultimo_estado ? new Date(ticket.fecha_ultimo_estado) : null
        }));
    } catch (error) {
        console.error("Error al cargar historial:", error);
        return [];
    }
}

function generarHashTicket(ticket) {
    return `${ticket.folio}-${ticket.estado}-${ticket.fecha_ultimo_estado || ''}`;
}

function crearFilaHistorialHTML(ticket) {
    return `
        <tr class="hover:bg-gray-50 transition-colors duration-150" data-folio="${ticket.folio}">
            <td class="py-3 px-4 border-b">${ticket.folio}</td>
            <td class="py-3 px-4 border-b">${ticket.sector}</td>
            <td class="py-3 px-4 border-b capitalize ${getEstadoColor(ticket.estado)}">${ticket.estado}</td>
            <td class="py-3 px-4 border-b">${formatearFecha(ticket.creado)}</td>
            <td class="py-3 px-4 border-b">${ticket.finalizado ? formatearFecha(ticket.finalizado) : "-"}</td>
        </tr>
    `;
}

async function mostrarHistorialInteligente(filtroEstado = "todos", filtroSector = "todos", fechaInicio = null, fechaFin = null) {
    const cuerpo = document.getElementById("tabla-historial");

    try {
        let historial = await cargarHistorialReal();

        let filtrado = historial.filter(ticket => {
            const estadoCoincide = filtroEstado === "todos" || ticket.estado === filtroEstado;

            let sectorCoincide = true;
            if (filtroSector !== "todos") {
                sectorCoincide = ticket.sector === filtroSector;
            }

            let fechaCoincide = true;
            if (fechaInicio && fechaFin) {
                const fechaTicket = new Date(ticket.creado);
                fechaCoincide = fechaTicket >= fechaInicio && fechaTicket <= fechaFin;
            }

            return estadoCoincide && sectorCoincide && fechaCoincide;
        });

        filtrado.sort((a, b) => b.creado - a.creado);

        const nuevoEstado = new Map();
        filtrado.forEach(ticket => {
            nuevoEstado.set(ticket.folio, {
                html: crearFilaHistorialHTML(ticket),
                hash: generarHashTicket(ticket)
            });
        });

        if (!primeraCargaCompletada || filtrado.length !== estadoAnteriorHistorial.size) {
            if (filtrado.length === 0) {
                cuerpo.innerHTML = `<tr><td colspan="5" class="py-4 px-4 text-center text-gray-500">No hay registros</td></tr>`;
            } else {
                cuerpo.innerHTML = filtrado.map(t => crearFilaHistorialHTML(t)).join('');
            }
            primeraCargaCompletada = true;
        } else {
            nuevoEstado.forEach((nuevo, folio) => {
                const anterior = estadoAnteriorHistorial.get(folio);
                if (!anterior || anterior.hash !== nuevo.hash) {
                    const fila = cuerpo.querySelector(`[data-folio="${folio}"]`);
                    if (fila) fila.outerHTML = nuevo.html;
                    else cuerpo.insertAdjacentHTML('afterbegin', nuevo.html);
                }
            });

            estadoAnteriorHistorial.forEach((_, folio) => {
                if (!nuevoEstado.has(folio)) {
                    const fila = cuerpo.querySelector(`[data-folio="${folio}"]`);
                    if (fila) fila.remove();
                }
            });
        }

        estadoAnteriorHistorial = nuevoEstado;
        actualizarResumen(filtrado);

    } catch (error) {
        console.error("Error en el render de historial:", error);
    }
}

function getEstadoColor(estado) {
    const colores = {
        'Completado': 'text-green-600 font-semibold',
        'Cancelado': 'text-red-600 font-semibold',
        'Atendiendo': 'text-blue-600 font-semibold',
        'Pendiente': 'text-yellow-600 font-semibold'
    };
    return colores[estado] || 'text-gray-600';
}

function formatearFecha(fecha) {
    return new Date(fecha).toLocaleString('es-ES', {
        year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
    });
}

function aplicarFiltros() {
    const filtroEstado = document.getElementById("filtro-status").value;
    const filtroSector = document.getElementById("filtro-sector").value;
    const fInicio = document.getElementById("filtro-fecha-inicio").value;
    const fFin = document.getElementById("filtro-fecha-fin").value;

    let fechaInicio = fInicio ? new Date(fInicio + "T00:00:00") : null;
    let fechaFin = fFin ? new Date(fFin + "T23:59:59") : null;

    mostrarHistorialInteligente(filtroEstado, filtroSector, fechaInicio, fechaFin);
}

function actualizarResumen(lista) {
    const conteo = { "Pendiente": 0, "Cancelado": 0, "Atendiendo": 0, "Completado": 0 };
    lista.forEach(t => { if (conteo.hasOwnProperty(t.estado)) conteo[t.estado]++; });

    document.getElementById("total-agregados").textContent = lista.length;
    document.getElementById("total-completados").textContent = conteo.Completado;
    document.getElementById("total-cancelados").textContent = conteo.Cancelado;
    document.getElementById("total-atendiendo").textContent = conteo.Atendiendo;
    document.getElementById("total-pendientes").textContent = conteo.Pendiente;
}

// Cargar sectores para el filtro
async function cargarSectoresFiltro() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/sectores`);
        const sectores = await res.json();
        const sectorSelect = document.getElementById("filtro-sector");
        sectorSelect.innerHTML = '<option value="todos">Todos</option>';

        sectores.forEach(s => {
            const opt = document.createElement("option");
            opt.value = s.Sector;
            opt.textContent = s.Sector;
            sectorSelect.appendChild(opt);
        });
    } catch (err) {
        console.error("Error al cargar sectores para filtro:", err);
    }
}

// LÓGICA DE WEBSOCKETS SUSTITUYENDO INTERVALOS
socket.on('connect', () => {
    console.log('🔗 Historial conectado al WebSocket');
});

socket.on('tickets_updated', () => {
    console.log('⚡ Cambio detectado: actualizando historial y contadores');
    actualizarDatosCabecera();
    aplicarFiltros(); // Esto refresca la tabla con los filtros actuales
});

window.onload = async function () {
    mostrarFecha();
    actualizarDatosCabecera();
    // ✅ Cargar sectores dinámicamente
    await cargarSectoresFiltro();
    await mostrarHistorialInteligente();
};

// Listeners
document.querySelectorAll("#filtro-status, #filtro-sector, #filtro-fecha-inicio, #filtro-fecha-fin").forEach(el => {
    el.addEventListener("change", aplicarFiltros);
});

document.getElementById("btn-limpiar-fechas").addEventListener("click", () => {
    document.getElementById("filtro-status").value = "todos";
    document.getElementById("filtro-sector").value = "todos";
    document.getElementById("filtro-fecha-inicio").value = "";
    document.getElementById("filtro-fecha-fin").value = "";
    aplicarFiltros();
});


window.actualizarDatosCabecera = actualizarDatosCabecera;
