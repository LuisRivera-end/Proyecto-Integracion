import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

// ── Detect if logged-in user is a Subjefe (Jefe de Departamento) ──
const _currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
const _esSubjefe = _currentUser && _currentUser.rol === 6;
const _sectorSubjefe = _esSubjefe ? _currentUser.sector : null;

// Variables para controlar el estado
let estadoAnteriorHistorial = new Map();
let primeraCargaCompletada = false;

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
        console.log("Respuesta de total_tickets:", data);

        // If subjefe, we can't rely on this endpoint (it counts all sectors).
        // We'll calculate the count from the historial data instead.
        if (_esSubjefe) return null; // Signal to use historial-based count

        let cantidad = 0;

        if (Array.isArray(data) && data.length > 0) {
            cantidad = data[0].cantidad || 0;
        } else if (typeof data === 'object' && data.cantidad !== undefined) {
            cantidad = data.cantidad;
        } else if (typeof data === 'number') {
            cantidad = data;
        }

        console.log("Tickets obtenidos:", cantidad);
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

        if (_esSubjefe) {
            // For subjefe, count today's tickets from historial filtered by sector
            const historial = await cargarHistorialReal();
            const tz = 'America/Mexico_City';
            const hoy = new Date().toLocaleDateString('en-CA', { timeZone: tz }); // YYYY-MM-DD
            const ticketsHoy = historial.filter(t => {
                const fecha = parseFechaLocal(t.creado);
                if (!fecha) return false;
                const y = fecha.getUTCFullYear();
                const m = String(fecha.getUTCMonth() + 1).padStart(2, '0');
                const d = String(fecha.getUTCDate()).padStart(2, '0');
                return `${y}-${m}-${d}` === hoy;
            });
            animarNumero(total, ticketsHoy.length);
        } else {
            animarNumero(total, datos);
        }
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
        let historial = await response.json();

        // ── Subjefe: filter to their sector only ──
        if (_esSubjefe && _sectorSubjefe) {
            historial = historial.filter(t => t.sector === _sectorSubjefe);
        }

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

        if (_esSubjefe && _sectorSubjefe) {
            // Subjefe: lock sector filter to their own sector
            sectorSelect.innerHTML = `<option value="${_sectorSubjefe}" selected>${_sectorSubjefe}</option>`;
            sectorSelect.disabled = true;
            // Also hide the sector filter label/container since it's irrelevant
            const sectorContainer = sectorSelect.closest('.flex.flex-col');
            if (sectorContainer) sectorContainer.style.display = 'none';
        } else {
            sectorSelect.innerHTML = '<option value="todos">Todos</option>';
            sectores.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s.Sector;
                opt.textContent = s.Sector;
                sectorSelect.appendChild(opt);
            });
        }
    } catch (err) {
        console.error("Error al cargar sectores para filtro:", err);
    }
}

// Configuración de Socket.IO

if (typeof io !== 'undefined') {
    const socket = io(API_BASE_URL);
    socket.on('connect', () => {
        console.log('Historial conectado al WebSocket');

        // Registrar al empleado para mantener viva la sesion
        if (_currentUser && _currentUser.id && !_esSubjefe && _currentUser.rol !== 1) {
            socket.emit('ventanilla_register', { id_empleado: _currentUser.id });
        }
    });

    socket.on('tickets_updated', () => {
        console.log('Cambio detectado: actualizando historial y contadores');
        actualizarDatosCabecera();
        aplicarFiltros(); // Esto refresca la tabla con los filtros actuales
    });
} else {
    console.error('No se pudo conectar al WebSocket');
}

window.onload = async function () {
    mostrarFecha();
    actualizarDatosCabecera();
    // Cargar sectores dinámicamente
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

// ─── Reporte PDF con Modal ───

const modalReporte = document.getElementById("modal-reporte");
const modalBackdrop = document.getElementById("modal-reporte-backdrop");
const modalClose = document.getElementById("modal-reporte-close");
const btnCancelar = document.getElementById("btn-cancelar-reporte");
const btnGenerar = document.getElementById("btn-generar-reporte");
const inputDesde = document.getElementById("reporte-desde");
const inputHasta = document.getElementById("reporte-hasta");
const errorDiv = document.getElementById("modal-reporte-error");
const semestreInfo = document.getElementById("modal-semestre-info");

let semestreActual = null;

function abrirModal() {
    modalReporte.classList.remove("hidden");
    modalReporte.classList.add("flex");
    cargarInfoSemestre();
}

function cerrarModal() {
    modalReporte.classList.add("hidden");
    modalReporte.classList.remove("flex");
    errorDiv.classList.add("hidden");
    // Limpiar presets activos
    document.querySelectorAll(".preset-btn").forEach(b => {
        b.classList.remove("border-blue-500", "text-blue-600", "bg-blue-50");
        b.classList.add("border-slate-200", "text-slate-600");
    });
}

async function cargarInfoSemestre() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/reporte/semestre-actual`);
        if (res.ok) {
            semestreActual = await res.json();
            inputDesde.min = semestreActual.inicio;
            inputDesde.max = semestreActual.fin;
            inputHasta.min = semestreActual.inicio;
            inputHasta.max = semestreActual.fin;
            semestreInfo.textContent = `Semestre actual: ${semestreActual.label} (${formatDateLabel(semestreActual.inicio)} - ${formatDateLabel(semestreActual.fin)})`;
        }
    } catch (e) {
        console.error("Error al cargar info del semestre:", e);
    }
}

function formatDateLabel(dateStr) {
    const [y, m, d] = dateStr.split('-');
    return `${d}/${m}/${y}`;
}

function toYMD(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function clampToSemestre(dateStr) {
    if (!semestreActual) return dateStr;
    if (dateStr < semestreActual.inicio) return semestreActual.inicio;
    if (dateStr > semestreActual.fin) return semestreActual.fin;
    return dateStr;
}

// Presets
document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const preset = btn.dataset.preset;
        const hoy = new Date();
        let desde, hasta;

        if (preset === "hoy") {
            desde = hasta = toYMD(hoy);
        } else if (preset === "semanal") {
            const hace7 = new Date(hoy);
            hace7.setDate(hoy.getDate() - 7);
            desde = toYMD(hace7);
            hasta = toYMD(hoy);
        } else if (preset === "mensual") {
            const hace30 = new Date(hoy);
            hace30.setDate(hoy.getDate() - 30);
            desde = toYMD(hace30);
            hasta = toYMD(hoy);
        }

        inputDesde.value = clampToSemestre(desde);
        inputHasta.value = clampToSemestre(hasta);

        // Estilo activo
        document.querySelectorAll(".preset-btn").forEach(b => {
            b.classList.remove("border-blue-500", "text-blue-600", "bg-blue-50");
            b.classList.add("border-slate-200", "text-slate-600");
        });
        btn.classList.add("border-blue-500", "text-blue-600", "bg-blue-50");
        btn.classList.remove("border-slate-200", "text-slate-600");

        errorDiv.classList.add("hidden");
    });
});

function mostrarError(msg) {
    errorDiv.textContent = msg;
    errorDiv.classList.remove("hidden");
}

async function generarReportePDF() {
    const desde = inputDesde.value;
    const hasta = inputHasta.value;

    if (!desde || !hasta) {
        mostrarError("Selecciona ambas fechas para generar el reporte.");
        return;
    }
    if (desde > hasta) {
        mostrarError("La fecha 'Desde' no puede ser posterior a 'Hasta'.");
        return;
    }

    const textoOriginal = btnGenerar.innerHTML;

    try {
        btnGenerar.disabled = true;
        btnGenerar.innerHTML = `
            <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            <span>Generando...</span>
        `;

        let fetchUrl = `${API_BASE_URL}/api/reporte/generar?desde=${desde}&hasta=${hasta}`;
        if (_esSubjefe && _sectorSubjefe) {
            fetchUrl += `&sector=${encodeURIComponent(_sectorSubjefe)}`;
        }

        const response = await fetch(fetchUrl);

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || "Error al generar reporte");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `reporte_${desde}_${hasta}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        cerrarModal();

    } catch (error) {
        console.error("Error al generar reporte PDF:", error);
        mostrarError(error.message);
    } finally {
        btnGenerar.disabled = false;
        btnGenerar.innerHTML = textoOriginal;
    }
}

// Event listeners del modal
document.getElementById("btn-reporte-pdf").addEventListener("click", abrirModal);
modalBackdrop.addEventListener("click", cerrarModal);
modalClose.addEventListener("click", cerrarModal);
btnCancelar.addEventListener("click", cerrarModal);
btnGenerar.addEventListener("click", generarReportePDF);
