let descansosCount = 0;

// Login demo
document.getElementById("login-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const user = document.getElementById("username").value;
  const pass = document.getElementById("password").value;

  if (user === "admin" && pass === "admin123") {
    document.getElementById("login-screen").classList.add("hidden");
    document.getElementById("management-screen").classList.remove("hidden");
  } else {
    document.getElementById("login-error").classList.remove("hidden");
  }
});

// Tabs
function selectSector(sector) {
    document.querySelectorAll(".sector-tab").forEach(tab => {
      tab.classList.remove("bg-cyan-400", "text-white");
      tab.classList.add("bg-gray-500", "text-gray-400", "hover:bg-gray-700");
    });
  
    const activeTab = document.getElementById(`tab-${sector}`);
    activeTab.classList.remove("bg-gray-500", "text-gray-400", "hover:bg-gray-700");
    activeTab.classList.add("bg-cyan-400", "text-white");
}
  
function selectEmployee() {
    const contenedor = document.getElementById("contenedor");

    const select = document.createElement("select");
    select.className = "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition";
    
    const opciones = [
      { value: "", text: "Seleccionar empleado" },
      { value: "empleado1", text: "Empleado 1" },
      { value: "empleado2", text: "Empleado 2" },
      { value: "empleado3", text: "Empleado 3" },
      { value: "empleado3", text: "Empleado 4" }
    ];

    opciones.forEach(op => {
      const option = document.createElement("option");
      option.value = op.value;
      option.textContent = op.text;
      select.appendChild(option);
    });
    contenedor.appendChild(select);
}

// descanso
function addDescanso(inicio = "", fin = "") {
  const container = document.getElementById("descansos-container");
  const id = descansosCount++;
  const html = `
    <div id="descanso-${id}" class="flex flex-col md:flex-row gap-3 items-center bg-gray-50 p-4 rounded-lg border">
      <input type="time" class="flex-1 border rounded px-2 py-1" value="${inicio}">
      <input type="time" class="flex-1 border rounded px-2 py-1" value="${fin}">
      <button type="button" onclick="removeDescanso(${id})"
              class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded">X</button>
    </div>`;
  container.insertAdjacentHTML("beforeend", html);
}
function removeDescanso(id) {
  document.getElementById(`descanso-${id}`).remove();
}

// exito
document.getElementById("agenda-form").addEventListener("submit", (e) => {
  e.preventDefault();
  document.getElementById("success-message").classList.remove("hidden");
  setTimeout(() => {
    document.getElementById("success-message").classList.add("hidden");
  }, 2000);
});

// eliminar tickets 
function deleteTicket(button) {
  const row = button.closest("tr");
  row.remove();
  alert("Ticket eliminado correctamente");
}

// Logout
function logout() {
  document.getElementById("login-form").reset();
  document.getElementById("management-screen").classList.add("hidden");
  document.getElementById("login-screen").classList.remove("hidden");
}
selectEmployee();