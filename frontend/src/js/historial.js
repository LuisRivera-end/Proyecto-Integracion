import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

// Variables para controlar el refresh
let refreshInterval;
let estadoAnteriorHistorial = new Map();

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
        const datos = data[0].cantidad;
        console.log("Tickets obtenidos:", datos);

        return datos;
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

// Función para mostrar el historial con actualización inteligente
async function mostrarHistorialInteligente(filtroEstado = "todos", filtroSector = "todos", fechaInicio = null, fechaFin = null) {
    const cuerpo = document.getElementById("tabla-historial");

    try {
        // Cargar datos actualizados
        let historial = await cargarHistorialReal();
        
        // Aplicar filtros
        let filtrado = historial.filter(ticket => {
            const estadoCoincide = filtroEstado === "todos" || 
                                ticket.estado.toLowerCase() === filtroEstado.toLowerCase();
            
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
            
            return estadoCoincide && sectorCoincide && fechaCoincide;
        });

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

        // Si es la primera carga o hay cambios significativos, reconstruir toda la tabla
        if (estadoAnteriorHistorial.size === 0 || 
            filtrado.length !== estadoAnteriorHistorial.size ||
            Array.from(nuevoEstado.keys()).some(folio => !estadoAnteriorHistorial.has(folio))) {
            
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
            
        } else {
            // Actualización incremental - solo modificar lo que cambió
            nuevoEstado.forEach((nuevo, folio) => {
                const anterior = estadoAnteriorHistorial.get(folio);
                
                if (!anterior || anterior.hash !== nuevo.hash) {
                    // Encontrar la fila existente y actualizarla
                    const filaExistente = cuerpo.querySelector(`[data-folio="${folio}"]`);
                    if (filaExistente) {
                        filaExistente.outerHTML = nuevo.html;
                    } else {
                        // Agregar nueva fila
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
    switch(estado.toLowerCase()) {
        case 'cancelado':
            return 'text-red-600 font-semibold';
        case 'completado':
            return 'text-green-600 font-semibold';
        case 'atendiendo':
            return 'text-blue-600 font-semibold';
        case 'pendiente':
            return 'text-yellow-600 font-semibold';
        default:
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
    
    if (fechaInicioInput.value) {
        fechaInicio = new Date(fechaInicioInput.value);
        fechaInicio.setHours(0, 0, 0, 0);
    }
    
    if (fechaFinInput.value) {
        fechaFin = new Date(fechaFinInput.value);
        fechaFin.setHours(23, 59, 59, 999);
    }
    
    if (fechaInicio && fechaFin && fechaInicio > fechaFin) {
        alert("La fecha de inicio no puede ser mayor que la fecha de fin");
        fechaFinInput.value = "";
        fechaFin = null;
    }
    
    mostrarHistorialInteligente(filtroEstado, filtroSector, fechaInicio, fechaFin);
}

// Actualizar estadísticas - Versión robusta
function actualizarResumen(lista) {
    const elementos = {
        "total-agregados": lista.length,
        "total-completados": lista.filter(t => t.estado === "completado").length,
        "total-cancelados": lista.filter(t => t.estado === "cancelado").length,
        "total-atendiendo": lista.filter(t => t.estado === "atendiendo").length,
        "total-pendientes": lista.filter(t => t.estado === "pendiente").length
    };

    // Actualizar elementos numéricos
    Object.entries(elementos).forEach(([id, valor]) => {
        const elemento = document.getElementById(id);
        if (elemento) {
            elemento.textContent = valor;
        }
    });

    // Actualizar sectores
    const conteoSectores = {};
    lista.forEach(t => {
        conteoSectores[t.sector] = (conteoSectores[t.sector] || 0) + 1;
    });

    const sectoresOrdenados = Object.entries(conteoSectores).sort((a,b) => b[1]-a[1]);
    const mas = sectoresOrdenados[0]?.[0] || "-";
    const menos = sectoresOrdenados[sectoresOrdenados.length - 1]?.[0] || "-";

    const sectorMas = document.getElementById("sector-mas");
    const sectorMenos = document.getElementById("sector-menos");
    
    if (sectorMas) sectorMas.textContent = mas;
    if (sectorMenos) sectorMenos.textContent = menos;
}

// Iniciar sistema de refresh automático
function iniciarRefreshAutomatico() {
    // Actualizar cada 5 segundos (puedes ajustar este tiempo)
    refreshInterval = setInterval(() => {
        console.log("🔄 Actualizando automáticamente historial...");
        aplicarFiltros(); // Esto aplicará los filtros actuales y actualizará la tabla
    }, 5000);
}

// Detener el refresh automático
function detenerRefreshAutomatico() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Window onload
window.onload = async function() {
    mostrarFecha();
    
    // Establecer fechas por defecto (últimos 7 días)
    const hoy = new Date();
    const hace7Dias = new Date();
    hace7Dias.setDate(hoy.getDate() - 7);
    
    document.getElementById("filtro-fecha-inicio").value = hace7Dias.toISOString().split('T')[0];
    document.getElementById("filtro-fecha-fin").value = hoy.toISOString().split('T')[0];
    
    if (dentroHorario()) {
        await actualizarDatos();
        setInterval(actualizarDatos, 30000);
    } else {
        document.getElementById('total-tickets').textContent = "-";
    }
    
    // Cargar historial inicial
    await mostrarHistorialInteligente();
    
    // Iniciar refresh automático
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
window.actualizarDatos=actualizarDatos;