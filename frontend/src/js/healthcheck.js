import Config from './config.js';

const API_BASE_URL = Config.API_BASE_URL;

/**
 * Espera a que el backend esté disponible haciendo polling a /api/sectores.
 * Cuando responde, oculta el overlay de loading con una animación suave.
 * @param {number} intervalMs - Intervalo entre reintentos (default 2000ms)
 * @returns {Promise<void>} Se resuelve cuando el backend está listo
 */
export function waitForBackend(intervalMs = 2000) {
  return new Promise((resolve) => {
    const overlay = document.getElementById('loading-overlay');

    async function check() {
      try {
        const res = await fetch(`${API_BASE_URL}/api/sectores`, {
          method: 'GET',
          signal: AbortSignal.timeout(5000),
        });
        if (res.ok) {
          hideOverlay(overlay);
          resolve();
          return;
        }
      } catch (_) {
        // Backend no disponible, reintentar
      }
      setTimeout(check, intervalMs);
    }

    check();
  });
}

/**
 * Oculta el overlay con una transición de fade-out y luego lo elimina del DOM.
 */
function hideOverlay(overlay) {
  if (!overlay) return;
  overlay.style.opacity = '0';
  overlay.addEventListener('transitionend', () => {
    overlay.remove();
  });
}
