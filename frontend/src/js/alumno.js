import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ticket-form");
    const formContainer = document.getElementById("form-container");
    const ticketResult = document.getElementById("ticket-result");
    const errorMessage = document.getElementById("error-message");
    const errorText = document.getElementById("error-text");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const sector = document.getElementById("sector").value;

        if (!sector) {
            showError("Por favor, selecciona un sector.");
            return;
        }
        try {
            // 1. Generar el ticket
            let response, data;
                response = await fetch(`${API_BASE_URL}/api/ticket`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        sector
                    })
                });

            data = await response.json();
            console.log("🎯 Respuesta API ticket:", data);

            if (!response.ok) {
                throw new Error(data.error || "Error al generar el ticket");
            }
            document.getElementById("result-sector").textContent = data.sector || sector;
            document.getElementById("result-ticket").textContent = data.folio;
            if (data.fecha) document.getElementById("result-fecha").textContent = data.fecha;

            if (data.qr_url) {
                const qrContainer = document.getElementById("qr-container");
                const qrImage = document.getElementById("qr-image");
                const qrLink = document.getElementById("qr-link");

                qrImage.src = data.qr_url;
                if (qrLink) qrLink.href = data.pdf_url || data.qr_url;
                qrContainer.classList.remove("hidden");
            }
            // Cambiar vistas
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

    window.resetForm = function () {
        form.reset();
        formContainer.classList.remove("hidden");
        ticketResult.classList.add("hidden");
        errorMessage.classList.add("hidden");
    };

});

async function imprimir() {
    const sector = document.getElementById("result-sector").textContent.trim();
    const numero_ticket = document.getElementById("result-ticket").textContent.trim();
    const fecha = document.getElementById("result-fecha").textContent.trim();
    const tiempo_estimado = document.getElementById("tiempo-estimado-minutos").textContent.trim();
    console.log('🖨️ Enviando a impresión directa...');

    console.log('🖨️ Datos para impresión:', {
        numero_ticket, 
        sector, 
        fecha, 
        tiempo_estimado,
    }); 

    try {
        const response = await fetch(`${API_BASE_URL}/api/ticket/print`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
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

window.imprimir = imprimir;