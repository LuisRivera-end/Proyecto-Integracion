const API_BASE_URL = window.location.hostname === "localhost" 
    ? "http://localhost:5000"
    : "http://backend:5000"; 

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById('ticket-form');
    const formContainer = document.getElementById('form-container');
    const ticketResult = document.getElementById('ticket-result');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const matriculaInput = document.getElementById('input-matricula-folio');
        const sectorInput = document.getElementById('sector');

        const matricula = matriculaInput.value.trim();
        const sector = sectorInput.value;

        if (!matricula || !sector) {
            showError("Debes completar matrícula y sector.");
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/ticket`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ matricula, sector })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Error al generar el ticket");
            }

            // Ocultar el formulario y mostrar el ticket
            formContainer.classList.add('hidden');
            ticketResult.classList.remove('hidden');
            errorMessage.classList.add('hidden');

            // Actualizar los campos del ticket
            document.getElementById('result-fecha').textContent = data.fecha;
            document.getElementById('result-matricula-o-folio').textContent = data.alumno;
            document.getElementById('result-ticket').textContent = data.folio;
            document.getElementById('result-sector').textContent = data.sector;

        } catch (err) {
            showError(err.message);
        }
    });

    // Función para mostrar mensaje de error
    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    // Función para resetear el formulario y la pantalla de ticket
    window.resetForm = function() {
        form.reset();
        ticketResult.classList.add('hidden');
        formContainer.classList.remove('hidden');
        errorMessage.classList.add('hidden');
    };
});
