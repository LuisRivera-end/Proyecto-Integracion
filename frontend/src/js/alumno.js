import Config from './config.js';
import { lanzarAlerta } from './alertas/notifier.js';
import { waitForBackend } from './healthcheck.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", async () => {
    const formContainer = document.getElementById("form-container");
    const ticketResult = document.getElementById("ticket-result");
    const errorMessage = document.getElementById("error-message");
    const errorText = document.getElementById("error-text");
    const sectorButtonsContainer = document.getElementById("sector-buttons");

    // Cargar sectores dinámicamente desde la API y renderizar como botones
    async function cargarSectores() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/sectores`);
            const sectores = await response.json();
            sectorButtonsContainer.innerHTML = "";
            sectores.forEach((s, i) => {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.textContent = s.Sector;
                // #b2d4b3 otra opcion del color
                btn.className = "w-full bg-[#a1d99b] border border-slate-200 text-slate-700 font-semibold px-5 py-5 rounded-xl transition-all duration-200 shadow-sm hover:bg-emerald-600 hover:text-white hover:border-emerald-600 hover:shadow-md transform hover:-translate-y-0.5 min-h-[64px] text-lg cursor-pointer flex items-center justify-center";
                // Si es el último y el total es impar, centrar el botón
                if (sectores.length % 2 !== 0 && i === sectores.length - 1) {
                    btn.classList.add("col-span-2", "justify-self-center", "max-w-[calc(50%-0.5rem)]");
                }
                btn.addEventListener("click", () => handleSectorClick(s.Sector, btn));
                sectorButtonsContainer.appendChild(btn);
            });
        } catch (error) {
            console.error("Error al cargar sectores:", error);
        }
    }

    // Esperar al backend antes de cargar datos
    await waitForBackend();
    cargarSectores();

    // Generar ticket directamente al hacer clic en un botón de sector
    async function generarTicket(sector, btn, tipoCaja = 'normal') {
        // Deshabilitar todos los botones mientras se genera el ticket
        const allButtons = sectorButtonsContainer.querySelectorAll("button");
        allButtons.forEach(b => b.disabled = true);

        const originalText = btn.textContent;
        btn.innerHTML = '<span class="flex items-center justify-center gap-2"><svg class="animate-spin h-5 w-5 border-b-2 border-white rounded-full" viewBox="0 0 24 24"></svg> Generando...</span>';

        try {
            const response = await fetch(`${API_BASE_URL}/api/ticket`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sector, tipo_caja: tipoCaja })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Error al generar el ticket");
            }

            document.getElementById("result-sector").textContent = data.sector || sector;
            document.getElementById("result-ticket").textContent = data.folio;
            if (data.fecha) document.getElementById("result-fecha").textContent = data.fecha;

            // Guardar el tipo de ticket en un atributo para usar en impresión/descarga
            document.getElementById("ticket-result").setAttribute("data-ticket-type", tipoCaja);

            // Cambiar vistas
            formContainer.classList.add("hidden");
            ticketResult.classList.remove("hidden");
            errorMessage.classList.add("hidden");

        } catch (err) {
            showError(err.message);
        } finally {
            allButtons.forEach(b => b.disabled = false);
            btn.textContent = originalText;
        }
    }

    // Manejo de selección de sector con verificación de Caja Rápida
    async function handleSectorClick(sector, btn) {
        // Solo verificar Caja Rápida si el sector es "Cajas"
        if (sector.toLowerCase() === 'cajas') {
            try {
                const res = await fetch(`${API_BASE_URL}/api/caja-rapida/estado`);
                const estado = await res.json();

                if (estado.activo) {
                    // Mostrar modal de selección
                    mostrarModalCaja(sector, btn);
                    return;
                }
            } catch (err) {
                console.error('Error al verificar Caja Rápida:', err);
            }
        }

        // Flujo normal
        generarTicket(sector, btn, 'normal');
    }

    function mostrarModalCaja(sector, btn) {
        const modal = document.getElementById('caja-modal');
        const btnNormal = document.getElementById('caja-modal-normal');
        const btnRapida = document.getElementById('caja-modal-rapida');
        const btnCancel = document.getElementById('caja-modal-cancel');

        modal.classList.remove('hidden');
        modal.classList.add('flex');

        function cleanup() {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            btnNormal.removeEventListener('click', onNormal);
            btnRapida.removeEventListener('click', onRapida);
            btnCancel.removeEventListener('click', onCancel);
        }

        function onNormal() {
            cleanup();
            generarTicket(sector, btn, 'normal');
        }

        function onRapida() {
            cleanup();
            generarTicket(sector, btn, 'rapida');
        }

        function onCancel() {
            cleanup();
        }

        btnNormal.addEventListener('click', onNormal);
        btnRapida.addEventListener('click', onRapida);
        btnCancel.addEventListener('click', onCancel);
    }

    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.remove("hidden");
    }

    window.resetForm = function () {
        formContainer.classList.remove("hidden");
        ticketResult.classList.add("hidden");
        errorMessage.classList.add("hidden");
    };

    // Configurar Socket.IO para escuchar actualizaciones en tiempo real
    if (typeof io !== 'undefined') {
        const socket = io(API_BASE_URL);

        socket.on('connect', () => {
            console.log('Conectado al servidor de WebSockets');
        });

        socket.on('sectores_updated', async () => {
            console.log('Actualización de sectores por WebSocket');
            await cargarSectores();
        });

        socket.on('disconnect', () => {
            console.error('Desconectado del servidor de WebSockets');
        });
    } else {
        console.error('No se pudo conectar al WebSocket');
    }

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
            lanzarAlerta('Ticket enviado a impresora POS-58', 'success');
        } else {
            throw new Error(result.error || "Error al imprimir");
        }

    } catch (error) {
        console.error('❌ Error impresión directa:', error);
        lanzarAlerta(error.message || 'Error al enviar a impresora', 'error');
    }
}

window.imprimir = imprimir;
