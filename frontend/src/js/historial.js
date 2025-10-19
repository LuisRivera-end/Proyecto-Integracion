const API_BASE_URL = "https://localhost:4443";

// Función para mostrar la fecha actual
function mostrarFecha() {
    const fecha = new Date();
    const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('fecha-actual').textContent = fecha.toLocaleDateString('es-ES', opciones);
}

// Mostrar total - CORREGIDA
async function totalTickets() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/total_tickets`);
            
        if (!response.ok) {
            throw new Error(`Error al obtener tickets: ${response.status}`);
        }

        const data = await response.json();
        const datos = data[0].cantidad;
        console.log("Tickets obtenidos:", datos); // Debug

        return datos;
    } catch (error) {
        console.error("Error al cargar tickets:", error);
        return 0; // Devuelve 0 si hay error
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

// Función actualizarDatos - CORREGIDA (ahora es async)
async function actualizarDatos() {
    try {
        const datos = await totalTickets(); // Esperar a que se resuelva la Promise
        const total = document.getElementById('total-tickets');
        
        // Usar animación o asignación directa
        animarNumero(total, datos);
        // O si prefieres sin animación:
        // total.textContent = datos;
        
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

// Datos simulados para el historial
const sectores = ["Cajas", "Becas", "Servicios Escolares"];
const estados = ["atendiendo", "cancelado", "completado", "pendiente"];
let historial = [];

// Generar datos simulados
function generarHistorialSimulado(cantidad = 25) {
    const hoy = new Date();
    historial = [];

    for (let i = 0; i < cantidad; i++) {
        const sector = sectores[Math.floor(Math.random() * sectores.length)];
        const estado = estados[Math.floor(Math.random() * estados.length)];
        
        // Crear fechas aleatorias en los últimos 30 días
        const diasAtras = Math.floor(Math.random() * 30);
        const creado = new Date(hoy);
        creado.setDate(creado.getDate() - diasAtras);
        creado.setHours(Math.floor(Math.random() * 24), Math.floor(Math.random() * 60), 0, 0);
        
        const finalizado = estado !== "pendiente" 
            ? new Date(creado.getTime() + Math.random() * 4 * 60 * 60 * 1000)
            : null;

        historial.push({
            id: "T" + String(100 + i),
            sector,
            estado,
            creado,
            finalizado
        });
    }
}

// Función para mostrar el historial con todos los filtros
function mostrarHistorial(filtroEstado = "todos", filtroSector = "todos", fechaInicio = null, fechaFin = null) {
    const cuerpo = document.getElementById("tabla-historial");
    cuerpo.innerHTML = "";

    let filtrado = historial.filter(ticket => {
        const estadoCoincide = filtroEstado === "todos" || ticket.estado === filtroEstado;
        const sectorCoincide = filtroSector === "todos" || ticket.sector.toLowerCase() === filtroSector;
        
        // Filtro por fecha
        let fechaCoincide = true;
        if (fechaInicio && fechaFin) {
            const fechaTicket = new Date(ticket.creado);
            fechaCoincide = fechaTicket >= fechaInicio && fechaTicket <= fechaFin;
        }
        
        return estadoCoincide && sectorCoincide && fechaCoincide;
    });

    // Ordenar por fecha de creación (más reciente primero)
    filtrado.sort((a, b) => new Date(b.creado) - new Date(a.creado));

    filtrado.forEach(ticket => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td class="py-3 px-4">${ticket.id}</td>
            <td class="py-3 px-4">${ticket.sector}</td>
            <td class="py-3 px-4 capitalize ${ticket.estado === 'cancelado' ? 'text-red-600' : ticket.estado === 'completado' ? 'text-green-600' : 'text-yellow-600'}">${ticket.estado}</td>
            <td class="py-3 px-4">${ticket.creado.toLocaleString()}</td>
            <td class="py-3 px-4">${ticket.finalizado ? ticket.finalizado.toLocaleString() : "-"}</td>
        `;
        cuerpo.appendChild(tr);
    });

    actualizarResumen(filtrado);
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
        fechaInicio.setHours(0, 0, 0, 0); // Inicio del día
    }
    
    if (fechaFinInput.value) {
        fechaFin = new Date(fechaFinInput.value);
        fechaFin.setHours(23, 59, 59, 999); // Fin del día
    }
    
    // Validar que la fecha de inicio no sea mayor que la de fin
    if (fechaInicio && fechaFin && fechaInicio > fechaFin) {
        alert("La fecha de inicio no puede ser mayor que la fecha de fin");
        fechaFinInput.value = "";
        fechaFin = null;
    }
    
    mostrarHistorial(filtroEstado, filtroSector, fechaInicio, fechaFin);
}

// Actualizar estadísticas
function actualizarResumen(lista) {
    const total = lista.length;
    const completados = lista.filter(t => t.estado === "completado").length;
    const cancelados = lista.filter(t => t.estado === "cancelado").length;
    const agregados = total;
    const pendientes = total - completados - cancelados;
    
    const conteoSectores = {};
    lista.forEach(t => {
        conteoSectores[t.sector] = (conteoSectores[t.sector] || 0) + 1;
    });

    const sectoresOrdenados = Object.entries(conteoSectores).sort((a,b) => b[1]-a[1]);
    const mas = sectoresOrdenados[0]?.[0] || "-";
    const menos = sectoresOrdenados[sectoresOrdenados.length - 1]?.[0] || "-";

    document.getElementById("total-agregados").textContent = agregados;
    document.getElementById("total-completados").textContent = completados;
    document.getElementById("total-cancelados").textContent = cancelados;
    document.getElementById("sector-mas").textContent = mas;
    document.getElementById("sector-menos").textContent = menos;
    document.getElementById("total-pendientes").textContent = pendientes;
}

// Window onload - CORREGIDO (ahora es async)
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
        // Eliminadas las referencias a elementos que no existen
    }
    
    generarHistorialSimulado();
    aplicarFiltros(); // Aplicar filtros iniciales
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