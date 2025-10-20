// print-service.js - Servicio de impresión en Windows
const express = require('express');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const app = express();
const PORT = 3001;

app.use(express.json({ limit: '10mb' }));

const sumatraPath = `"C:\\Users\\lelie\\AppData\\Local\\SumatraPDF\\SumatraPDF.exe"`; 

// Endpoint para imprimir PDF
app.post("/print", (req, res) => {
    const { pdfContent, printerName, ticketName } = req.body;

    // Guardar PDF temporalmente
    const tempDir = "C:\\temp\\prints";
    if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });

    const pdfPath = path.join(tempDir, `${ticketName}.pdf`);
    fs.writeFileSync(pdfPath, Buffer.from(pdfContent, "base64"));

    console.log("📄 PDF guardado en:", pdfPath);

    // Ejecutar impresión usando SumatraPDF
    exec(`${sumatraPath} -print-to "${printerName}" "${pdfPath}"`, (error, stdout, stderr) => {
        if (error) {
            console.error("❌ Error imprimiendo:", error);
            res.status(500).json({ success: false, message: "Error imprimiendo", error: error.message });
        } else {
            console.log("✅ Impreso correctamente");
            res.json({ success: true, message: "Impresión enviada correctamente" });
        }
    });
});

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'Windows Print Service' });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🖨️ Servicio de impresión corriendo en http://localhost:${PORT}`);
    console.log('📍 Listo para recibir trabajos de Docker...');
});