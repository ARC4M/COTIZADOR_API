# --- Modelo para códigos de invitación ---
from database import db
class CodigoInvitacion(db.Model):
    __tablename__ = 'codigos_invitacion'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(32), unique=True, nullable=False)
    creado = db.Column(db.DateTime, nullable=False)
    vence = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Integer, default=0)

from database import db
from werkzeug.security import generate_password_hash, check_password_hash

class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    nit = db.Column(db.String(30), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(30), nullable=True)
    contacto = db.Column(db.String(100), nullable=True)
    logo_url = db.Column(db.String(200), nullable=True)
    cotizaciones = db.relationship('Cotizacion', backref='empresa', lazy=True)
    token_activo = db.Column(db.Text, nullable=True)  # Token JWT activo para control de sesión

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
from sqlalchemy import LargeBinary

# --- Modelo Producto ---
class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Float, nullable=False)
    unidad = db.Column(db.String(30), nullable=True)
    codigo = db.Column(db.String(50), nullable=True)
    # Puedes agregar más campos según necesidad

class Cotizacion(db.Model):
    __tablename__ = 'cotizaciones'

    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(30), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    vendedor = db.Column(db.String(100), nullable=True)
    fecha = db.Column(db.String(30), nullable=True)
    validez = db.Column(db.String(30), nullable=True)
    forma_pago = db.Column(db.String(100), nullable=True)
    tiempo_entrega = db.Column(db.String(100), nullable=True)
    estado_cotizacion = db.Column(db.String(30), nullable=True)
    notas_legales = db.Column(db.Text, nullable=True)
    firma = db.Column(db.Text, nullable=True)  # Puede ser base64 o texto
    codigo_cotizacion = db.Column(db.String(30), nullable=False, unique=True)
    observaciones = db.Column(db.Text, nullable=True)
    productos = db.Column(db.JSON, nullable=False)
    subtotal = db.Column(db.Float, nullable=True)
    descuento = db.Column(db.Float, nullable=True)
    iva = db.Column(db.Float, nullable=True)
    total = db.Column(db.Float, nullable=False)
    condiciones = db.Column(db.Text, nullable=True)
    estado_envio = db.Column(db.String(20), nullable=False)
    archivo_pdf = db.Column(LargeBinary, nullable=False)

