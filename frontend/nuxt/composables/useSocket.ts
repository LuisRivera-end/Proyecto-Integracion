export class NativeSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Record<string, Array<(...args: any[]) => void>> = {};
  public connected = false;

  constructor(public url: string) {
    this.connect();
  }

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

  off(event: string, callback?: (...args: any[]) => void) {
    if (!callback) {
      this.listeners[event] = [];
    } else if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  emit(event: string, data: any = {}) {
    if (this.ws && this.connected && this.ws.readyState === WebSocket.OPEN) {
      console.log('📤 WS Enviando:', event, data);
      this.ws.send(JSON.stringify({ type: event, data }));
    } else {
       console.warn(`⏳ WS no listo. Posponiendo o ignorando evento: ${event}`);
       // Opcional: Reintento único tras conectar
       if (event === 'ventanilla_register') {
          this.on('connect', () => this.emit(event, data));
       }
    }
  }

  disconnect() {
      if(this.ws) {
          this.ws.onclose = null; // Prevent reconnect
          this.ws.close();
      }
  }

  private trigger(event: string, data?: any) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }
}

let socketInstance: NativeSocketClient | null = null;

export const useSocket = () => {
  if (socketInstance) return socketInstance;

  const { API_BASE_URL } = useConfig();
  const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + '/ws';
  
  socketInstance = new NativeSocketClient(wsUrl);
  return socketInstance;
}
