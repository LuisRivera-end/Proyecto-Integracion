const form = document.getElementById("ticket-form");
const formContainer = document.getElementById("form-container");
const ticketResult = document.getElementById("ticket-result");
const errorMessage = document.getElementById("error-message");
const errorText = document.getElementById("error-text");

form.addEventListener("submit", function(e) {
    e.preventDefault();

    const matricula = document.getElementById("matricula").value.trim();
    const sector = document.getElementById("sector").value;

    if (!matricula || !sector) {
        errorText.textContent = "Por favor, completa todos los campos.";
        errorMessage.classList.remove("hidden");
        return;
    }

    errorMessage.classList.add("hidden");

    // filio random
    const folio = "T-" + Math.floor(Math.random() * 1000);

    document.getElementById("result-matricula").textContent = matricula;
    document.getElementById("result-sector").textContent = sector;
    document.getElementById("result-folio").textContent = folio;

    formContainer.classList.add("hidden");
    ticketResult.classList.remove("hidden");
});

function resetForm() {
    form.reset();
    ticketResult.classList.add("hidden");
    formContainer.classList.remove("hidden");
}