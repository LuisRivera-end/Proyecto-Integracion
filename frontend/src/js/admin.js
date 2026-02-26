import Config from './config.js';
import { lanzarAlerta } from './alertas/notifier.js';
const API_BASE_URL = Config.API_BASE_URL;

async function logout() {
    try {
        const res = await fetch(`${API_BASE_URL}/api/logout`, {
            method: "POST",
            credentials: "include"
        });

        const data = await res.json();

        lanzarAlerta(data.message || "Sesión cerrada", 'success');

        // Esperar 1.5 segundos antes de redirigir
        setTimeout(() => {
            window.location.href = "/login.html";
        }, 1500);

    } catch (error) {
        console.error("Error al cerrar sesión:", error);
        lanzarAlerta(error.message || "Error al cerrar sesión", 'error');
    }
}
window.logout = logout;

// ─── Limpieza semestral automática ───
async function verificarLimpiezaSemestral() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/reporte/limpieza-semestral`);

        if (response.status === 204) {
            // No hay tickets del semestre anterior, nada que hacer
            return;
        }

        if (response.ok) {
            // Se generó el PDF y se limpiaron los tickets → descargar
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "reporte_semestral_limpieza.pdf";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            console.log("✅ Limpieza semestral completada. Reporte descargado.");
        }
    } catch (error) {
        console.error("Error en limpieza semestral:", error);
    }
}

// Ejecutar al cargar la página admin
document.addEventListener("DOMContentLoaded", () => {
    verificarLimpiezaSemestral();
});