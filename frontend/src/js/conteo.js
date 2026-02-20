import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

async function actualizarConteos() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/tickets_count`);
        if (!response.ok) throw new Error("Error al obtener los datos");
        const data = await response.json();

        // Actualizar los números en las tarjetas
        // Usamos una pequeña transición para que se note el cambio (opcional)
        actualizarElemento("count-servicios", data["Servicios Escolares"]);
        actualizarElemento("count-becas", data["Becas"]);
        actualizarElemento("count-cajas", data["Cajas"]);
        actualizarElemento("count-tesoreria", data["Tesoreria"]);

    } catch (err) {
        console.error("Error al actualizar conteos:", err);
    }
}

// Función auxiliar para manejar valores nulos y dar feedback visual
function actualizarElemento(id, valor) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = valor || 0;
    }
}

// 1. Carga inicial al abrir la página
document.addEventListener("DOMContentLoaded", () => {
    actualizarConteos();

    // 2. Configurar Socket.IO para el conteo
    // Si este JS vive en la misma página que el anterior, 
    // podrías reutilizar la variable 'socket'. 
    // Si es un archivo separado o página aparte, creamos la conexión:
    const socket = io(API_BASE_URL);

    socket.on('connect', () => {
        console.log('🔗 Conteos conectados al WebSocket');
    });

    // Escuchamos el mismo evento que los tickets públicos
    socket.on('tickets_updated', () => {
        console.log('📊 Actualizando conteos por cambio en tickets...');
        actualizarConteos();
    });

    socket.on('disconnect', () => {
        console.log('⚠️ WebSocket de conteos desconectado');
    });
});