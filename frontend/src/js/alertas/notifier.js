// Toastify is loaded as a global script in the HTML file
/* global Toastify */

export function lanzarAlerta(mensaje, tipo = "success") {
    let fondo;

    // Definimos los colores según el tipo
    switch (tipo) {
        case "error":
            fondo = "linear-gradient(to right, #ff5f6d, #ffc371)"; // Rojo/Naranja
            break;
        case "info":
            fondo = "linear-gradient(to right, #2193b0, #6dd5ed)"; // Azul
            break;
        case "success":
            fondo = "linear-gradient(to right, #00b09b, #96c93d)"; // Verde
            break;
        case "warning":
            fondo = "linear-gradient(to right, #f7dc6f, #f1c40f)"; // Amarillo
            break;
        default:
            fondo = "linear-gradient(to right, #00b09b, #96c93d)"; // Verde
            break;
    }

    Toastify({
        text: mensaje,
        duration: 3000,
        gravity: "top",
        position: "right",
        stopOnFocus: true, // Se detiene el tiempo si el usuario pone el mouse encima
        style: {
            background: fondo,
            borderRadius: "8px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
        }
    }).showToast();
}