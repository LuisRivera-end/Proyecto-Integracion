import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

async function logout() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/logout`, {
            method: "POST",
            credentials: "include"  
        });
        const data = await res.json();
        alert(data.message);
        // Redirigir a login o recargar la página
        window.location.href = "/login.html";
    } catch (error) {
        console.error("Error al cerrar sesión:", error);
    }
}
window.logout = logout;