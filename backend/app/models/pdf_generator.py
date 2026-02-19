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

def generar_ticket_PDF(numero_ticket, sector, fecha):
    pdf = TicketPDF("P", "mm", (58, 100))  # Tamaño ajustado para ticket
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(left=3, top=5, right=3)
    pdf.add_page()

    # Encabezado (la imagen ya se coloca en header())
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "TICKET DE TURNO", ln=True, align="C")
    pdf.ln(2)

    # Datos del ticket
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, f"Folio: {numero_ticket}", ln=True)
    pdf.cell(0, 5, f"Sector: {sector}", ln=True)
    pdf.cell(0, 5, f"Fecha: {fecha}", ln=True)
    
    pdf.ln(3)
    
    # Separador
    pdf.cell(0, 0, "-" * 35, ln=True, align="C")
    pdf.ln(3)
    
    # Información adicional
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 4, "Conserve este ticket", ln=True, align="C")
    pdf.cell(0, 4, "para su atención", ln=True, align="C")
    
    # Espacio para corte
    pdf.ln(10)

    return pdf.output(dest='S').encode('latin-1')

def generar_ticket_PDF_archivo(numero_ticket, sector, fecha):
    pdf = TicketPDF("P", "mm", (58, 100))
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(left=3, top=5, right=3)
    pdf.add_page()

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "TICKET DE TURNO", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, f"Folio: {numero_ticket}", ln=True)
    pdf.cell(0, 5, f"Sector: {sector}", ln=True)
    pdf.cell(0, 5, f"Fecha: {fecha}", ln=True)

    pdf.ln(3)
    pdf.cell(0, 0, "-" * 35, ln=True, align="C")
    pdf.ln(3)

    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 4, "Conserve este ticket", ln=True, align="C")
    pdf.cell(0, 4, "para su atención", ln=True, align="C")

    pdf.ln(10)

    carpeta = "tickets"
    os.makedirs(carpeta, exist_ok=True)

    nombre_archivo = f"ticket_{numero_ticket}.pdf"
    ruta = os.path.join(carpeta, nombre_archivo)

    pdf.output(ruta)
    return ruta, nombre_archivo