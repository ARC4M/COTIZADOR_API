import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def enviar_email(destinatario, asunto, cuerpo, archivo_pdf):
    remitente = "camiloandresbenitezvaldes@gmail.com"
    password = "wkqo jlut ocja cgke"


    mensaje = EmailMessage()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto  # Unicode subject is supported
    mensaje.set_content(cuerpo, charset="utf-8")

    # Adjuntar PDF (desde memoria)
    # Use an ASCII filename for the attachment to avoid encoding issues
    mensaje.add_attachment(
        archivo_pdf,
        maintype="application",
        subtype="pdf",
        filename="cotizacion.pdf"
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(mensaje)
        return True
    except Exception as e:
        print("Error al enviar correo:", e)
        return False


