const API_BASE_URL = "https://localhost:4443";

// Función para mostrar la fecha actual
function mostrarFecha() {
    const fecha = new Date();
    const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('fecha-actual').textContent = fecha.toLocaleDateString('es-ES', opciones);
}
async function actualizarTicketsFueraHorario() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/ticket/cancelar_fuera_horario`, {
            method: "PUT"
        });
        const data = await response.json();

        if (response.ok) {
            console.log("Tickets fuera de horario actualizados:", data.mensaje);
        } else {
            console.warn("No se pudieron actualizar tickets fuera de horario:", data.error);
        }
    } catch (err) {
        console.error("Error al actualizar tickets fuera de horario:", err);
    }
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
// Función para mostrar el historial con todos los filtros
async function mostrarHistorial(filtroEstado = "todos", filtroSector = "todos", fechaInicio = null, fechaFin = null) {
    const cuerpo = document.getElementById("tabla-historial");
    cuerpo.innerHTML = "";

    try {
        // ✅ CORRECCIÓN: Cargar los datos primero
        let historial = await cargarHistorialReal();
        
        let filtrado = historial.filter(ticket => {
            // Corregir comparación de estados (ignorar mayúsculas/minúsculas)
            const estadoCoincide = filtroEstado === "todos" || 
                                ticket.estado.toLowerCase() === filtroEstado.toLowerCase();
            
            // Corregir comparación de sectores
            let sectorCoincide = true;
            if (filtroSector !== "todos") {
                // Mapear nombres de filtro a nombres de base de datos
                const mapeoSectores = {
                    'cajas': 'Cajas',
                    'becas': 'Becas', 
                    'servicios escolares': 'Servicios Escolares'
                };
                const sectorBd = mapeoSectores[filtroSector.toLowerCase()];
                sectorCoincide = ticket.sector === sectorBd;
            }
            
            // Filtro por fecha
            let fechaCoincide = true;
            if (fechaInicio && fechaFin) {
                const fechaTicket = new Date(ticket.creado);
                fechaCoincide = fechaTicket >= fechaInicio && fechaTicket <= fechaFin;
            }
            
            return estadoCoincide && sectorCoincide && fechaCoincide;
        });

        console.log("🔍 Filtros aplicados:", {
            filtroEstado,
            filtroSector,
            totalTickets: historial.length,
            ticketsFiltrados: filtrado.length
        });

        // Ordenar por fecha de creación (más reciente primero)
        filtrado.sort((a, b) => new Date(b.creado) - new Date(a.creado));

        if (filtrado.length === 0) {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td colspan="5" class="py-4 px-4 text-center text-gray-500">
                    No se encontraron tickets que coincidan con los filtros
                </td>
            `;
            cuerpo.appendChild(tr);
        } else {
            filtrado.forEach(ticket => {
                const tr = document.createElement("tr");
                tr.className = "hover:bg-gray-50 transition-colors duration-150";
                tr.innerHTML = `
                    <td class="py-3 px-4 border-b">${ticket.folio}</td>
                    <td class="py-3 px-4 border-b">${ticket.sector}</td>
                    <td class="py-3 px-4 border-b capitalize ${getEstadoColor(ticket.estado)}">${ticket.estado}</td>
                    <td class="py-3 px-4 border-b">${formatearFecha(ticket.creado)}</td>
                    <td class="py-3 px-4 border-b">${ticket.finalizado ? formatearFecha(ticket.finalizado) : "-"}</td>
                `;
                cuerpo.appendChild(tr);
            });
        }

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
    
    mostrarHistorial(filtroEstado, filtroSector, fechaInicio, fechaFin);
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

// Window onload
window.onload = async function() {
    mostrarFecha();

    // Primero, cancelar tickets fuera de horario
    await actualizarTicketsFueraHorario();

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

    await mostrarHistorial(); // Cargar historial real
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