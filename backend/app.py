# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from datetime import datetime
import random
import string

app = Flask(__name__)
CORS(app)

@app.route('/v1/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mariadb"),
        user=os.getenv("DB_USER", "turnoadmin"),
        password=os.getenv("DB_PASSWORD", "13Demayo!"),
        database=os.getenv("DB_NAME", "TurnosUal")
    )

def generar_folio_unico(cursor):
    estados_activos = (1, 3)  # ID_Estados: 1 = Pendiente, 3 = Activo/Atendiendo
    while True:
        folio = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        cursor.execute("""
            SELECT 1 FROM Turno 
            WHERE Folio = %s AND ID_Estados IN (%s, %s)
        """, (folio, *estados_activos))
        if not cursor.fetchone():
            return folio

@app.route('/api/ticket', methods=['POST'])
def generar_ticket():
    data = request.get_json()
    matricula = data.get('matricula')
    sector = data.get('sector')

    if not matricula or not sector:
        return jsonify({"error": "matrícula y sector son requeridos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Buscar ID_Alumno a partir de la matrícula
    cursor.execute("SELECT ID_Alumno, nombre1, Apellido1 FROM Alumnos WHERE Matricula = %s", (matricula,))
    alumno = cursor.fetchone()

    if not alumno:
        return jsonify({"error": "No se encontró alumno con esa matrícula"}), 404

    ID_Alumno = alumno["ID_Alumno"]
    
    # 3️⃣ Generar folio aleatorio
    Folio = generar_folio_unico(cursor)
    Fecha_Ticket = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 4️⃣ Insertar el turno con estado "Pendiente" (ID_Estado = 1)
    cursor.execute("""
        INSERT INTO Turno (ID_Alumno, ID_Ventanilla, Fecha_Ticket, Folio, ID_Estados)
        VALUES (%s, NULL, %s, %s, 1)
    """, (ID_Alumno, Fecha_Ticket, Folio))

    conn.commit()

    # 5️⃣ Responder al frontend
    return jsonify({
        "mensaje": "Ticket generado exitosamente",
        "folio": Folio,
        "fecha": Fecha_Ticket,
        "alumno": matricula,
        "sector": sector
    }), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)