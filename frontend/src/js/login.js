import Config from './config.js';

const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", async () => {
    const loginForm = document.getElementById("login-form");
    const loginError = document.getElementById("login-error");
    const errorMessage = document.getElementById("error-message");
    const errorText = document.getElementById("error-text");

    // Limpiar sesión anterior al cargar login
    localStorage.removeItem('currentUser');

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value.trim();

            function showError(message) {
                if (errorText) errorText.textContent = message;
                if (errorMessage) errorMessage.classList.remove("hidden");
                if (loginError) {
                    loginError.textContent = message;
                    loginError.classList.remove("hidden");
                }
            }

            try {
                // Primero hacemos el login
                const res = await fetch(`${API_BASE_URL}/api/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                if (!res.ok) {
                    const errorData = await res.json();
                    throw new Error(errorData.error || "Credenciales incorrectas");
                }

                const data = await res.json();
                const currentUser = { 
                    id: data.id, 
                    username: data.nombre, 
                    rol: data.rol, 
                    sector: data.sector 
                };

                if (currentUser.rol === 1) {
                    // Guardar sesión para admin si es necesario, o redirigir directo
                    localStorage.setItem('currentUser', JSON.stringify(currentUser));
                    window.location.href = "admin.html";
                    return;
                }

                const ahora = new Date();
                const dia = ahora.getDay();
                const hora = ahora.getHours();

                if (dia === 0) {
                    showError("No se puede acceder a ventanilla en los domingos.");
                    return;
                } else if (dia >= 1 && dia <= 5) {
                    if (hora < 8 || hora >= 17) {
                        showError("Solo se puede acceder de lunes a viernes de 8:00 a 17:00.");
                        return;
                    }
                } else if (dia === 6) {
                    if (hora < 8 || hora >= 14) {
                        showError("Solo se puede acceder los sábados de 8:00 a 14:00.");
                        return;
                    }
                }

                // Si pasa la validación, seguimos con la ventanilla
                const ventanillaActivaRes = await fetch(`${API_BASE_URL}/api/empleado/${currentUser.id}/ventanilla-activa`);
                if (!ventanillaActivaRes.ok) {
                    throw new Error("Error al verificar ventanilla del empleado");
                }

                const ventanillaActiva = await ventanillaActivaRes.json();
                if (ventanillaActiva && ventanillaActiva.ID_Ventanilla) {
                    console.log("Usando ventanilla asignada:", ventanillaActiva);
                    currentUser.ventanilla = {
                        id: ventanillaActiva.ID_Ventanilla,
                        nombre: ventanillaActiva.Ventanilla
                    };
                    
                    // Guardar sesión en localStorage
                    localStorage.setItem('currentUser', JSON.stringify(currentUser));
                    
                    // Redirigir a gestion.html
                    window.location.href = "gestion.html";
                    return;
                }

                alert("No tienes una ventanilla asignada. Contacta al administrador.");
                return;

            } catch (err) {
                console.error("Error en login:", err);
                showError(err.message);
            }
        });
    }
});
