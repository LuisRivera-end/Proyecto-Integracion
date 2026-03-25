export class NativeSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Record<string, Array<(...args: any[]) => void>> = {};
  public connected = false;

  constructor(public url: string) {
    this.connect();
  }

  /**
   * Conecta el WebSocket al servidor especificado en la URL.
   * Maneja los eventos de conexión, mensajes, errores y desconexión con reconexión automática.
   */
  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    console.log(`🔌 Conectando WebSocket a ${this.url}...`);
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('✅ WebSocket Conectado');
      this.connected = true;
      this.trigger('connect');
    };

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        console.log('📥 WS Recibido:', payload.type || 'no-type', payload);
        if (payload.type) {
          this.trigger(payload.type, payload);
        }
      } catch (e) {
        console.error("❌ Invalid WS JSON", e, event.data);
      }
    };

    this.ws.onclose = (event) => {
      if (this.connected) {
          console.warn('⚠️ WebSocket Cerrado', event.code, event.reason);
          this.trigger('disconnect');
      }
      this.connected = false;
      setTimeout(() => this.connect(), 3000); // auto-reconnect
    };
    
    this.ws.onerror = (e) => {
        console.error("🚫 WebSocket Error:", e);
    }
  }

  /**
   * Suscribe un listener a un evento específico del WebSocket.
   * 
   * @param {string} event - El nombre del evento a escuchar.
   * @param {(...args: any[]) => void} callback - La función que se ejecutará cuando ocurra el evento.
   */
  on(event: string, callback: (...args: any[]) => void) {
    if (!this.listeners[event]) this.listeners[event] = [];
    // Evitar duplicados exactos
    if (!this.listeners[event].includes(callback)) {
      this.listeners[event].push(callback);
    }
    
    if (event === 'connect' && this.connected && this.ws?.readyState === WebSocket.OPEN) {
      callback();
    }
  }

  /**
   * Elimina un listener de un evento específico del WebSocket.
   * Si no se proporciona callback, elimina todos los listeners del evento.
   * 
   * @param {string} event - El nombre del evento a dejar de escuchar.
   * @param {(...args: any[]) => void} [callback] - La función opcional a eliminar.
   */
  off(event: string, callback?: (...args: any[]) => void) {
    if (!callback) {
      this.listeners[event] = [];
    } else if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  /**
   * Emite un evento a través del WebSocket con los datos proporcionados.
   * 
   * @param {string} event - El nombre del evento a emitir.
   * @param {any} [data={}] - Los datos a enviar con el evento.
   */
  emit(event: string, data: any = {}) {
    if (this.ws && this.connected && this.ws.readyState === WebSocket.OPEN) {
      console.log('📤 WS Enviando:', event, data);
      this.ws.send(JSON.stringify({ type: event, data }));
    } else {
       console.warn(`⏳ WS no listo. Ignorando evento: ${event}`);
    }
  }

  /**
   * Desconecta el WebSocket y previene la reconexión automática.
   */
  disconnect() {
      if(this.ws) {
          this.ws.onclose = null; // Prevent reconnect
          this.ws.close();
      }
  }

  /**
   * Dispara un evento localmente llamando a todos los listeners suscritos.
   * 
   * @param {string} event - El nombre del evento a disparar.
   * @param {any} [data] - Los datos opcionales a pasar a los listeners.
   */
  private trigger(event: string, data?: any) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }
}

let socketInstance: NativeSocketClient | null = null;

/**
 * Proporciona una instancia única (Singleton) del cliente WebSocket.
 * 
 * @returns {NativeSocketClient} La instancia global del cliente WebSocket.
 */
export const useSocket = () => {
  if (socketInstance) return socketInstance;

  const { API_BASE_URL } = useConfig();
  const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + '/ws';
  
  socketInstance = new NativeSocketClient(wsUrl);
  return socketInstance;
}
