from fpdf import FPDF
from io import BytesIO
import os

def generar_pdf(data, filename):
    pdf = FPDF()
    pdf.add_page()
    # --- Colores corporativos personalizados ---
    COLOR_PRIMARIO = (26, 35, 126)      # Azul oscuro
    COLOR_SECUNDARIO = (21, 101, 192)   # Azul medio
    COLOR_TEXTO = (33, 33, 33)          # Gris oscuro
    COLOR_TABLA_HEADER = (197, 225, 250) # Azul claro
    COLOR_TABLA_ROW_ALT = (232, 240, 253) # Muy claro
    COLOR_TABLA_ROW = (255, 255, 255)
    COLOR_BACKGROUND = (245, 249, 255)   # Azul muy claro para fondo

    # --- Fondo de página personalizado ---
    pdf.set_fill_color(*COLOR_BACKGROUND)
    pdf.rect(0, 0, 210, 297, 'F')  # A4: 210x297mm

    # Código de cotización
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(*COLOR_PRIMARIO)
    pdf.cell(0, 8, f"Código: {data.get('codigo_cotizacion', '')}", ln=True, align='R')
    pdf.set_text_color(*COLOR_TEXTO)

    # --- DATOS DE EMPRESA DINÁMICOS ---
    empresa = data.get('empresa', {})
    nombre_empresa = empresa.get('nombre', 'EMPRESA')
    nit = empresa.get('nit', '')
    direccion = empresa.get('direccion', '')
    telefono = empresa.get('telefono', '')
    contacto = empresa.get('contacto', '')
    logo_url = empresa.get('logo_url')
    email_empresa = empresa.get('email', '')

    # Logo (si hay url o ruta)
    if logo_url:
        try:
            if os.path.exists(logo_url):
                pdf.image(logo_url, x=10, y=8, w=35)
        except Exception:
            pass
    else:
        logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logo.jpg'))
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=10, y=8, w=35)

    # Nombre de la empresa y datos
    pdf.set_xy(50, 10)
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*COLOR_PRIMARIO)
    pdf.cell(0, 10, nombre_empresa, ln=True, align='L')
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(60, 60, 60)
    pdf.set_x(50)
    if nit:
        pdf.cell(0, 8, f"NIT: {nit}", ln=True, align='L')
    if direccion:
        pdf.set_x(50)
        pdf.cell(0, 8, f"Dirección: {direccion}", ln=True, align='L')
    if telefono:
        pdf.set_x(50)
        pdf.cell(0, 8, f"Tel: {telefono}", ln=True, align='L')
    if email_empresa:
        pdf.set_x(50)
        pdf.cell(0, 8, f"Email: {email_empresa}", ln=True, align='L')
    if contacto:
        pdf.set_x(50)
        pdf.cell(0, 8, f"Contacto: {contacto}", ln=True, align='L')
    pdf.set_text_color(*COLOR_TEXTO)
    pdf.ln(10)


    # Línea divisoria
    pdf.set_draw_color(*COLOR_PRIMARIO)
    pdf.set_line_width(1.2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    # Título Cotización
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(*COLOR_SECUNDARIO)
    pdf.cell(0, 15, "COTIZACIÓN", ln=True, align='C')
    pdf.set_text_color(*COLOR_TEXTO)
    pdf.ln(2)


    # Recuadro datos del cliente con más información
    pdf.set_fill_color(232, 240, 253)  # Color muy claro corporativo
    pdf.set_draw_color(*COLOR_SECUNDARIO)
    pdf.set_font("Arial", '', 12)
    pdf.cell(95, 8, f"Cliente: {data.get('cliente','')}", border='LT', fill=True)
    pdf.cell(95, 8, f"Correo: {data.get('correo','')}", border='TR', fill=True, ln=True)
    pdf.cell(95, 8, f"Teléfono: {data.get('telefono','')}", border='L', fill=True)
    pdf.cell(95, 8, f"Dirección: {data.get('direccion','')}", border='R', fill=True, ln=True)
    pdf.cell(95, 8, f"Vendedor: {data.get('vendedor','')}", border='L', fill=True)
    pdf.cell(95, 8, f"Fecha: {data.get('fecha','')}", border='R', fill=True, ln=True)
    pdf.cell(95, 8, f"Validez: {data.get('validez','')}", border='L', fill=True)
    pdf.cell(95, 8, f"Forma de pago: {data.get('forma_pago','')}", border='R', fill=True, ln=True)
    pdf.cell(95, 8, f"Entrega: {data.get('tiempo_entrega','')}", border='L', fill=True)
    pdf.cell(95, 8, f"Estado: {data.get('estado_cotizacion','')}", border='R', fill=True, ln=True)
    pdf.cell(190, 0, '', border='LBR', ln=True)
    pdf.ln(6)


    # Tabla de productos con filas alternas y descuento por producto
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(*COLOR_TABLA_HEADER)
    pdf.set_text_color(*COLOR_PRIMARIO)
    pdf.cell(50, 10, "Producto", border=1, fill=True)
    pdf.cell(20, 10, "Cant.", border=1, fill=True, align='C')
    pdf.cell(30, 10, "Precio", border=1, fill=True, align='C')
    pdf.cell(30, 10, "Desc.", border=1, fill=True, align='C')
    pdf.cell(30, 10, "IVA", border=1, fill=True, align='C')
    pdf.cell(30, 10, "Subtotal", border=1, fill=True, align='C')
    pdf.ln()

    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(*COLOR_TEXTO)
    fill = False
    for p in data["productos"]:
        subtotal = p["cantidad"] * p["precio"]
        desc = p.get("descuento", 0)
        iva_prod = p.get("iva", 0)
        subtotal_desc = subtotal - desc
        subtotal_iva = subtotal_desc + (subtotal_desc * iva_prod / 100)
        if fill:
            pdf.set_fill_color(*COLOR_TABLA_ROW_ALT)
        else:
            pdf.set_fill_color(*COLOR_TABLA_ROW)
        pdf.cell(50, 10, str(p['nombre']), border=1, fill=True)
        pdf.cell(20, 10, str(p['cantidad']), border=1, align='C', fill=True)
        pdf.cell(30, 10, f"${p['precio']:,}", border=1, align='R', fill=True)
        pdf.cell(30, 10, f"${desc:,}", border=1, align='R', fill=True)
        pdf.cell(30, 10, f"{iva_prod}%", border=1, align='C', fill=True)
        pdf.cell(30, 10, f"${subtotal_iva:,.0f}", border=1, align='R', fill=True)
        pdf.ln()
        fill = not fill


    # Resumen de totales
    pdf.ln(5)
    pdf.set_font("Arial", '', 12)
    pdf.cell(160, 8, "Subtotal:", align='R')
    pdf.cell(30, 8, f"${data.get('subtotal', 0):,.0f}", align='R', ln=True)
    pdf.cell(160, 8, "Descuento:", align='R')
    pdf.cell(30, 8, f"${data.get('descuento', 0):,.0f}", align='R', ln=True)
    pdf.cell(160, 8, "IVA:", align='R')
    pdf.cell(30, 8, f"${data.get('iva', 0):,.0f}%", align='R', ln=True)
    pdf.set_font("Arial", 'B', 13)
    pdf.set_fill_color(*COLOR_PRIMARIO)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(160, 12, "TOTAL", border=1, align='R', fill=True)
    pdf.cell(30, 12, f"${data.get('total', 0):,.0f}", border=1, align='R', fill=True)
    pdf.set_text_color(*COLOR_TEXTO)
    pdf.ln(18)




    # Notas legales (si existen)
    if data.get('notas_legales'):
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(255, 249, 196)  # Amarillo suave corporativo
        pdf.set_text_color(*COLOR_PRIMARIO)
        pdf.cell(0, 8, "Notas legales:", ln=True, fill=True)
        pdf.set_font("Arial", '', 11)
        pdf.set_fill_color(255, 253, 231)
        pdf.set_text_color(*COLOR_TEXTO)
        pdf.multi_cell(0, 8, data['notas_legales'], fill=True)

    # Observaciones (si existen)
    if data.get('observaciones'):
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(255, 249, 196)
        pdf.set_text_color(*COLOR_PRIMARIO)
        pdf.cell(0, 8, "Observaciones:", ln=True, fill=True)
        pdf.set_font("Arial", '', 12)
        pdf.set_fill_color(255, 253, 231)
        pdf.set_text_color(*COLOR_TEXTO)
        pdf.multi_cell(0, 8, data['observaciones'], fill=True)

    # Condiciones (si existen)
    if data.get('condiciones'):
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(255, 249, 196)
        pdf.set_text_color(*COLOR_PRIMARIO)
        pdf.cell(0, 8, "Condiciones:", ln=True, fill=True)
        pdf.set_font("Arial", '', 12)
        pdf.set_fill_color(255, 253, 231)
        pdf.set_text_color(*COLOR_TEXTO)
        pdf.multi_cell(0, 8, data['condiciones'], fill=True)



    # Espacio para firma
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(*COLOR_SECUNDARIO)
    pdf.cell(0, 8, "Firma del cliente: ____________________________", ln=True)
    pdf.set_text_color(*COLOR_TEXTO)
    if data.get('firma'):
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 8, f"(Firma digital: {data['firma'][:20]}...)", ln=True)

    # Pie de página
    pdf.set_y(-25)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(*COLOR_SECUNDARIO)
    pdf.cell(0, 10, "Gracias por su interés. Para dudas, contáctenos.", 0, 0, 'C')
    pdf.set_text_color(*COLOR_TEXTO)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    ruta = os.path.join("cotizador_api", "cotizaciones", filename)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    pdf.output(ruta)
    return pdf_bytes, data.get('total', 0)

