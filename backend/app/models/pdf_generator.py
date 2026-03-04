from fpdf import FPDF
import os
from datetime import datetime

class TicketPDF(FPDF):
    def header(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "..", "..", "ual_no_fondo.png")
        try:
            self.image(image_path, x=14, y=5, w=30)
        except Exception as e:
            print(f"Error al cargar la imagen: {e}")
            pass
        self.ln(20)

    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "I", 7)
        self.cell(0, 4, "Esfuerzo que trasciende", 0, 0, "C")

def _formatear_fecha(fecha_str):
    """Convierte '2026-02-26 17:54:52' a '26/Feb/2026 - 05:54 PM'"""
    meses = {
        1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
    }
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        mes = meses[dt.month]
        hora = dt.strftime("%I:%M %p")
        return f"{dt.day}/{mes}/{dt.year}", hora
    except Exception:
        return fecha_str, ""

def generar_ticket_PDF(numero_ticket, sector, fecha):
    pdf = TicketPDF("P", "mm", (58, 90))
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(left=3, top=5, right=3)
    pdf.add_page()

    # --- Título ---
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, "TICKET DE TURNO", ln=True, align="C")
    pdf.ln(2)

    # --- Separador punteado ---
    y_actual = pdf.get_y()
    pdf.line(3, y_actual, 55, y_actual)
    pdf.ln(3)

    # --- "Su turno:" label ---
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 4, "Su turno:", ln=True, align="C")
    pdf.ln(1)

    # --- FOLIO GRANDE (protagonista) ---
    pdf.set_font("Arial", "B", 22)
    pdf.cell(0, 12, numero_ticket, ln=True, align="C")
    pdf.ln(1)

    # --- Sector ---
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, sector, ln=True, align="C")
    pdf.ln(2)

    # --- Separador punteado ---
    y_actual = pdf.get_y()
    pdf.line(3, y_actual, 55, y_actual)
    pdf.ln(3)
    
    # --- Fecha formateada ---
    pdf.set_font("Arial", "I", 7)
    fecha_fmt, hora_fmt = _formatear_fecha(fecha)
    if hora_fmt:
        pdf.cell(0, 4, f"{fecha_fmt} - {hora_fmt}", ln=True, align="C")
    else:
        pdf.cell(0, 4, fecha_fmt, ln=True, align="C")
    pdf.ln(2)
    # --- Mensaje ---
    pdf.cell(0, 3, "Conserve este ticket", ln=True, align="C")
    pdf.cell(0, 3, "para su atencion", ln=True, align="C")
    

    # Espacio para corte
    pdf.ln(8)

    return pdf.output(dest='S').encode('latin-1')