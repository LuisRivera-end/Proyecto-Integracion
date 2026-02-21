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
            creado: ticket.fecha_ticket,
            finalizado: ticket.fecha_ultimo_estado || null
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

async function mostrarHistorialInteligente(filtroEstado = "todos", filtroSector = "todos", fechaInicio = null, fechaFin = null, buscarFolio = "") {
    const cuerpo = document.getElementById("tabla-historial");

    try {
        let historial = await cargarHistorialReal();

        let filtrado = historial.filter(ticket => {
            const estadoCoincide = filtroEstado === "todos" || ticket.estado === filtroEstado;

            let sectorCoincide = true;
            if (filtroSector !== "todos") {
                sectorCoincide = ticket.sector === filtroSector;
            }

            // Filtro por folio (búsqueda parcial, case-insensitive)
            let folioCoincide = true;
            if (buscarFolio) {
                folioCoincide = ticket.folio.toLowerCase().includes(buscarFolio.toLowerCase());
            }

            let fechaCoincide = true;
            if (fechaInicio && fechaFin) {
                const fechaTicket = parseFechaLocal(ticket.creado);
                if (fechaTicket) {
                    // Usar UTC para obtener la fecha CDMX real almacenada
                    const y = fechaTicket.getUTCFullYear();
                    const m = String(fechaTicket.getUTCMonth() + 1).padStart(2, '0');
                    const d = String(fechaTicket.getUTCDate()).padStart(2, '0');
                    const cdmxDate = new Date(`${y}-${m}-${d}T00:00:00`);
                    fechaCoincide = cdmxDate >= fechaInicio && cdmxDate <= fechaFin;
                }
            }

            return estadoCoincide && sectorCoincide && fechaCoincide && folioCoincide;
        });

        filtrado.sort((a, b) => {
            const dateA = parseFechaLocal(a.creado);
            const dateB = parseFechaLocal(b.creado);
            return dateB - dateA;
        });

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

// Parsea una fecha del backend y la convierte a hora CDMX
// Flask serializa datetimes en formato RFC 2822 UTC: "Sat, 21 Feb 2026 21:51:59 GMT"
function parseFechaLocal(fechaStr) {
    if (!fechaStr) return null;
    // new Date() puede parsear RFC 2822 correctamente como UTC
    const fecha = new Date(fechaStr);
    if (isNaN(fecha)) return null;
    return fecha;
}

function formatearFecha(fechaStr) {
    const fecha = parseFechaLocal(fechaStr);
    if (!fecha) return '-';
    // Flask serializa las fechas CDMX como "GMT", así que usamos getUTC*
    // para obtener los valores originales almacenados (que ya son hora CDMX)
    const dd = String(fecha.getUTCDate()).padStart(2, '0');
    const mm = String(fecha.getUTCMonth() + 1).padStart(2, '0');
    const yyyy = fecha.getUTCFullYear();
    const hh = String(fecha.getUTCHours()).padStart(2, '0');
    const min = String(fecha.getUTCMinutes()).padStart(2, '0');
    return `${dd}/${mm}/${yyyy}, ${hh}:${min}`;
}

function aplicarFiltros() {
    const filtroEstado = document.getElementById("filtro-status").value;
    const filtroSector = document.getElementById("filtro-sector").value;
    const fInicio = document.getElementById("filtro-fecha-inicio").value;
    const fFin = document.getElementById("filtro-fecha-fin").value;
    const buscarFolio = document.getElementById("buscar-folio").value.trim();

    let fechaInicio = fInicio ? new Date(fInicio + "T00:00:00") : null;
    let fechaFin = fFin ? new Date(fFin + "T23:59:59") : null;

    mostrarHistorialInteligente(filtroEstado, filtroSector, fechaInicio, fechaFin, buscarFolio);
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

// Búsqueda instantánea al escribir
document.getElementById("buscar-folio").addEventListener("input", aplicarFiltros);

document.getElementById("btn-limpiar-fechas").addEventListener("click", () => {
    document.getElementById("filtro-status").value = "todos";
    document.getElementById("filtro-sector").value = "todos";
    document.getElementById("filtro-fecha-inicio").value = "";
    document.getElementById("filtro-fecha-fin").value = "";
    document.getElementById("buscar-folio").value = "";
    aplicarFiltros();
});


window.actualizarDatosCabecera = actualizarDatosCabecera;

// --- Reporte PDF ---
async function generarReportePDF() {
    const btn = document.getElementById("btn-reporte-pdf");
    const textoOriginal = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = `
            <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            <span>Generando...</span>
        `;
        
        const response = await fetch(`${API_BASE_URL}/api/reporte/semanal`);
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || "Error al generar reporte");
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `reporte_semanal.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error("Error al generar reporte PDF:", error);
        alert("Error al generar el reporte: " + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = textoOriginal;
    }
}

document.getElementById("btn-reporte-pdf").addEventListener("click", generarReportePDF);
