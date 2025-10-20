const API_BASE_URL = "https://localhost:4443";

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
            // Obtener tiempo estimado de espera para el sector específico
            let tiempoEstimado = 5; // Valor por defecto actualizado
            
            try {
                const tiempoResponse = await fetch(`${API_BASE_URL}/api/tiempo_espera_promedio/${encodeURIComponent(sector)}`);
                if (tiempoResponse.ok) {
                    const tiempoData = await tiempoResponse.json();
                    tiempoEstimado = tiempoData.tiempo_estimado;
                }
            } catch (tiempoError) {
                console.warn("No se pudo obtener el tiempo estimado:", tiempoError);
                // Usar valor por defecto si falla
            }

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

    console.log('🖨️ Enviando a impresión directa...');

    try {
        const response = await fetch(`${API_BASE_URL}/api/ticket/print`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                matricula, 
                numero_ticket, 
                sector, 
                fecha, 
                tiempo_estimado 
            })
        });

        const result = await response.json();
        
        if (response.ok) {
            console.log('✅ Ticket enviado a impresora:', result.message);
            alert('Ticket enviado a impresora POS-58');
        } else {
            throw new Error(result.error || "Error al imprimir");
        }

    } catch (error) {
        console.error('❌ Error impresión directa:', error);
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