import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ticket-form");
    const formContainer = document.getElementById("form-container");
    const ticketResult = document.getElementById("ticket-result");
    const errorMessage = document.getElementById("error-message");
    const errorText = document.getElementById("error-text");
    const submitBtn = form.querySelector("button[type='submit']");

    // Custom dropdown elements
    const sectorInput = document.getElementById("sector");
    const sectorToggle = document.getElementById("sector-toggle");
    const sectorLabel = document.getElementById("sector-label");
    const sectorOptions = document.getElementById("sector-options");
    const sectorArrow = document.getElementById("sector-arrow");

    // Toggle dropdown
    sectorToggle.addEventListener("click", () => {
        const isOpen = !sectorOptions.classList.contains("hidden");
        sectorOptions.classList.toggle("hidden");
        sectorArrow.classList.toggle("rotate-180");
        if (!isOpen) {
            sectorToggle.classList.add("border-slate-500", "ring-2", "ring-slate-500");
        } else {
            sectorToggle.classList.remove("border-slate-500", "ring-2", "ring-slate-500");
        }
    });

    // Close dropdown on outside click
    document.addEventListener("click", (e) => {
        if (!e.target.closest("#custom-select")) {
            sectorOptions.classList.add("hidden");
            sectorArrow.classList.remove("rotate-180");
            sectorToggle.classList.remove("border-slate-500", "ring-2", "ring-slate-500");
        }
    });

    // Select option handler
    function selectSector(value, text) {
        sectorInput.value = value;
        sectorLabel.textContent = text;
        sectorLabel.classList.remove("text-slate-400");
        sectorLabel.classList.add("text-slate-800");
        sectorOptions.classList.add("hidden");
        sectorArrow.classList.remove("rotate-180");
        sectorToggle.classList.remove("border-slate-500", "ring-2", "ring-slate-500");
        // Highlight selected
        sectorOptions.querySelectorAll("button").forEach(btn => {
            btn.classList.remove("bg-slate-100", "font-bold");
            if (btn.dataset.value === value) {
                btn.classList.add("bg-slate-100", "font-bold");
            }
        });
    }

    // Cargar sectores dinámicamente desde la API
    async function cargarSectores() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/sectores`);
            const sectores = await response.json();
            sectorOptions.innerHTML = "";
            sectores.forEach(s => {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.dataset.value = s.Sector;
                btn.textContent = s.Sector;
                btn.className = "w-full text-left px-5 py-4 text-lg md:text-xl text-slate-700 hover:bg-emerald-50 hover:text-emerald-700 active:bg-emerald-100 transition-colors border-b border-slate-100 last:border-b-0 cursor-pointer";
                btn.addEventListener("click", () => selectSector(s.Sector, s.Sector));
                sectorOptions.appendChild(btn);
            });
        } catch (error) {
            console.error("Error al cargar sectores:", error);
        }
    }
    cargarSectores();

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const sector = document.getElementById("sector").value;

        if (!sector) {
            showError("Por favor, selecciona un sector.");
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<svg class="animate-spin h-5 w-5 mr-2 border-b-2 border-blue-600 rounded-full" viewBox="0 0 24 24"></svg> Generando ticket...';
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

            if (!response.ok) {
                throw new Error(data.error || "Error al generar el ticket");
            }
            document.getElementById("result-sector").textContent = data.sector || sector;
            document.getElementById("result-ticket").textContent = data.folio;
            if (data.fecha) document.getElementById("result-fecha").textContent = data.fecha;

            // Guardar el tipo de ticket en un atributo para usar en impresión/descarga
            document.getElementById("ticket-result").setAttribute("data-ticket-type", "normal");

            // Cambiar vistas
            formContainer.classList.add("hidden");
            ticketResult.classList.remove("hidden");
            errorMessage.classList.add("hidden");

        } catch (err) {
            showError(err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Generar Ticket';
        }
    });

    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.remove("hidden");
    }

    window.resetForm = function () {
        form.reset();
        sectorInput.value = "";
        sectorLabel.textContent = "Selecciona un sector";
        sectorLabel.classList.add("text-slate-400");
        sectorLabel.classList.remove("text-slate-800");
        sectorOptions.querySelectorAll("button").forEach(btn => btn.classList.remove("bg-slate-100", "font-bold"));
        formContainer.classList.remove("hidden");
        ticketResult.classList.add("hidden");
        errorMessage.classList.add("hidden");
    };

});

async function imprimir() {
    const sector = document.getElementById("result-sector").textContent.trim();
    const numero_ticket = document.getElementById("result-ticket").textContent.trim();
    const fecha = document.getElementById("result-fecha").textContent.trim();
    console.log('🖨️ Enviando a impresión directa...');

    console.log('🖨️ Datos para impresión:', {
        numero_ticket,
        sector,
        fecha,
    });

    try {
        const response = await fetch(`${API_BASE_URL}/api/ticket/print`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                numero_ticket,
                sector,
                fecha,
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

async function descargarPDF() {
    const sector = document.getElementById("result-sector").textContent.trim();
    const numero_ticket = document.getElementById("result-ticket").textContent.trim();
    const fecha = document.getElementById("result-fecha").textContent.trim();

    try {
        const response = await fetch(`${API_BASE_URL}/api/ticket/download`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                numero_ticket,
                sector,
                fecha
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Error al generar el PDF");
        }

        // Convertir base64 a Blob y descargar
        const byteCharacters = atob(result.pdf_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/pdf' });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = result.filename || `ticket_${numero_ticket}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('❌ Error al descargar PDF:', error);
        alert('Error al descargar el PDF: ' + error.message);
    }
}

window.descargarPDF = descargarPDF;