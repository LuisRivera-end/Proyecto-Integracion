import Config from './config.js';
const API_BASE_URL = Config.API_BASE_URL;

// Paleta de colores para sectores conocidos
const SECTOR_COLORS = {
    'cajas':                { border: 'border-green-500', bg: 'bg-green-50', icon: 'bg-green-500', text: 'text-green-700' },
    'servicios escolares':  { border: 'border-blue-500',  bg: 'bg-blue-50',  icon: 'bg-blue-500',  text: 'text-blue-700'  },
    'becas':                { border: 'border-amber-500', bg: 'bg-amber-50', icon: 'bg-amber-500', text: 'text-amber-700' },
    'tesoreria':            { border: 'border-red-500',   bg: 'bg-red-50',   icon: 'bg-red-500',   text: 'text-red-700'   },
};

// Colores genéricos para sectores nuevos
const GENERIC_COLORS = [
    { border: 'border-purple-500', bg: 'bg-purple-50', icon: 'bg-purple-500', text: 'text-purple-700' },
    { border: 'border-cyan-500',   bg: 'bg-cyan-50',   icon: 'bg-cyan-500',   text: 'text-cyan-700'   },
    { border: 'border-pink-500',   bg: 'bg-pink-50',   icon: 'bg-pink-500',   text: 'text-pink-700'   },
    { border: 'border-teal-500',   bg: 'bg-teal-50',   icon: 'bg-teal-500',   text: 'text-teal-700'   },
];

function getColorsForSector(sectorName) {
    const key = sectorName.toLowerCase();
    if (SECTOR_COLORS[key]) return SECTOR_COLORS[key];

    // Asignar color genérico basado en hash del nombre
    let hash = 0;
    for (let i = 0; i < key.length; i++) hash = key.charCodeAt(i) + ((hash << 5) - hash);
    return GENERIC_COLORS[Math.abs(hash) % GENERIC_COLORS.length];
}

function renderBadges(data) {
    const container = document.getElementById('sector-badges');
    if (!container) return;

    const entries = Object.entries(data);
    if (entries.length === 0) {
        container.innerHTML = '<p class="text-slate-400 text-sm text-center col-span-2 py-4">Sin sectores</p>';
        return;
    }

    container.innerHTML = entries.map(([sector, count]) => {
        const c = getColorsForSector(sector);
        return `
            <div class="flex flex-col gap-1">
                <span class="text-slate-500 text-xs font-bold uppercase tracking-wider truncate">${sector}</span>
                <div class="flex items-center justify-center gap-3 border-2 ${c.border} ${c.bg} rounded-2xl px-3 py-4 hover:-translate-y-0.5 transition-transform">
                    <span class="inline-flex p-2 ${c.icon} rounded-xl text-white">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                        </svg>
                    </span>
                    <span class="text-4xl font-black ${c.text}">${count || 0}</span>
                </div>
            </div>
        `;
    }).join('');
}

async function actualizarConteos() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/tickets_count`);
        if (!response.ok) throw new Error("Error al obtener los datos");
        const data = await response.json();
        renderBadges(data);
    } catch (err) {
        console.error("Error al actualizar conteos:", err);
    }
}

// 1. Carga inicial al abrir la página
document.addEventListener("DOMContentLoaded", () => {
    actualizarConteos();

    const socket = io(API_BASE_URL);

    socket.on('connect', () => {
        console.log('🔗 Conteos conectados al WebSocket');
    });

    socket.on('tickets_updated', () => {
        console.log('📊 Actualizando conteos por cambio en tickets...');
        actualizarConteos();
    });

    socket.on('disconnect', () => {
        console.log('⚠️ WebSocket de conteos desconectado');
    });
});