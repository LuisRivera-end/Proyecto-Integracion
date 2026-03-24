const { io } = require('socket.io-client');
const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const os = require('os');
const platform = os.platform();

const IS_WINDOWS = platform === 'win32';
const IS_LINUX = platform === 'linux';

// Detectar si corre como .exe (pkg) o como script normal
const appDir = process.pkg ? path.dirname(process.execPath) : __dirname;

// Buscar el archivo .env en la carpeta actual, o en un nivel superior (útil si el .exe está en /dist)
const envPath = fs.existsSync(path.join(appDir, '.env')) 
    ? path.join(appDir, '.env') 
    : path.join(appDir, '..', '.env');

require('dotenv').config({ path: envPath });

const app = express();
const PORT = process.env.PRINT_SERVICE_PORT;

const SERVER_URL = process.env.PRINT_SERVER_URL;
const SUMATRA_PATH = `"${process.env.SUMATRA_PATH}"`;
const PRINTER_NAME = process.env.PRINTER_NAME;

console.log('🚀 Iniciando cliente de impresión...');
console.log(`📂 Directorio: ${appDir}`);
console.log(`🌐 Servidor: ${SERVER_URL}`);
console.log(`🖨️ Impresora: ${PRINTER_NAME}`);

const socket = io(SERVER_URL, {
    transports: ['websocket', 'polling'],
    secure: true,
    reconnection: true,
    reconnectionAttempts: 20,
    reconnectionDelay: 2000,
    timeout: 10000,
    rejectUnauthorized: false,
});

// Conexión al servidor
socket.on('connect', () => {
    console.log('✅ Conectado al servidor WebSocket');
    console.log('📡 Socket ID:', socket.id);

    socket.emit('register_printer', {
        printer_name: PRINTER_NAME,
        location: 'Recepcion',
        client_type: IS_WINDOWS ? 'windows_print_service' : 'linux_print_service'
    });
});

socket.on('connection_ack', (data) => {
    console.log('🔗 Conexión establecida con el servidor:', data);
});


// Registro exitoso
socket.on('registration_success', (data) => {
    console.log('🎉', data.message);
});

// Escuchar trabajos de impresión
socket.on('print_job', (data) => {
    console.log('🖨️ Trabajo recibido - Ticket:', data.ticket_number);
    handlePrintJob(data);
});

function buildPrintCommand(pdfPath) {
    if (IS_WINDOWS) {
        return `${SUMATRA_PATH} -print-to "${PRINTER_NAME}" "${pdfPath}"`;
    } else if (IS_LINUX) {
        return `lp -d "${PRINTER_NAME}" "${pdfPath}"`;
    } else {
        throw new Error(`Plataforma ${platform} no soportada`);
    }
}

// Función de impresión (Windows / Linux)
function handlePrintJob(data) {
    try {

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

                socket.emit('print_failed', {
                    ticket_number: data.ticket_number,
                    error: error.message
                });

                return;
            }

            console.log('✅ Impresión exitosa:', data.ticket_number);

            socket.emit('print_completed', {
                ticket_number: data.ticket_number
            });

            setTimeout(() => {

                try {
                    fs.unlinkSync(pdfPath);
                    console.log('🧹 Archivo eliminado');
                } catch(e) {
                    console.log('⚠️ No se pudo eliminar archivo:', e.message);
                }

            }, 5000);

        });

    } catch (error) {

        console.error('❌ Error procesando trabajo:', error);

        socket.emit('print_failed', {
            ticket_number: data.ticket_number,
            error: error.message
        });

    }
}

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', connected: socket.connected, printer: PRINTER_NAME, server_url: SERVER_URL });
});

app.listen(PORT, () => console.log(`🎯 Cliente listo en http://localhost:${PORT}/health`));
