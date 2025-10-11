const API_BASE_URL = window.location.hostname === "localhost"
    ? "http://localhost:5000"
    : "http://backend:5000";

async function actualizarConteos() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/tickets_count`);
        if (!response.ok) throw new Error("Error al obtener los datos");
        const data = await response.json();

        // Actualizar los números en las tarjetas
        document.getElementById("count-servicios").textContent = data["Servicios Escolares"] || 0;
        document.getElementById("count-becas").textContent = data["Becas"] || 0;
        document.getElementById("count-cajas").textContent = data["Cajas"] || 0;
    } catch (err) {
        console.error("Error al actualizar conteos:", err);
    }
}

// Llamar al cargar
actualizarConteos();

// Actualizar cada 5 segundos
setInterval(actualizarConteos, 5000);
