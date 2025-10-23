const { io } = require('socket.io-client');
const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3001;

// Apunta al proxy HTTPS de Docker/Nginx
const SERVER_URL = 'https://host.docker.internal:4443'; 

const SUMATRA_PATH = '"C:\\Users\\lelie\\AppData\\Local\\SumatraPDF\\SumatraPDF.exe"';
const PRINTER_NAME = 'POS-58';

console.log('🚀 Iniciando cliente de impresión...');

const socket = io(SERVER_URL, {
    transports: ['websocket', 'polling'],
    secure: true,
    reconnection: true,
    reconnectionAttempts: 20,
    reconnectionDelay: 2000,
    timeout: 10000,
});

// Conexión al servidor
socket.on('connect', () => {
    console.log('✅ Conectado al servidor WebSocket');
    console.log('📡 Socket ID:', socket.id);

    socket.emit('register_printer', {
        printer_name: PRINTER_NAME,
        location: 'Recepcion',
        client_type: 'windows_print_service'
    });
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

// Función de impresión
function handlePrintJob(data) {
    try {
        const tempDir = "C:\\temp\\prints";
        if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });

        const pdfPath = path.join(tempDir, `ticket_${data.ticket_number}.pdf`);
        fs.writeFileSync(pdfPath, Buffer.from(data.pdf_content, "base64"));

        const command = `${SUMATRA_PATH} -print-to "${PRINTER_NAME}" "${pdfPath}"`;
        console.log('🖨️ Ejecutando:', command);

        exec(command, (error) => {
            if (error) {
                console.error('❌ Error imprimiendo:', error.message);
                socket.emit('print_failed', { ticket_number: data.ticket_number, error: error.message });
            } else {
                console.log('✅ Impresión exitosa:', data.ticket_number);
                socket.emit('print_completed', { ticket_number: data.ticket_number });

                setTimeout(() => {
                    try { fs.unlinkSync(pdfPath); console.log('🧹 Archivo eliminado'); } 
                    catch(e){ console.log('⚠️ No se pudo eliminar archivo:', e.message); }
                }, 5000);
            }
        });

    } catch (error) {
        console.error('❌ Error procesando trabajo:', error);
        socket.emit('print_failed', { ticket_number: data.ticket_number, error: error.message });
    }
}

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', connected: socket.connected, printer: PRINTER_NAME, server_url: SERVER_URL });
});

app.listen(PORT, () => console.log(`🎯 Cliente listo en http://localhost:${PORT}/health`));
