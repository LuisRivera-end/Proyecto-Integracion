const API_BASE_URL = window.location.hostname === "localhost" 
    ? "http://localhost:5000"
    : "http://backend:5000"; 

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ticket-form");
    const formContainer = document.getElementById("form-container");
    const ticketResult = document.getElementById("ticket-result");
    const errorMessage = document.getElementById("error-message");
    const errorText = document.getElementById("error-text");

    const noMatriculaCheckbox = document.getElementById("no-matricula-checkbox");
    const matriculaFolioLabel = document.getElementById("matricula-folio-label");
    const inputMatriculaFolio = document.getElementById("input-matricula-folio");

    noMatriculaCheckbox.addEventListener("click", () => {
        if (noMatriculaCheckbox.checked) {
            matriculaFolioLabel.textContent = "Folio";
            inputMatriculaFolio.placeholder = "Ingresa tu folio";
        } else {
            matriculaFolioLabel.textContent = "Matrícula";
            inputMatriculaFolio.placeholder = "Ingresa tu matrícula";
        }
    });

    form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const MatriculaOFolioIngresado = inputMatriculaFolio.value.trim();
    const sector = document.getElementById("sector").value;

    if (!MatriculaOFolioIngresado || !sector) {
        showError("Por favor, completa todos los campos.");
        return;
    }

    try {   
        console.log("Iniciando proceso de generación de ticket...");
        
        // 1. Primero obtener el tiempo estimado
        let tiempoEstimado = 5; // Valor por defecto actualizado
        try {
            console.log("Consultando tiempo estimado para sector:", sector);
            const tiempoResponse = await fetch(`${API_BASE_URL}/api/tiempo_espera_promedio/${encodeURIComponent(sector)}`);
            
            if (tiempoResponse.ok) {
                const tiempoData = await tiempoResponse.json();
                tiempoEstimado = tiempoData.tiempo_estimado;
                console.log("Tiempo estimado obtenido:", tiempoEstimado);
            } else {
                console.warn("No se pudo obtener tiempo estimado, usando valor por defecto");
            }
        } catch (tiempoError) {
            console.warn("Error al obtener tiempo estimado:", tiempoError);
            // Mantener el valor por defecto
        }

        // 2. Luego generar el ticket
        console.log("Generando ticket...");
        const response = await fetch(`${API_BASE_URL}/api/ticket`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                matricula: MatriculaOFolioIngresado,
                sector 
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Error al generar el ticket");
        }

        // ✅ Actualizar campos visibles del ticket
        const matriculaFolio = document.getElementById("matricula-o-folio");
        matriculaFolio.textContent = noMatriculaCheckbox.checked ? "Folio:" : "Matrícula:";

        document.getElementById("result-matricula-o-folio").textContent = MatriculaOFolioIngresado;
        document.getElementById("result-sector").textContent = data.sector || sector;
        document.getElementById("result-ticket").textContent = data.folio || ("T-" + Math.floor(Math.random() * 1000));
        if (data.fecha) document.getElementById("result-fecha").textContent = data.fecha;

        // ✅ Mostrar tiempo estimado de espera
        const tiempoEstimadoElement = document.getElementById("tiempo-estimado-minutos");
        if (tiempoEstimadoElement) {
            tiempoEstimadoElement.textContent = tiempoEstimado;
            console.log("Tiempo estimado mostrado en UI:", tiempoEstimado);
        }

        // ✅ Cambiar vistas
        formContainer.classList.add("hidden");
        ticketResult.classList.remove("hidden");
        errorMessage.classList.add("hidden");

    } catch (err) {
        showError(err.message);
    }
});

    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.remove("hidden");
    }

    window.resetForm = function() {
        form.reset();
        formContainer.classList.remove("hidden");
        ticketResult.classList.add("hidden");
        errorMessage.classList.add("hidden");
        // Restablecer texto y placeholder
        matriculaFolioLabel.textContent = "Matrícula";
        inputMatriculaFolio.placeholder = "Ingresa tu matrícula";
    };
    
});

async function imprimir() {
    const matricula = document.getElementById("result-matricula-o-folio").textContent.trim();
    const sector = document.getElementById("result-sector").textContent.trim();
    const numero_ticket = document.getElementById("result-ticket").textContent.trim();
    const fecha = document.getElementById("result-fecha").textContent.trim();
    const tiempo_estimado = document.getElementById("tiempo-estimado-minutos").textContent.trim();

    try {
        // 1️⃣ Pedimos el PDF al backend
        const response = await fetch(`${API_BASE_URL}/api/ticket/download`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ matricula, numero_ticket, sector, fecha, tiempo_estimado })
        });

        if (!response.ok) throw new Error("Error al generar el PDF");

        const blob = await response.blob();

        // 2️⃣ Convertimos el PDF a base64 para QZ
        const reader = new FileReader();
        reader.onload = async function() {
            const base64PDF = reader.result.split(",")[1]; // solo la parte base64

            // 3️⃣ Conectamos con QZ Tray
            await qz.websocket.connect();

            // 4️⃣ Elegimos la impresora (predeterminada o específica)
            const printer = await qz.printers.find("POS-58");
            const config = qz.configs.create(printer);

            // 5️⃣ Mandamos a imprimir
            const printData = [{
                type: 'pdf',
                format: 'base64',
                data: base64PDF
            }];

            await qz.print(config, printData);

            // 6️⃣ Desconectamos
            qz.websocket.disconnect();

            console.log("Ticket impreso correctamente");
        };

        reader.readAsDataURL(blob);

    } catch (error) {
        console.error("Error al imprimir:", error);
        alert("No se pudo imprimir el ticket. Intenta de nuevo.");
    }
}

async function descargar() {
    // Obtener los datos visibles del ticket
    const matricula = document.getElementById("result-matricula-o-folio").textContent.trim();
    const sector = document.getElementById("result-sector").textContent.trim();
    const numero_ticket = document.getElementById("result-ticket").textContent.trim();
    const fecha = document.getElementById("result-fecha").textContent.trim();
    const tiempo_estimado = document.getElementById("tiempo-estimado-minutos").textContent.trim();

    try {
        const response = await fetch(`${API_BASE_URL}/api/ticket/download`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                matricula,
                numero_ticket,
                sector,
                fecha,
                tiempo_estimado
            })
        });

        if (!response.ok) {
            throw new Error("Error al generar el PDF desde el servidor");
        }

        // Recibimos el PDF como Blob
        const blob = await response.blob();
        const pdfURL = URL.createObjectURL(blob);

        // Crear un enlace temporal para forzar descarga
        const a = document.createElement("a");
        a.href = pdfURL;
        a.download = `ticket_${numero_ticket}.pdf`; // nombre del archivo descargado
        document.body.appendChild(a);
        a.click();

        // Limpieza
        a.remove();
        URL.revokeObjectURL(pdfURL);
    } catch (error) {
        console.error("Error al imprimir:", error);
        alert("No se pudo generar el ticket. Intenta de nuevo.");
    }
}