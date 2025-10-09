// Función para mostrar la fecha actual
function mostrarFecha() {
    const fecha = new Date();
    const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('fecha-actual').textContent = fecha.toLocaleDateString('es-ES', opciones);
}

// se va aquitar solamente lo estoy simulando pura simulacion
function generarDatosSimulados() {
    const total = Math.floor(Math.random() * 150) + 50;
    return {
        total: total,
        enEspera: Math.floor(Math.random() * 15),
        ultimoTicket: 'T' + String(total).padStart(3, '0')
    };
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
        elemento.textContent = Math.floor(valorActual);
    }, 16);
}

function actualizarDatos() {
    const datos = generarDatosSimulados();
    
    animarNumero(document.getElementById('total-tickets'), datos.total);
    animarNumero(document.getElementById('tickets-espera'), datos.enEspera);
    document.getElementById('ultimo-ticket').textContent = datos.ultimoTicket;
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


window.onload = function() {
    mostrarFecha();
    if (dentroHorario()) {
        actualizarDatos();
        setInterval(actualizarDatos, 30000);
    } else {
        document.getElementById('total-tickets').textContent = "-";
        document.getElementById('tickets-espera').textContent = "-";
        document.getElementById('ultimo-ticket').textContent = "-";
    }
};// Datos simulados para el historial
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
            <td class="py-3 px-4 capitalize ${ticket.estado === 'cancelado' ? 'text-red-600' : ticket.estado === 'atendido' ? 'text-green-600' : 'text-yellow-600'}">${ticket.estado}</td>
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
    const atendidos = lista.filter(t => t.estado === "atendido").length;
    const cancelados = lista.filter(t => t.estado === "cancelado").length;
    const agregados = total;
    
    const conteoSectores = {};
    lista.forEach(t => {
        conteoSectores[t.sector] = (conteoSectores[t.sector] || 0) + 1;
    });

    const sectoresOrdenados = Object.entries(conteoSectores).sort((a,b) => b[1]-a[1]);
    const mas = sectoresOrdenados[0]?.[0] || "-";

    document.getElementById("total-agregados").textContent = agregados;
    document.getElementById("total-atendidos").textContent = atendidos;
    document.getElementById("total-cancelados").textContent = cancelados;
    document.getElementById("sector-mas").textContent = mas;
}

// Filtros
document.getElementById("filtro-status").addEventListener("change", e => {
    mostrarHistorial(e.target.value, document.getElementById("filtro-sector").value);
});

document.getElementById("filtro-sector").addEventListener("change", e => {
    mostrarHistorial(document.getElementById("filtro-status").value, e.target.value);
});

// Inicializar historial al cargar la página
window.addEventListener("DOMContentLoaded", () => {
    generarHistorialSimulado();
    mostrarHistorial();
});
