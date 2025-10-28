import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("ticket-form");
    const formContainer = document.getElementById("form-container");
    const ticketResult = document.getElementById("ticket-result");
    const errorMessage = document.getElementById("error-message");
    const errorText = document.getElementById("error-text");

    const noMatriculaCheckbox = document.getElementById("no-matricula-checkbox");
    const matriculaFolioLabel = document.getElementById("matricula-folio-label");
    const inputMatriculaFolio = document.getElementById("input-matricula-folio");

    // Manejar cambios en el checkbox de invitado
noMatriculaCheckbox.addEventListener('change', function(e) {
    const inputMatricula = document.getElementById('input-matricula-folio');
    const invitadoInfo = document.getElementById('invitado-info');
    
    if (this.checked) {
        matriculaFolioLabel.textContent = "Tipo";
        inputMatricula.placeholder = "No requerido para invitados";
        inputMatricula.value = "";
        inputMatricula.setAttribute('disabled', 'disabled');
        inputMatricula.classList.add('bg-slate-100', 'text-slate-400');
        invitadoInfo.classList.remove('hidden');
    } else {
        matriculaFolioLabel.textContent = "Matrícula";
        inputMatricula.placeholder = "Ingresa tu matrícula";
        inputMatricula.removeAttribute('disabled');
        inputMatricula.classList.remove('bg-slate-100', 'text-slate-400');
        invitadoInfo.classList.add('hidden');
    }
});

    form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const MatriculaOFolioIngresado = inputMatriculaFolio.value.trim();
    const sector = document.getElementById("sector").value;
    const esInvitado = noMatriculaCheckbox.checked;

    if ((!esInvitado && !MatriculaOFolioIngresado) || !sector) {
            showError("Por favor, completa todos los campos.");
            return;
        }
        
    const ahora = new Date();
    const dia = ahora.getDay(); 
    const hora = ahora.getHours();

        if (dia === 0) {
            showError("No se pueden generar tickets los domingos.");
            return;
        } else if (dia >= 1 && dia <= 5) { 
            if (hora < 8 || hora >= 17) {
                showError("Solo se pueden generar tickets de lunes a viernes de 8:00 a 17:00.");
                return;
            }
        } else if (dia === 6) { 
            if (hora < 8 || hora >= 14) {
                showError("Solo se pueden generar tickets los sábados de 8:00 a 14:00.");
                return;
            }
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
        let response, data;
        if (esInvitado) {
                // GENERAR TICKET INVITADO
                console.log("Generando ticket para INVITADO");
                response = await fetch(`${API_BASE_URL}/api/ticket/invitado`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                        sector 
                    })
                });
            } else {
                // GENERAR TICKET NORMAL (alumno)
                console.log("Generando ticket para ALUMNO");
                response = await fetch(`${API_BASE_URL}/api/ticket`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                        matricula: MatriculaOFolioIngresado,
                        sector 
                    })
                });
            }

        data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Error al generar el ticket");
        }

        const matriculaFolio = document.getElementById("matricula-o-folio");
        if (esInvitado) {
                matriculaFolio.textContent = "Tipo:";
                document.getElementById("result-matricula-o-folio").textContent = "Invitado";
                document.getElementById("result-matricula-o-folio").style.fontWeight = "bold";
            } else {
                matriculaFolio.textContent = "Matrícula:";
                document.getElementById("result-matricula-o-folio").textContent = MatriculaOFolioIngresado;
                document.getElementById("result-matricula-o-folio").style.fontWeight = "normal";
            }

            document.getElementById("result-sector").textContent = data.sector || sector;
            document.getElementById("result-ticket").textContent = data.folio;
            if (data.fecha) document.getElementById("result-fecha").textContent = data.fecha;

            // Guardar el tipo de ticket en un atributo para usar en impresión/descarga
            document.getElementById("ticket-result").setAttribute("data-ticket-type", esInvitado ? "invitado" : "normal");

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
        noMatriculaCheckbox.checked = false;
        noMatriculaCheckbox.dispatchEvent(new Event('change'));
    };
    
});

async function imprimir() {
    const matricula = document.getElementById("result-matricula-o-folio").textContent.trim();
    const sector = document.getElementById("result-sector").textContent.trim();
    const numero_ticket = document.getElementById("result-ticket").textContent.trim();
    const fecha = document.getElementById("result-fecha").textContent.trim();
    const tiempo_estimado = document.getElementById("tiempo-estimado-minutos").textContent.trim();
    const esInvitado = document.getElementById("ticket-result").getAttribute("data-ticket-type") === "invitado";

    console.log('🖨️ Enviando a impresión directa...');

    try {
        const response = await fetch(`${API_BASE_URL}/api/ticket/print`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                matricula: esInvitado ? null : matricula, // Para invitados, enviar null
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
    const GOOGLE_LOGIN_URL = `${API_BASE_URL}/api/login_google`; 
    const matricula = document.getElementById("result-matricula-o-folio").textContent.trim();
    const sector = document.getElementById("result-sector").textContent.trim();
    const numero_ticket = document.getElementById("result-ticket").textContent.trim();
    const fecha = document.getElementById("result-fecha").textContent.trim();
    const tiempo_estimado = document.getElementById("tiempo-estimado-minutos").textContent.trim();
    const esInvitado = document.getElementById("ticket-result").getAttribute("data-ticket-type") === "invitado";

    try {
        const response = await fetch(`${API_BASE_URL}/api/ticket/download`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                matricula: esInvitado ? null : matricula, // Para invitados, enviar null
                numero_ticket,
                sector,
                fecha,
                tiempo_estimado
            })
        });

        if (response.status === 401) {
            alert("⚠️ Autenticación de Google Drive requerida. Serás redirigido para iniciar sesión y autorizar a la aplicación.");
            window.location.href = GOOGLE_LOGIN_URL;
            return; 
        }

        const data = await response.json();
        if (!response.ok) {
            // Manejar otros errores (ej. 500, 400, o fallos de subida a Drive)
            const errorMessage = data.error || "Error desconocido en el servidor";
            throw new Error(errorMessage);
        }

        // Éxito: El PDF fue subido exitosamente a Google Drive
        console.log("✅ Subida exitosa - Respuesta completa:", data);

        if (data.drive_info && data.drive_info.view_link) {
            alert(`✅ Ticket subido a Google Drive\n\n📁 Ver en Drive: ${data.drive_info.view_link}\n\nHaz clic en OK para abrir el archivo.`);

            // Abrir automáticamente en nueva pestaña
            window.open(data.drive_info.view_link, '_blank');
        } else {
            alert("✅ Ticket procesado, pero no se obtuvo link de Drive");
        }
    } catch (error) {
        console.error("Error al generar/subir ticket:", error);
        alert(`❌ No se pudo subir el ticket: ${error.message}.`);
    }
}

window.imprimir = imprimir;
window.descargar = descargar;