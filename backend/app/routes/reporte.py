from flask import Blueprint, send_file, request, jsonify
from app.models.database import get_db_connection
from fpdf import FPDF
from datetime import datetime, timedelta, date
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import tempfile
import pytz

bp = Blueprint('reporte', __name__, url_prefix='/api')

DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
COLORES_CHART = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4']

# ─── Utilidades de semestre ───

def obtener_semestre(fecha):
    """Retorna (inicio, fin) del semestre al que pertenece la fecha."""
    if fecha.month <= 6:
        return date(fecha.year, 1, 1), date(fecha.year, 6, 30)
    else:
        return date(fecha.year, 7, 1), date(fecha.year, 12, 31)

def obtener_semestre_anterior(fecha):
    """Retorna (inicio, fin) del semestre anterior al actual."""
    if fecha.month <= 6:
        return date(fecha.year - 1, 7, 1), date(fecha.year - 1, 12, 31)
    else:
        return date(fecha.year, 1, 1), date(fecha.year, 6, 30)

def validar_rango_semestral(desde, hasta):
    """Valida que ambas fechas estén dentro del mismo semestre."""
    sem_desde = obtener_semestre(desde)
    sem_hasta = obtener_semestre(hasta)
    if sem_desde != sem_hasta:
        return False, "El rango de fechas no puede cruzar entre semestres (Ene-Jun / Jul-Dic)"
    if desde > hasta:
        return False, "La fecha de inicio no puede ser posterior a la fecha fin"
    return True, None

# ─── Generadores de gráficos ───

def _generar_grafico_barras(datos, titulo, xlabel, ylabel, filename, color='#10b981'):
    """Genera un gráfico de barras y lo guarda como imagen."""
    fig, ax = plt.subplots(figsize=(7, 3.5))
    
    etiquetas = list(datos.keys())
    valores = list(datos.values())
    
    bars = ax.bar(etiquetas, valores, color=color, edgecolor='white', linewidth=0.5, width=0.6)
    
    for bar, val in zip(bars, valores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(val), ha='center', va='bottom', fontsize=9, fontweight='bold', color='#334155')
    
    ax.set_title(titulo, fontsize=12, fontweight='bold', color='#1e293b', pad=12)
    ax.set_xlabel(xlabel, fontsize=9, color='#64748b')
    ax.set_ylabel(ylabel, fontsize=9, color='#64748b')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#e2e8f0')
    ax.spines['bottom'].set_color('#e2e8f0')
    ax.tick_params(colors='#64748b', labelsize=8)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color='#f1f5f9', linewidth=0.8)
    
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def _generar_grafico_pastel(datos, titulo, filename):
    """Genera un gráfico de pastel y lo guarda como imagen."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    
    etiquetas = list(datos.keys())
    valores = list(datos.values())
    colores = COLORES_CHART[:len(etiquetas)]
    
    wedges, texts, autotexts = ax.pie(
        valores, labels=etiquetas, autopct='%1.1f%%',
        colors=colores, startangle=90, pctdistance=0.75,
        textprops={'fontsize': 9, 'color': '#334155'}
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_fontweight('bold')
    
    ax.set_title(titulo, fontsize=12, fontweight='bold', color='#1e293b', pad=12)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)


# ─── Clase PDF ───

class ReportePDF(FPDF):
    def __init__(self, fecha_inicio, fecha_fin, titulo="Reporte de Tickets"):
        super().__init__('P', 'mm', 'Letter')
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.titulo_reporte = titulo
    
    def header(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "..", "..", "ual.png")
        try:
            self.image(image_path, x=15, y=10, w=30)
        except Exception:
            pass
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, self.titulo_reporte, ln=True, align="C")
        self.set_font("Arial", "", 10)
        self.set_text_color(100, 116, 139)
        self.cell(0, 6, f"{self.fecha_inicio} - {self.fecha_fin}", ln=True, align="C")
        self.set_text_color(0, 0, 0)
        self.ln(5)
        self.set_draw_color(226, 232, 240)
        self.line(15, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Pagina {self.page_no()} | Generado el {datetime.now(pytz.timezone('America/Mexico_City')).strftime('%d/%m/%Y %H:%M')}", 0, 0, "C")


# ─── Función compartida para generar PDF ───

def _construir_reporte_pdf(fecha_inicio_str, fecha_fin_str, titulo="Reporte de Tickets"):
    """Genera el PDF completo y retorna la ruta del archivo temporal."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 1. Resumen general
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN ID_Estados = 4 THEN 1 ELSE 0 END) as completados,
                SUM(CASE WHEN ID_Estados = 2 THEN 1 ELSE 0 END) as cancelados,
                SUM(CASE WHEN ID_Estados = 1 THEN 1 ELSE 0 END) as pendientes,
                SUM(CASE WHEN ID_Estados = 3 THEN 1 ELSE 0 END) as atendiendo
            FROM Turno
            WHERE DATE(Fecha_Ticket) BETWEEN %s AND %s
        """, (fecha_inicio_str, fecha_fin_str))
        resumen = cursor.fetchone()
        
        # 2. Tickets por fecha
        cursor.execute("""
            SELECT DATE(Fecha_Ticket) as fecha, COUNT(*) as cantidad
            FROM Turno
            WHERE DATE(Fecha_Ticket) BETWEEN %s AND %s
            GROUP BY DATE(Fecha_Ticket)
            ORDER BY fecha
        """, (fecha_inicio_str, fecha_fin_str))
        por_fecha_raw = cursor.fetchall()
        
        # Crear lookup de fecha → cantidad
        fecha_cantidades = {}
        for row in por_fecha_raw:
            f = row['fecha']
            if hasattr(f, 'strftime'):
                fecha_cantidades[f] = row['cantidad']
            else:
                fecha_cantidades[datetime.strptime(str(f), '%Y-%m-%d').date()] = row['cantidad']
        
        desde_dt_temp = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        hasta_dt_temp = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        total_dias = (hasta_dt_temp - desde_dt_temp).days + 1
        
        dia_nombres = {1: 'Lun', 2: 'Mar', 3: 'Mié', 4: 'Jue', 5: 'Vie', 6: 'Sáb', 7: 'Dom'}
        meses_nombres = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                         7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        
        if total_dias <= 14:
            # DIARIO: "24/02 (Lun)"
            chart_datos = {}
            current = desde_dt_temp
            while current <= hasta_dt_temp:
                label = f"{current.strftime('%d/%m')} ({dia_nombres[current.isoweekday()]})"
                chart_datos[label] = fecha_cantidades.get(current, 0)
                current += timedelta(days=1)
            chart_titulo = 'Tickets por Fecha'
            chart_xlabel = 'Fecha'
        elif total_dias <= 90:
            # SEMANAL: "Sem 03/02"
            from collections import OrderedDict
            chart_datos = OrderedDict()
            current = desde_dt_temp
            while current <= hasta_dt_temp:
                # Inicio de la semana (lunes)
                week_start = current - timedelta(days=current.weekday())
                if week_start < desde_dt_temp:
                    week_start = desde_dt_temp
                label = f"Sem {week_start.strftime('%d/%m')}"
                if label not in chart_datos:
                    chart_datos[label] = 0
                chart_datos[label] += fecha_cantidades.get(current, 0)
                current += timedelta(days=1)
            chart_titulo = 'Tickets por Semana'
            chart_xlabel = 'Semana'
        else:
            # MENSUAL: "Febrero 2026"
            from collections import OrderedDict
            chart_datos = OrderedDict()
            current = desde_dt_temp
            while current <= hasta_dt_temp:
                label = f"{meses_nombres[current.month]} {current.year}"
                if label not in chart_datos:
                    chart_datos[label] = 0
                chart_datos[label] += fecha_cantidades.get(current, 0)
                current += timedelta(days=1)
            chart_titulo = 'Tickets por Mes'
            chart_xlabel = 'Mes'
        
        # 3. Tickets por ventanilla (completados)
        cursor.execute("""
            SELECT v.Ventanilla as nombre, COUNT(*) as cantidad
            FROM Turno t
            JOIN Ventanillas v ON t.ID_Ventanilla = v.ID_Ventanilla
            WHERE DATE(t.Fecha_Ticket) BETWEEN %s AND %s
              AND t.ID_Estados = 4
            GROUP BY v.Ventanilla
            ORDER BY cantidad DESC
        """, (fecha_inicio_str, fecha_fin_str))
        por_ventanilla = {row['nombre']: row['cantidad'] for row in cursor.fetchall()}
        
        # 4. Tickets por sector
        cursor.execute("""
            SELECT s.Sector as nombre, COUNT(*) as cantidad
            FROM Turno t
            JOIN Sectores s ON t.ID_Sector = s.ID_Sector
            WHERE DATE(t.Fecha_Ticket) BETWEEN %s AND %s
            GROUP BY s.Sector
            ORDER BY cantidad DESC
        """, (fecha_inicio_str, fecha_fin_str))
        por_sector = {row['nombre']: row['cantidad'] for row in cursor.fetchall()}
        
        # 5. Día con más tickets
        cursor.execute("""
            SELECT DATE(Fecha_Ticket) as fecha, COUNT(*) as cantidad
            FROM Turno
            WHERE DATE(Fecha_Ticket) BETWEEN %s AND %s
            GROUP BY DATE(Fecha_Ticket)
            ORDER BY cantidad DESC
            LIMIT 1
        """, (fecha_inicio_str, fecha_fin_str))
        dia_pico = cursor.fetchone()
        
        # --- Generar gráficos ---
        chart_dias = os.path.join(tmpdir, 'chart_dias.png')
        _generar_grafico_barras(chart_datos, chart_titulo, chart_xlabel, 'Cantidad', chart_dias, '#10b981')
        
        chart_ventanillas = os.path.join(tmpdir, 'chart_ventanillas.png')
        if por_ventanilla:
            _generar_grafico_barras(por_ventanilla, 'Tickets Atendidos por Ventanilla', 'Ventanilla', 'Completados', chart_ventanillas, '#3b82f6')
        
        chart_sectores = os.path.join(tmpdir, 'chart_sectores.png')
        if por_sector:
            _generar_grafico_pastel(por_sector, 'Distribucion por Sector', chart_sectores)
        
        # --- Construir PDF ---
        desde_dt = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
        hasta_dt = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
        fecha_i_fmt = desde_dt.strftime('%d/%m/%Y')
        fecha_f_fmt = hasta_dt.strftime('%d/%m/%Y')
        
        pdf = ReportePDF(fecha_i_fmt, fecha_f_fmt, titulo)
        pdf.add_page()
        
        # Resumen general
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Resumen General", ln=True)
        pdf.ln(3)
        
        total = resumen['total'] or 0
        completados = resumen['completados'] or 0
        cancelados = resumen['cancelados'] or 0
        pendientes = resumen['pendientes'] or 0
        atendiendo = resumen['atendiendo'] or 0
        
        col_w = 43
        pdf.set_font("Arial", "B", 10)
        
        metricas = [
            ("Total", str(total), (30, 41, 59)),
            ("Completados", str(completados), (16, 185, 129)),
            ("Cancelados", str(cancelados), (239, 68, 68)),
            ("Pendientes", str(pendientes), (245, 158, 11)),
        ]
        
        for etiqueta, valor, color in metricas:
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.set_fill_color(248, 250, 252)
            pdf.rect(x, y, col_w, 18, 'F')
            pdf.set_text_color(*color)
            pdf.set_font("Arial", "B", 16)
            pdf.set_xy(x, y + 1)
            pdf.cell(col_w, 8, valor, 0, 0, "C")
            pdf.set_font("Arial", "", 8)
            pdf.set_text_color(100, 116, 139)
            pdf.set_xy(x, y + 9)
            pdf.cell(col_w, 6, etiqueta, 0, 0, "C")
            pdf.set_xy(x + col_w + 3, y)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(25)
        
        # Puntos clave
        if dia_pico:
            dia_pico_fecha = dia_pico['fecha']
            if hasattr(dia_pico_fecha, 'strftime'):
                dia_pico_str = dia_pico_fecha.strftime('%d/%m/%Y')
            else:
                dia_pico_str = str(dia_pico_fecha)
            pdf.set_font("Arial", "B", 10)
            pdf.set_fill_color(240, 253, 244)
            pdf.cell(0, 8, f"  Dia con mas afluencia: {dia_pico_str} ({dia_pico['cantidad']} tickets)", ln=True, fill=True)
            pdf.ln(3)
        
        # Gráfico: Tickets por día
        if os.path.exists(chart_dias):
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 8, chart_titulo, ln=True)
            pdf.ln(2)
            pdf.image(chart_dias, x=15, w=180)
            pdf.ln(8)
        
        # Gráfico: Tickets por ventanilla
        if por_ventanilla and os.path.exists(chart_ventanillas):
            pdf.add_page()
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 8, "Tickets Atendidos por Ventanilla", ln=True)
            pdf.ln(2)
            pdf.image(chart_ventanillas, x=15, w=180)
            pdf.ln(8)
            
            pdf.set_font("Arial", "B", 10)
            pdf.set_fill_color(241, 245, 249)
            pdf.cell(100, 8, "Ventanilla", 1, 0, "C", True)
            pdf.cell(60, 8, "Tickets Completados", 1, 1, "C", True)
            
            pdf.set_font("Arial", "", 9)
            for nombre, cantidad in sorted(por_ventanilla.items(), key=lambda x: x[1], reverse=True):
                pdf.cell(100, 7, f"  {nombre}", 1, 0)
                pdf.cell(60, 7, str(cantidad), 1, 1, "C")
            pdf.ln(8)
        
        # Gráfico: Distribución por sector
        if por_sector and os.path.exists(chart_sectores):
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 8, "Distribucion por Sector", ln=True)
            pdf.ln(2)
            pdf.image(chart_sectores, x=40, w=130)
        
        # Guardar PDF
        pdf_path = os.path.join(tmpdir, 'reporte.pdf')
        pdf.output(pdf_path)
        
        return pdf_path
        
    finally:
        cursor.close()
        conn.close()


# ─── Endpoints ───

@bp.route('/reporte/generar', methods=['GET'])
def generar_reporte():
    """Genera un reporte PDF para un rango de fechas específico."""
    desde = request.args.get('desde')
    hasta = request.args.get('hasta')
    
    if not desde or not hasta:
        return jsonify({"error": "Parámetros 'desde' y 'hasta' son requeridos"}), 400
    
    try:
        desde_date = datetime.strptime(desde, '%Y-%m-%d').date()
        hasta_date = datetime.strptime(hasta, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
    
    # Validar rango semestral
    valido, error = validar_rango_semestral(desde_date, hasta_date)
    if not valido:
        return jsonify({"error": error}), 400
    
    try:
        pdf_path = _construir_reporte_pdf(desde, hasta, "Reporte de Tickets")
        
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'reporte_{desde}_{hasta}.pdf'
        )
    except Exception as e:
        print(f"Error en generar_reporte: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al generar reporte: {str(e)}"}), 500


@bp.route('/reporte/limpieza-semestral', methods=['GET'])
def limpieza_semestral():
    """
    Verifica si hay tickets del semestre anterior.
    Si existen: genera PDF del semestre anterior, elimina esos tickets, retorna el PDF.
    Si no existen: retorna 204 No Content.
    """
    tz = pytz.timezone('America/Mexico_City')
    hoy = datetime.now(tz).date()
    
    sem_ant_inicio, sem_ant_fin = obtener_semestre_anterior(hoy)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verificar si hay tickets del semestre anterior
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Turno
            WHERE DATE(Fecha_Ticket) BETWEEN %s AND %s
        """, (sem_ant_inicio.strftime('%Y-%m-%d'), sem_ant_fin.strftime('%Y-%m-%d')))
        
        resultado = cursor.fetchone()
        
        if not resultado or resultado['total'] == 0:
            return '', 204
        
        # Generar PDF del semestre anterior ANTES de eliminar
        sem_label = f"Ene-Jun {sem_ant_inicio.year}" if sem_ant_inicio.month == 1 else f"Jul-Dic {sem_ant_inicio.year}"
        pdf_path = _construir_reporte_pdf(
            sem_ant_inicio.strftime('%Y-%m-%d'),
            sem_ant_fin.strftime('%Y-%m-%d'),
            f"Reporte Semestral - {sem_label}"
        )
        
        # Eliminar SOLO tickets del semestre anterior (no los del actual)
        cursor.execute("""
            DELETE FROM Turno
            WHERE DATE(Fecha_Ticket) BETWEEN %s AND %s
        """, (sem_ant_inicio.strftime('%Y-%m-%d'), sem_ant_fin.strftime('%Y-%m-%d')))
        
        tickets_eliminados = cursor.rowcount
        conn.commit()
        print(f"Limpieza semestral: {tickets_eliminados} tickets eliminados del periodo {sem_ant_inicio} a {sem_ant_fin}")
        
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'reporte_semestral_{sem_ant_inicio}_{sem_ant_fin}.pdf'
        )
        
    except Exception as e:
        conn.rollback()
        print(f"Error en limpieza_semestral: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error en limpieza semestral: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@bp.route('/reporte/semestre-actual', methods=['GET'])
def info_semestre_actual():
    """Retorna las fechas del semestre actual para validación en frontend."""
    tz = pytz.timezone('America/Mexico_City')
    hoy = datetime.now(tz).date()
    inicio, fin = obtener_semestre(hoy)
    
    return jsonify({
        "inicio": inicio.strftime('%Y-%m-%d'),
        "fin": fin.strftime('%Y-%m-%d'),
        "label": f"Ene-Jun {inicio.year}" if inicio.month == 1 else f"Jul-Dic {inicio.year}"
    })
