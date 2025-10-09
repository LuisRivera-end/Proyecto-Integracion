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
};