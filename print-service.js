const WebSocket = require('ws');
const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

/**
 * 🖨️ Print Service Client
 * 
 * Este servicio se conecta vía WebSockets al backend de UAL, recibe trabajos 
 * de impresión en formato base64 (PDF), los guarda temporalmente y los 
 * envía a la impresora local configurada.
 */

const platform = os.platform();
const IS_WINDOWS = platform === 'win32';
const IS_LINUX = platform === 'linux';

// Detectar si corre como .exe (pkg) o como script normal para resolver rutas
const appDir = process.pkg ? path.dirname(process.execPath) : __dirname;

// Buscar el archivo .env en la carpeta del ejecutable o nivel superior
const envPath = fs.existsSync(path.join(appDir, '.env')) 
    ? path.join(appDir, '.env') 
    : path.join(appDir, '..', '.env');

require('dotenv').config({ path: envPath });

const app = express();
const PORT = process.env.PRINT_SERVICE_PORT || 3001;
const SERVER_URL = process.env.PRINT_SERVER_URL;
const PRINTER_NAME = process.env.PRINTER_NAME;

// Mapear https:// -> wss:// y http:// -> ws:// y asegurar que termine en /ws
let wsUrl = SERVER_URL.replace(/^http/, 'ws');
if (!wsUrl.endsWith('/ws')) {
    wsUrl = wsUrl.replace(/\/?$/, '/ws');
}

console.log('🚀 Iniciando cliente de impresión (Native WebSocket)...');
console.log(`📂 Directorio: ${appDir}`);
console.log(`🌐 Servidor: ${wsUrl}`);
console.log(`🖨️ Impresora: ${PRINTER_NAME}`);

let ws;
let connected = false;

/**
 * Inicia la conexión WebSocket con el servidor y maneja la lógica de vida.
 */
function connect() {
    console.log(`🔌 Conectando WebSocket a ${wsUrl}...`);
    
    // rejectUnauthorized: false permite certificados auto-firmados en desarrollo
    ws = new WebSocket(wsUrl, {
        rejectUnauthorized: false
    });

    ws.on('open', () => {
        console.log('✅ WebSocket Conectado');
        connected = true;

        // Registro de la impresora ante el backend
        emit('register_printer', {
            printer_name: PRINTER_NAME,
            location: 'Recepcion',
            client_type: IS_WINDOWS ? 'windows_print_service' : 'linux_print_service'
        });
    });

    ws.on('message', (messageRaw) => {
        try {
            const payload = JSON.parse(messageRaw.toString());
            const type = payload.type;
            
            // Log de eventos recibidos
            console.log('📥 WS Recibido:', type, payload);

            if (type === 'registration_success') {
                console.log('🎉', payload.message);
            } else if (type === 'print_job') {
                console.log('🖨️ Trabajo recibido - Ticket:', payload.ticket_number);
                handlePrintJob(payload);
            }
        } catch (e) {
            console.error("❌ Invalid WS JSON", e, messageRaw.toString());
        }
    });

    ws.on('close', () => {
        console.warn('⚠️ WebSocket Cerrado. Intentando reconectar en 3s...');
        connected = false;
        setTimeout(connect, 3000);
    });

    ws.on('error', (err) => {
        console.error('🚫 WebSocket Error:', err.message);
    });
}

/**
 * Envía un evento serializado al servidor siguiendo el protocolo {type, data}.
 * @param {string} type - Nombre del evento.
 * @param {object} data - Payload del evento.
 */
function emit(type, data = {}) {
    if (ws && connected && ws.readyState === WebSocket.OPEN) {
        console.log('📤 WS Enviando:', type, data);
        ws.send(JSON.stringify({ type, data }));
    } else {
        console.warn(`⏳ WS no listo. Ignorando evento: ${type}`);
    }
}

/**
 * Construye el comando de sistema para imprimir un PDF dependiendo del SO.
 * @param {string} pdfPath - Ruta absoluta al archivo PDF.
 * @returns {string} Comando para ejecutar vía exec.
 */
function buildPrintCommand(pdfPath) {
    if (IS_WINDOWS) {
        // En Windows se usa SumatraPDF (debe estar la ruta en el .env)
        const SUMATRA_PATH = `"${process.env.SUMATRA_PATH}"`;
        return `${SUMATRA_PATH} -print-to "${PRINTER_NAME}" "${pdfPath}"`;
    } else if (IS_LINUX) {
        // En Linux usamos el sistema de impresión CUPS (lp)
        return `lp -d "${PRINTER_NAME}" "${pdfPath}"`;
    } else {
        throw new Error(`Plataforma ${platform} no soportada`);
    }
}

/**
 * Maneja la recepción de un trabajo de impresión:
 * 1. Decodifica el Base64 a un archivo temporal.
 * 2. Ejecuta el comando de impresión del SO.
 * 3. Notifica éxito/error al backend.
 * 4. Elimina el archivo temporal.
 * 
 * @param {object} data - Datos del ticket incluyendo ticket_number y pdf_content.
 */
function handlePrintJob(data) {
    try {
        // Sanitización básica del número de ticket
        if (!/^[a-zA-Z0-9_\-]+$/.test(String(data.ticket_number))) {
            throw new Error(`El número de ticket es inválido.`);
        }

        const tempDir = path.join(os.tmpdir(), "print-service");
        if (!fs.existsSync(tempDir)) {
            fs.mkdirSync(tempDir, { recursive: true });
        }

        const pdfPath = path.join(tempDir, `ticket_${data.ticket_number}.pdf`);
        fs.writeFileSync(pdfPath, Buffer.from(data.pdf_content, "base64"));

        const command = buildPrintCommand(pdfPath);
        console.log('🖨️ Ejecutando:', command);

        exec(command, (error) => {
            if (error) {
                console.error('❌ Error imprimiendo:', error.message);
                emit('print_failed', {
                    ticket_number: data.ticket_number,
                    error: error.message
                });
                return;
            }

            console.log('✅ Impresión exitosa:', data.ticket_number);
            emit('print_completed', {
                ticket_number: data.ticket_number
            });

            // Limpieza del archivo temporal tras 5 segundos
            setTimeout(() => {
                try {
                    fs.unlinkSync(pdfPath);
                    console.log('🧹 Archivo temporal eliminado');
                } catch(e) { /* ignore */ }
            }, 5000);
        });

    } catch (error) {
        console.error('❌ Error procesando trabajo:', error);
        emit('print_failed', {
            ticket_number: data.ticket_number,
            error: error.message
        });
    }
}

// Iniciar ciclo de conexión
connect();

/**
 * Endpoint de Health Check Local
 * Permite monitorear el estado del servicio externamente.
 */
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        connected: connected && ws.readyState === WebSocket.OPEN, 
        printer: PRINTER_NAME, 
        base_url: SERVER_URL,
        ws_url: wsUrl
    });
});

app.listen(PORT, () => console.log(`🎯 Cliente listo en http://localhost:${PORT}/health`));
