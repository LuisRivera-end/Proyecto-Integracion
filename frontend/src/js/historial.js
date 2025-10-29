import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

// Variables para controlar el refresh
let refreshInterval;
let estadoAnteriorHistorial = new Map();
let primeraCargaCompletada = false; // ✅ Nueva variable para controlar

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

// Función actualizarDatos
async function actualizarDatos() {
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

function dentroHorario() {
    const fecha = new Date();
    const dia = fecha.getDay();
    const hora = fecha.getHours();

    if (dia === 0) return false;
    if (dia >= 1 && dia <= 5) return hora >= 8 && hora < 17;
    if (dia === 6) return hora >= 8 && hora < 14;
    return false;
}

// Cargar historial real desde la base de datos
async function cargarHistorialReal() {
    try {
        console.log("📡 Solicitando historial a:", `${API_BASE_URL}/api/tickets/historial`);
        const response = await fetch(`${API_BASE_URL}/api/tickets/historial`);
        
        if (!response.ok) {
            throw new Error(`Error al obtener historial: ${response.status}`);
        }

        const historial = await response.json();
        console.log("📊 Historial recibido:", historial.length, "tickets");
        
        // Formatear las fechas
        historial.forEach(ticket => {
            ticket.creado = new Date(ticket.fecha_ticket);
            if (ticket.fecha_ultimo_estado) {
                ticket.finalizado = new Date(ticket.fecha_ultimo_estado);
            }
        });
        
        return historial;
    } catch (error) {
        console.error("Error al cargar historial:", error);
        return [];
    }
}

// Función para generar un hash único del ticket para comparación
function generarHashTicket(ticket) {
    return `${ticket.folio}-${ticket.estado}-${ticket.fecha_ultimo_estado || ''}`;
}

// Función para crear el HTML de una fila del historial
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

// Función para mostrar el historial con actualización inteligente - CORREGIDA
async function mostrarHistorialInteligente(filtroEstado = "todos", filtroSector = "todos", fechaInicio = null, fechaFin = null) {
    const cuerpo = document.getElementById("tabla-historial");

    try {
        // Cargar datos actualizados primero
        let historial = await cargarHistorialReal();
        
        console.log("🔍 ESTADOS ENCONTRADOS EN EL HISTORIAL:");
        const estadosUnicos = [...new Set(historial.map(t => t.estado))];
        console.log(estadosUnicos);

        console.log("🔍 SECTORES ENCONTRADOS EN EL HISTORIAL:");
        const sectoresUnicos = [...new Set(historial.map(t => t.sector))];
        console.log(sectoresUnicos);

        // ✅ CORRECCIÓN: Debuggear los filtros aplicados
        console.log("🔍 FILTROS APLICADOS:", {
            filtroEstado,
            filtroSector, 
            fechaInicio,
            fechaFin
        });

        // Aplicar filtros
        let filtrado = historial.filter(ticket => {
            const estadoCoincide = filtroEstado === "todos" || 
                                ticket.estado === filtroEstado;
            
            let sectorCoincide = true;
            if (filtroSector !== "todos") {
                const mapeoSectores = {
                    'cajas': 'Cajas',
                    'becas': 'Becas', 
                    'servicios escolares': 'Servicios Escolares'
                };
                const sectorBd = mapeoSectores[filtroSector.toLowerCase()];
                sectorCoincide = ticket.sector === sectorBd;
            }
            
            let fechaCoincide = true;
            if (fechaInicio && fechaFin) {
                const fechaTicket = new Date(ticket.creado);
                fechaCoincide = fechaTicket >= fechaInicio && fechaTicket <= fechaFin;
            }
            
            const coincide = estadoCoincide && sectorCoincide && fechaCoincide;
            
            // ✅ DEBUG: Ver por qué un ticket no coincide
            if (!coincide) {
                console.log(`❌ Ticket ${ticket.folio} no coincide:`, {
                    estado: ticket.estado,
                    filtroEstado,
                    estadoCoincide,
                    sector: ticket.sector,
                    filtroSector,
                    sectorCoincide,
                    fechaTicket: ticket.creado,
                    fechaInicio,
                    fechaFin,
                    fechaCoincide
                });
            }
            
            return coincide;
        });

        console.log("🔍 RESULTADO FILTRADO:", filtrado.length, "tickets");

        // Ordenar por fecha de creación (más reciente primero)
        filtrado.sort((a, b) => new Date(b.creado) - new Date(a.creado));

        // Generar nuevo estado
        const nuevoEstado = new Map();
        filtrado.forEach(ticket => {
            nuevoEstado.set(ticket.folio, {
                html: crearFilaHistorialHTML(ticket),
                hash: generarHashTicket(ticket)
            });
        });

        // ✅ CORRECCIÓN: Siempre reconstruir en la primera carga
        if (!primeraCargaCompletada || estadoAnteriorHistorial.size === 0 || 
            filtrado.length !== estadoAnteriorHistorial.size) {
            
            // Reconstruir tabla completa
            if (filtrado.length === 0) {
                cuerpo.innerHTML = `
                    <tr>
                        <td colspan="5" class="py-4 px-4 text-center text-gray-500">
                            No se encontraron tickets que coincidan con los filtros
                        </td>
                    </tr>
                `;
            } else {
                let htmlCompleto = '';
                filtrado.forEach(ticket => {
                    htmlCompleto += crearFilaHistorialHTML(ticket);
                });
                cuerpo.innerHTML = htmlCompleto;
            }
            
            // ✅ Marcar primera carga como completada
            primeraCargaCompletada = true;
            
        } else {
            // Actualización incremental - solo modificar lo que cambió
            nuevoEstado.forEach((nuevo, folio) => {
                const anterior = estadoAnteriorHistorial.get(folio);
                
                if (!anterior || anterior.hash !== nuevo.hash) {
                    const filaExistente = cuerpo.querySelector(`[data-folio="${folio}"]`);
                    if (filaExistente) {
                        filaExistente.outerHTML = nuevo.html;
                    } else {
                        cuerpo.innerHTML += nuevo.html;
                    }
                }
            });

            // Eliminar tickets que ya no existen
            estadoAnteriorHistorial.forEach((_, folio) => {
                if (!nuevoEstado.has(folio)) {
                    const filaEliminar = cuerpo.querySelector(`[data-folio="${folio}"]`);
                    if (filaEliminar) {
                        filaEliminar.remove();
                    }
                }
            });
        }

        // Actualizar estado anterior
        estadoAnteriorHistorial = nuevoEstado;

        // Actualizar estadísticas
        actualizarResumen(filtrado);

    } catch (error) {
        console.error("Error al mostrar historial:", error);
        cuerpo.innerHTML = `
            <tr>
                <td colspan="5" class="py-4 px-4 text-center text-red-500">
                    Error al cargar el historial
                </td>
            </tr>
        `;
    }
}

// Función auxiliar para obtener color según estado
function getEstadoColor(estado) {
    switch(estado) {
        case 'Completado':
            return 'text-green-600 font-semibold';
        case 'Cancelado':
            return 'text-red-600 font-semibold';
        case 'Atendiendo':
            return 'text-blue-600 font-semibold';
        case 'Pendiente':
            return 'text-yellow-600 font-semibold';
        default:
            console.warn(`🎨 Estado no reconocido para color: "${estado}"`);
            return 'text-gray-600';
    }
}

// Función auxiliar para formatear fecha
function formatearFecha(fecha) {
    return new Date(fecha).toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Función para aplicar todos los filtros
function aplicarFiltros() {
    const filtroEstado = document.getElementById("filtro-status").value;
    const filtroSector = document.getElementById("filtro-sector").value;
    const fechaInicioInput = document.getElementById("filtro-fecha-inicio");
    const fechaFinInput = document.getElementById("filtro-fecha-fin");
    
    let fechaInicio = null;
    let fechaFin = null;
    
    // ✅ CORRECCIÓN: Solo aplicar fechas si tienen valor
    if (fechaInicioInput.value) {
    const partesInicio = fechaInicioInput.value.split("-");
    fechaInicio = new Date(
        partesInicio[0],
        partesInicio[1] - 1,
        partesInicio[2],
        0, 0, 0, 0
    );
}

if (fechaFinInput.value) {
    const partesFin = fechaFinInput.value.split("-");
    fechaFin = new Date(
        partesFin[0],
        partesFin[1] - 1,
        partesFin[2],
        23, 59, 59, 999
    );
}
    
    // ✅ CORRECCIÓN: Solo validar si ambas fechas tienen valor
    if (fechaInicio && fechaFin && fechaInicio > fechaFin) {
        alert("La fecha de inicio no puede ser mayor que la fecha de fin");
        fechaFinInput.value = "";
        fechaFin = null;
    }
    
    console.log("🎯 Aplicando filtros:", {
        filtroEstado,
        filtroSector,
        fechaInicio: fechaInicioInput.value,
        fechaFin: fechaFinInput.value
    });
    
    mostrarHistorialInteligente(filtroEstado, filtroSector, fechaInicio, fechaFin);
}

// Actualizar estadísticas - VERSIÓN DEFINITIVAMENTE CORREGIDA
function actualizarResumen(lista) {
    console.log("🔍 Datos recibidos para estadísticas:", lista);
    
    // Contar por estado - INICIALIZAR CORRECTAMENTE
    const conteoEstados = {
        "Pendiente": 0,
        "Cancelado": 0,
        "Atendiendo": 0,
        "Completado": 0
    };

    // Contar tickets por estado
    lista.forEach(ticket => {
        const estado = ticket.estado;
        console.log(`🔍 Ticket ${ticket.folio} - Estado: "${estado}"`);
        
        if (conteoEstados.hasOwnProperty(estado)) {
            conteoEstados[estado]++;
        } else {
            console.warn(`⚠️ Estado no reconocido: "${estado}" (${ticket.folio})`);
        }
    });

    // ✅ CORRECCIÓN DEFINITIVA: Usar valores directos del objeto
    const totalAgregados = lista.length;
    const totalCompletados = conteoEstados.Completado;
    const totalCancelados = conteoEstados.Cancelado;
    const totalAtendiendo = conteoEstados.Atendiendo;
    const totalPendientes = conteoEstados.Pendiente;

    console.log("🔍 Valores calculados:", {
        totalAgregados, totalCompletados, totalCancelados, totalAtendiendo, totalPendientes
    });

    // Actualizar DOM
    document.getElementById("total-agregados").textContent = totalAgregados;
    document.getElementById("total-completados").textContent = totalCompletados;
    document.getElementById("total-cancelados").textContent = totalCancelados;
    document.getElementById("total-atendiendo").textContent = totalAtendiendo;
    document.getElementById("total-pendientes").textContent = totalPendientes;

    console.log("📊 Estadísticas actualizadas:", {
        total: totalAgregados,
        completados: totalCompletados,
        cancelados: totalCancelados,
        atendiendo: totalAtendiendo,
        pendientes: totalPendientes
    });
}

// Iniciar sistema de refresh automático - CORREGIDO
function iniciarRefreshAutomatico() {
    // ✅ Esperar 2 segundos antes de iniciar el refresh automático
    setTimeout(() => {
        refreshInterval = setInterval(() => {
            console.log("🔄 Actualizando automáticamente historial...");
            aplicarFiltros();
        }, 3000); // 10 segundos
    }, 2000);
}

// Detener el refresh automático
function detenerRefreshAutomatico() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Window onload - CORREGIDO
window.onload = async function() {
    mostrarFecha();
    
    // ✅ CORRECCIÓN: NO establecer fechas por defecto inicialmente
    // Dejar los campos de fecha vacíos para mostrar todos los tickets
    
    if (dentroHorario()) {
        await actualizarDatos();
        setInterval(actualizarDatos, 30000);
    } else {
        document.getElementById('total-tickets').textContent = "-";
    }
    
    // ✅ Cargar historial inicial SIN filtros
    await mostrarHistorialInteligente();
    
    // ✅ Iniciar refresh automático después de que todo esté cargado
    iniciarRefreshAutomatico();
};

// Event listeners para los filtros
document.getElementById("filtro-status").addEventListener("change", aplicarFiltros);
document.getElementById("filtro-sector").addEventListener("change", aplicarFiltros);
document.getElementById("filtro-fecha-inicio").addEventListener("change", aplicarFiltros);
document.getElementById("filtro-fecha-fin").addEventListener("change", aplicarFiltros);

// Botón para limpiar fechas
document.getElementById("btn-limpiar-fechas").addEventListener("click", function() {
    document.getElementById("filtro-fecha-inicio").value = "";
    document.getElementById("filtro-fecha-fin").value = "";
    aplicarFiltros();
});

// Pausar refresh cuando la pestaña no está visible
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        detenerRefreshAutomatico();
    } else {
        iniciarRefreshAutomatico();
    }
});

window.actualizarDatos = actualizarDatos;