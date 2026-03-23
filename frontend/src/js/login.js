import Config from './config.js';


const API_BASE_URL = Config.API_BASE_URL;

document.addEventListener("DOMContentLoaded", async () => {
    const loginForm = document.getElementById("login-form");
    const loginError = document.getElementById("login-error");


    // Limpiar sesión anterior al cargar login
    localStorage.removeItem('currentUser');

    if (loginForm) {
        const submitBtn = loginForm.querySelector("button[type='submit']");
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<svg class="animate-spin h-5 w-5 mr-2 border-b-2 border-blue-600 rounded-full" viewBox="0 0 24 24"></svg> Iniciando sesión...';

            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value.trim();

            function showError(message) {
                if (loginError) {
                    loginError.textContent = message;
                    loginError.classList.remove("hidden");

                    setTimeout(() => {
                        loginError.classList.add("hidden");
                    }, 3000);
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

                if (currentUser.rol === 6) {
                    // Jefe de Departamento → vista de empleados de su sector
                    localStorage.setItem('currentUser', JSON.stringify(currentUser));
                    window.location.href = "subjefes.html";
                    return;
                }

                // Si pasa la validación, seguimos con la ventanilla
                const ventanillaActivaRes = await fetch(`${API_BASE_URL}/api/empleado/${currentUser.id}/ventanilla-activa`);
                if (!ventanillaActivaRes.ok) {
                    throw new Error("Error al verificar ventanilla del empleado");
                }

                const ventanillaActiva = await ventanillaActivaRes.json();
                if ((ventanillaActiva && ventanillaActiva.ID_Ventanilla) || currentUser.rol === 6) {
                    console.log("Sesión válida:", currentUser.rol === 6 ? "Jefe de Departamento" : "Operador con ventanilla");

                    if (ventanillaActiva && ventanillaActiva.ID_Ventanilla) {
                        currentUser.ventanilla = {
                            id: ventanillaActiva.ID_Ventanilla,
                            nombre: ventanillaActiva.Ventanilla
                        };
                    }

                    // Guardar sesión en localStorage
                    localStorage.setItem('currentUser', JSON.stringify(currentUser));

                    // Redirigir a ventanilla.html
                    window.location.href = "ventanilla.html";
                    return;
                }

                showError("No tienes una ventanilla asignada. Contacta al administrador.");
                return;

            } catch (err) {
                console.error("Error en login:", err);
                showError(err.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Iniciar Sesión';
            }
        });
    }
});
