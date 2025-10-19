// qz-config.js - Solo configuración SSL y conexión
class QZConnectionManager {
    constructor() {
        this.isConnected = false;
        this.connectionPromise = null;
    }

    async connect() {
        // Si ya estamos conectados, retornar
        if (this.isConnected) return true;
        
        // Si hay una conexión en proceso, esperarla
        if (this.connectionPromise) {
            return await this.connectionPromise;
        }

        this.connectionPromise = this._connectInternal();
        return await this.connectionPromise;
    }

    async _connectInternal() {
        try {
            console.log('🔐 Configurando SSL para QZ Tray...');

            // Configuración de seguridad para desarrollo con SSL
            qz.security.setCertificatePromise((resolve, reject) => {
                console.log('📄 Configurando certificado SSL...');
                // Para SSL, podemos resolver sin certificado específico
                // QZ Tray usará el certificado del servidor
                resolve();
            });

            qz.security.setSignaturePromise((toSign) => {
                return (resolve, reject) => {
                    console.log('🔏 Generando firma SSL...');
                    // Firma simple para SSL
                    resolve("ssl-signature-" + Math.random().toString(36));
                };
            });

            // Configuración de conexión SSL
            const config = {
                host: 'localhost',
                port: 4443,
                protocol: 'wss', // WebSocket Secure
                bypassSSLCheck: true, // IMPORTANTE: Permitir certificado autofirmado
                timeout: 15000,
                retries: 2
            };

            console.log('🔄 Conectando a QZ Tray via SSL...', config);
            await qz.websocket.connect(config);
            
            this.isConnected = true;
            console.log('✅ QZ Tray conectado via SSL');
            return true;

        } catch (error) {
            console.error('❌ Error en conexión SSL:', error);
            this.isConnected = false;
            this.connectionPromise = null;
            throw error;
        }
    }

    disconnect() {
        if (this.isConnected) {
            qz.websocket.disconnect();
            this.isConnected = false;
            this.connectionPromise = null;
            console.log('🔌 QZ Tray desconectado');
        }
    }

    getStatus() {
        return {
            connected: this.isConnected,
            ssl: true
        };
    }
}

// Instancia global
const qzConnection = new QZConnectionManager();

// Inicializar automáticamente al cargar
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando conexión QZ Tray SSL...');
    // Conectar en background, pero no bloquear si falla
    qzConnection.connect().catch(error => {
        console.warn('⚠️ QZ Tray no disponible, se usará PDF como fallback');
    });
});

// Exportar funciones globales
window.ensureQZConnected = async function() {
    return await qzConnection.connect();
};

window.getQZConnectionStatus = function() {
    return qzConnection.getStatus();
};