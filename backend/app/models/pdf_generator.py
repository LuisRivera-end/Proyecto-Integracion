from fpdf import FPDF
import os

class TicketPDF(FPDF):
    def header(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "..", "..", "ual.png")
        try:
            self.image(image_path, x=14, y=5, w=30)
        except Exception as e:
            print(f"Error al cargar la imagen: {e}")
            pass
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "Esfuerzo que trasciende", 0, 0, "C")

def generar_ticket_PDF(matricula, numero_ticket, sector, fecha, tiempo_estimado):
    pdf = TicketPDF("P", "mm", (58, 210))
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(left=2, top=5, right=2)
    pdf.add_page()

    # Encabezado
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "TICKET", ln=True, align="C")
    pdf.ln(2)

    # Datos generales
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"N° Ticket: {numero_ticket}", ln=True)
    pdf.cell(0, 6, f"Matricula: {matricula}", ln=True)
    pdf.cell(0, 6, f"Sector: {sector}", ln=True)
    pdf.cell(0, 6, f"Fecha: {fecha}", ln=True)
    pdf.cell(0, 6, f"Tiempo Aproximado: {tiempo_estimado} minutos", ln=True)
    pdf.ln(3)

    # Separador
    pdf.cell(0, 0, "-" * 40, ln=True, align="C")
    pdf.ln(3)

    return pdf.output(dest='S').encode('latin-1')