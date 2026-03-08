from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fpdf import FPDF
from datetime import datetime, timedelta, date
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import tempfile
import pytz
import asyncio

from app.models.database import get_db

router = APIRouter(prefix="/api", tags=["Reportes"])

DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
COLORES_CHART = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4']

# ─── Utilidades de semestre ───

def obtener_semestre(fecha: date):
    if fecha.month <= 6:
        return date(fecha.year, 1, 1), date(fecha.year, 6, 30)
    else:
        return date(fecha.year, 7, 1), date(fecha.year, 12, 31)

def obtener_semestre_anterior(fecha: date):
    if fecha.month <= 6:
        return date(fecha.year - 1, 7, 1), date(fecha.year - 1, 12, 31)
    else:
        return date(fecha.year, 1, 1), date(fecha.year, 6, 30)

def validar_rango_semestral(desde: date, hasta: date):
    sem_desde = obtener_semestre(desde)
    sem_hasta = obtener_semestre(hasta)
    if sem_desde != sem_hasta:
        return False, "El rango de fechas no puede cruzar entre semestres (Ene-Jun / Jul-Dic)"
    if desde > hasta:
        return False, "La fecha de inicio no puede ser posterior a la fecha fin"
    return True, None

# ─── Generadores de gráficos (Síncronos) ───

def _generar_grafico_barras(datos, titulo, xlabel, ylabel, filename, color='#10b981'):
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

# ─── Lógica Asíncrona de BD + Lógica en Hilo ───

async def _extraer_datos_db(fecha_inicio_str: str, fecha_fin_str: str, sector: str, db: AsyncSession):
    # 1. Resumen general
    q_resumen = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN t.ID_Estados = 4 THEN 1 ELSE 0 END) as completados,
            SUM(CASE WHEN t.ID_Estados = 2 THEN 1 ELSE 0 END) as cancelados,
            SUM(CASE WHEN t.ID_Estados = 1 THEN 1 ELSE 0 END) as pendientes,
            SUM(CASE WHEN t.ID_Estados = 3 THEN 1 ELSE 0 END) as atendiendo
        FROM Turno t
        JOIN Sectores s ON t.ID_Sector = s.ID_Sector
        WHERE DATE(t.Fecha_Ticket) BETWEEN :fi AND :ff
    """
    params = {"fi": fecha_inicio_str, "ff": fecha_fin_str}
    if sector:
        q_resumen += " AND s.Sector = :sec"
        params["sec"] = sector
        
    res_res = await db.execute(text(q_resumen), params)
    resumen = dict(res_res.mappings().fetchone())
    
    # 2. Tickets por fecha
    q_fecha = """
        SELECT DATE(t.Fecha_Ticket) as fecha, COUNT(*) as cantidad
        FROM Turno t
        JOIN Sectores s ON t.ID_Sector = s.ID_Sector
        WHERE DATE(t.Fecha_Ticket) BETWEEN :fi AND :ff
    """
    if sector:
        q_fecha += " AND s.Sector = :sec"
    q_fecha += " GROUP BY DATE(t.Fecha_Ticket) ORDER BY fecha"
    
    res_fecha = await db.execute(text(q_fecha), params)
    por_fecha = [dict(r) for r in res_fecha.mappings().fetchall()]

    # 3. Tickets por ventanilla
    q_ventanilla = """
        SELECT v.Ventanilla as nombre, COUNT(*) as cantidad
        FROM Turno t
        JOIN Ventanillas v ON t.ID_Ventanilla = v.ID_Ventanilla
        JOIN Sectores s ON t.ID_Sector = s.ID_Sector
        WHERE DATE(t.Fecha_Ticket) BETWEEN :fi AND :ff
          AND t.ID_Estados = 4
    """
    if sector:
        q_ventanilla += " AND s.Sector = :sec"
    q_ventanilla += " GROUP BY v.Ventanilla ORDER BY cantidad DESC"
    
    res_ventanilla = await db.execute(text(q_ventanilla), params)
    por_ventanilla = [dict(r) for r in res_ventanilla.mappings().fetchall()]

    # 4. Tickets por sector
    q_sector = """
        SELECT s.Sector as nombre, COUNT(*) as cantidad
        FROM Turno t
        JOIN Sectores s ON t.ID_Sector = s.ID_Sector
        WHERE DATE(t.Fecha_Ticket) BETWEEN :fi AND :ff
    """
    if sector:
        q_sector += " AND s.Sector = :sec"
    q_sector += " GROUP BY s.Sector ORDER BY cantidad DESC"
    
    res_sector = await db.execute(text(q_sector), params)
    por_sector = [dict(r) for r in res_sector.mappings().fetchall()]

    # 5. Día pico
    q_pico = """
        SELECT DATE(t.Fecha_Ticket) as fecha, COUNT(*) as cantidad
        FROM Turno t
        JOIN Sectores s ON t.ID_Sector = s.ID_Sector
        WHERE DATE(t.Fecha_Ticket) BETWEEN :fi AND :ff
    """
    if sector:
        q_pico += " AND s.Sector = :sec"
    q_pico += " GROUP BY DATE(t.Fecha_Ticket) ORDER BY cantidad DESC LIMIT 1"
    
    res_pico = await db.execute(text(q_pico), params)
    row_pico = res_pico.mappings().fetchone()
    dia_pico = dict(row_pico) if row_pico else None

    return {
        "resumen": resumen,
        "por_fecha": por_fecha,
        "por_ventanilla": por_ventanilla,
        "por_sector": por_sector,
        "dia_pico": dia_pico,
    }

def _construir_pdf_sync(datos, fecha_inicio_str, fecha_fin_str, titulo="Reporte de Tickets"):
    tmpdir = tempfile.mkdtemp()
    
    resumen = datos["resumen"]
    por_fecha = datos["por_fecha"]
    por_ventanilla_list = datos["por_ventanilla"]
    por_sector_list = datos["por_sector"]
    dia_pico = datos["dia_pico"]

    fecha_cantidades = {}
    for row in por_fecha:
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
    
    from collections import OrderedDict

    if total_dias <= 14:
        chart_datos = OrderedDict()
        current = desde_dt_temp
        while current <= hasta_dt_temp:
            label = f"{current.strftime('%d/%m')} ({dia_nombres[current.isoweekday()]})"
            chart_datos[label] = fecha_cantidades.get(current, 0)
            current += timedelta(days=1)
        chart_titulo = 'Tickets por Fecha'
        chart_xlabel = 'Fecha'
    elif total_dias <= 90:
        chart_datos = OrderedDict()
        current = desde_dt_temp
        while current <= hasta_dt_temp:
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

    por_ventanilla = {row['nombre']: row['cantidad'] for row in por_ventanilla_list}
    por_sector = {row['nombre']: row['cantidad'] for row in por_sector_list}
    
    chart_dias = os.path.join(tmpdir, 'chart_dias.png')
    _generar_grafico_barras(chart_datos, chart_titulo, chart_xlabel, 'Cantidad', chart_dias, '#10b981')
    
    chart_ventanillas = os.path.join(tmpdir, 'chart_ventanillas.png')
    if por_ventanilla:
        _generar_grafico_barras(por_ventanilla, 'Tickets Atendidos por Ventanilla', 'Ventanilla', 'Completados', chart_ventanillas, '#3b82f6')
    
    chart_sectores = os.path.join(tmpdir, 'chart_sectores.png')
    if por_sector:
        _generar_grafico_pastel(por_sector, 'Distribucion por Sector', chart_sectores)

    # Construir PDF
    desde_dt = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
    hasta_dt = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
    fecha_i_fmt = desde_dt.strftime('%d/%m/%Y')
    fecha_f_fmt = hasta_dt.strftime('%d/%m/%Y')
    
    pdf = ReportePDF(fecha_i_fmt, fecha_f_fmt, titulo)
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "Resumen General", ln=True)
    pdf.ln(3)
    
    total = resumen['total'] or 0
    completados = resumen['completados'] or 0
    cancelados = resumen['cancelados'] or 0
    pendientes = resumen['pendientes'] or 0
    
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
    
    if os.path.exists(chart_dias):
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, chart_titulo, ln=True)
        pdf.ln(2)
        pdf.image(chart_dias, x=15, w=180)
        pdf.ln(8)
    
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
    
    if por_sector and os.path.exists(chart_sectores):
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 8, "Distribucion por Sector", ln=True)
        pdf.ln(2)
        pdf.image(chart_sectores, x=40, w=130)
    
    pdf_path = os.path.join(tmpdir, 'reporte.pdf')
    pdf.output(pdf_path)
    
    return pdf_path


# ─── Endpoints ───

@router.get("/reporte/generar")
async def generar_reporte(
    desde: str = Query(None),
    hasta: str = Query(None),
    sector: str = Query(None),
    db: AsyncSession = Depends(get_db)):
    
    if not desde or not hasta:
        raise HTTPException(status_code=400, detail="Parámetros 'desde' y 'hasta' son requeridos")
    
    try:
        desde_date = datetime.strptime(desde, '%Y-%m-%d').date()
        hasta_date = datetime.strptime(hasta, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    valido, error = validar_rango_semestral(desde_date, hasta_date)
    if not valido:
        raise HTTPException(status_code=400, detail=error)
    
    try:
        titulo_reporte = f"Reporte de Tickets - {sector}" if sector else "Reporte de Tickets"
        
        # 1. Traer data Asincronamente de BD
        datos = await _extraer_datos_db(desde, hasta, sector, db)
        
        # 2. Construir PDF en thread síncrono para no bloquear Event Loop de FastAPI
        pdf_path = await asyncio.to_thread(_construir_pdf_sync, datos, desde, hasta, titulo_reporte)
        
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f'reporte_{desde}_{hasta}.pdf'
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reporte/limpieza-semestral")
async def limpieza_semestral(db: AsyncSession = Depends(get_db)):
    tz = pytz.timezone('America/Mexico_City')
    hoy = datetime.now(tz).date()
    
    sem_ant_inicio, sem_ant_fin = obtener_semestre_anterior(hoy)
    fi_str = sem_ant_inicio.strftime('%Y-%m-%d')
    ff_str = sem_ant_fin.strftime('%Y-%m-%d')
    
    try:
        q_count = text("""
            SELECT COUNT(*) as total
            FROM Turno
            WHERE DATE(Fecha_Ticket) BETWEEN :fi AND :ff
        """)
        res_count = await db.execute(q_count, {"fi": fi_str, "ff": ff_str})
        resultado = res_count.fetchone()
        
        if not resultado or resultado[0] == 0:
            from fastapi import Response
            return Response(status_code=204) # 204 No Content is what frontend expects to stop download
        
        sem_label = f"Ene-Jun {sem_ant_inicio.year}" if sem_ant_inicio.month == 1 else f"Jul-Dic {sem_ant_inicio.year}"
        titulo = f"Reporte Semestral - {sem_label}"
        
        # Extraer data asincrona
        datos = await _extraer_datos_db(fi_str, ff_str, None, db)
        
        # Construir en thread
        pdf_path = await asyncio.to_thread(_construir_pdf_sync, datos, fi_str, ff_str, titulo)
        
        # Eliminar asíncronamente
        q_del = text("DELETE FROM Turno WHERE DATE(Fecha_Ticket) BETWEEN :fi AND :ff")
        res_del = await db.execute(q_del, {"fi": fi_str, "ff": ff_str})
        tickets_eliminados = res_del.rowcount
        await db.commit()
        
        print(f"Limpieza semestral: {tickets_eliminados} tickets eliminados")
        
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f'reporte_semestral_{fi_str}_{ff_str}.pdf'
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reporte/semestre-actual")
async def info_semestre_actual():
    tz = pytz.timezone('America/Mexico_City')
    hoy = datetime.now(tz).date()
    inicio, fin = obtener_semestre(hoy)
    
    return {
        "inicio": inicio.strftime('%Y-%m-%d'),
        "fin": fin.strftime('%Y-%m-%d'),
        "label": f"Ene-Jun {inicio.year}" if inicio.month == 1 else f"Jul-Dic {inicio.year}"
    }
