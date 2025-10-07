const matriculaFolioLabel = document.getElementById("matricula-folio-label");
const noMatriculaCheckbox = document.getElementById("no-matricula-checkbox");
const inputMatriculaFolio = document.getElementById("input-matricula-folio");
const form = document.getElementById("ticket-form");
const formContainer = document.getElementById("form-container");
const ticketResult = document.getElementById("ticket-result");
const errorMessage = document.getElementById("error-message");
const errorText = document.getElementById("error-text");

noMatriculaCheckbox.addEventListener("click", () => {
    if (noMatriculaCheckbox.checked) {
        matriculaFolioLabel.textContent = "Folio";
        inputMatriculaFolio.placeholder = "Ingresa tu folio";
    } else {
        matriculaFolioLabel.textContent = "Matrícula";
        inputMatriculaFolio.placeholder = "Ingresa tu matrícula";
    }
});

form.addEventListener("submit", function(e) {
    e.preventDefault();
    const MatriculaOFolioIngresado = inputMatriculaFolio.value.trim();
    const sector = document.getElementById("sector").value;

    if (!MatriculaOFolioIngresado|| !sector) {
        errorText.textContent = "Por favor, completa todos los campos.";
        errorMessage.classList.remove("hidden");
        return;
    }

    errorMessage.classList.add("hidden");

    
    const ticket = "T-" + Math.floor(Math.random() * 1000);

    const matriculaFolio = document.getElementById("matricula-o-folio");
    if (noMatriculaCheckbox.checked) {
        
        matriculaFolio.textContent = "Folio:";
    } else {
        
        matriculaFolio.textContent = "Matrícula:";
    } 
    document.getElementById("result-matricula-o-folio").textContent = MatriculaOFolioIngresado;
    document.getElementById("result-sector").textContent = sector;
    document.getElementById("result-ticket").textContent = ticket;

    formContainer.classList.add("hidden");
    ticketResult.classList.remove("hidden");
});


function resetForm() {
    form.reset();
    ticketResult.classList.add("hidden");
    formContainer.classList.remove("hidden");
    location.reload();
}