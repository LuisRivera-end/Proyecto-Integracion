import Toastify from 'toastify-js'

const BACKGROUNDS = {
  success: 'linear-gradient(to right, #00b09b, #96c93d)',
  error: 'linear-gradient(to right, #ff5f6d, #ffc371)',
  info: 'linear-gradient(to right, #2193b0, #6dd5ed)',
  warning: 'linear-gradient(to right, #f7dc6f, #f1c40f)',
}

export const useToast = () => {
  const lanzarAlerta = (mensaje: string, tipo: 'success' | 'error' | 'info' | 'warning' = 'success') => {
    Toastify({
      text: mensaje,
      duration: 3000,
      gravity: 'top',
      position: 'right',
      stopOnFocus: true,
      style: {
        background: BACKGROUNDS[tipo] || BACKGROUNDS.success,
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      },
    }).showToast()
  }

  return { lanzarAlerta }
}
