# app/websocket/print_handlers.py
from flask_socketio import emit
from flask import request

# Diccionario para trackear clientes conectados
connected_clients = {}

def register_socket_handlers(socketio):
    """Registrar todos los handlers de WebSocket"""
    
    @socketio.on('connect')
    def handle_connect():
        print(f'✅ Cliente WebSocket conectado: {request.sid}')
        emit('connection_ack', {'status': 'connected', 'sid': request.sid})

    @socketio.on('register_printer')
    def handle_register_printer(data):
        """El cliente se registra como disponible para imprimir"""
        client_id = request.sid
        printer_name = data.get('printer_name', 'POS-58')
        location = data.get('location', 'Recepcion')
        
        connected_clients[client_id] = {
            'printer_name': printer_name,
            'location': location,
            'status': 'available'
        }
        
        print(f'🖨️ Cliente registrado: {printer_name} en {location} (ID: {client_id})')
        emit('registration_success', {
            'message': f'Registrado como {printer_name}',
            'client_id': client_id
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        client_id = request.sid
        if client_id in connected_clients:
            printer_name = connected_clients[client_id]['printer_name']
            del connected_clients[client_id]
            print(f'❌ Cliente desconectado: {printer_name} (ID: {client_id})')
        else:
            print(f'❌ Cliente desconectado: {client_id}')

    @socketio.on('print_completed')
    def handle_print_completed(data):
        """El cliente notifica que completó la impresión"""
        client_id = request.sid
        if client_id in connected_clients:
            connected_clients[client_id]['status'] = 'available'
        
        print(f'✅ Impresión completada: {data.get("ticket_number")}')
        emit('print_success', {
            'ticket_number': data.get('ticket_number'),
            'client_id': client_id
        }, broadcast=True)

    @socketio.on('print_failed')
    def handle_print_failed(data):
        """El cliente notifica que falló la impresión"""
        client_id = request.sid
        if client_id in connected_clients:
            connected_clients[client_id]['status'] = 'available'
        
        print(f'❌ Impresión fallida: {data.get("error")}')
        emit('print_error', {
            'error': data.get('error'),
            'ticket_number': data.get('ticket_number')
        })

    # Función para obtener clientes disponibles
    def get_available_client():
        for client_id, client_data in connected_clients.items():
            if client_data['status'] == 'available':
                return client_id
        return None

    # Función para enviar trabajo de impresión
    def send_print_job(pdf_content, ticket_number, sector):
        client_id = get_available_client()
        if not client_id:
            return False, 'No hay impresoras disponibles'
        
        # Enviar trabajo al cliente
        socketio.emit('print_job', {
            'pdf_content': pdf_content,
            'ticket_number': ticket_number,
            'sector': sector,
            'job_id': f"job_{ticket_number}"
        }, room=client_id)
        
        # Marcar como ocupado
        connected_clients[client_id]['status'] = 'printing'
        
        return True, f'Ticket enviado a {connected_clients[client_id]["printer_name"]}'

    # Exportar la función para usar en otras partes
    return send_print_job