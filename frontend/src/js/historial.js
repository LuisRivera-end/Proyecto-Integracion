const API_BASE_URL = window.location.hostname === "localhost" 
    ? "http://localhost:5000"
    : "http://backend:5000";

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

// Window onload - CORREGIDO (ahora es async)
window.onload = async function() {
    mostrarFecha();
    
    if (dentroHorario()) {
        await actualizarDatos(); // Esperar a que se carguen los datos iniciales
        setInterval(actualizarDatos, 30000); // Actualizar cada 30 segundos
    } else {
        document.getElementById('total-tickets').textContent = "-";
        document.getElementById('tickets-espera').textContent = "-";
        document.getElementById('ultimo-ticket').textContent = "-";
    }
    
    // Inicializar el historial simulado (parte existente de tu código)
    generarHistorialSimulado();
    mostrarHistorial();
};

// El resto de tu código para el historial simulado se mantiene igual...
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
        const creado = new Date(hoy.getTime() - Math.random() * 3 * 24 * 60 * 60 * 1000); // últimos 3 días
        const finalizado = estado !== "espera"
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

// Renderizar tabla
function mostrarHistorial(filtroEstado = "todos", filtroSector = "todos") {
    const cuerpo = document.getElementById("tabla-historial");
    cuerpo.innerHTML = "";

    let filtrado = historial.filter(ticket => {
        const estadoCoincide = filtroEstado === "todos" || ticket.estado === filtroEstado;
        const sectorCoincide = filtroSector === "todos" || ticket.sector.toLowerCase() === filtroSector;
        return estadoCoincide && sectorCoincide;
    });

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

// Filtros
document.getElementById("filtro-status").addEventListener("change", e => {
    mostrarHistorial(e.target.value, document.getElementById("filtro-sector").value);
});

document.getElementById("filtro-sector").addEventListener("change", e => {
    mostrarHistorial(document.getElementById("filtro-status").value, e.target.value);
});