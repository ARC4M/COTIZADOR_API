from flask import Blueprint, request, jsonify, current_app
from models import Cotizacion, Empresa, Producto, CodigoInvitacion
from database import db
from pdf_generator import generar_pdf
from email_sender import enviar_email
import os
from datetime import datetime
import jwt
from functools import wraps
import secrets
from datetime import timedelta
from flask import Blueprint

cotizacion_bp = Blueprint("cotizacion", __name__)

@cotizacion_bp.route('/codigo/seguridad', methods=['POST'])
def generar_codigo_invitacion():
    data = request.json or {}
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email y password requeridos'}), 400
    if email != admin_email or password != admin_password:
        return jsonify({'error': 'Credenciales de administrador inválidas'}), 401
    # Generar código y vencimiento
    codigo = secrets.token_urlsafe(8)
    vencimiento = datetime.utcnow() + timedelta(minutes=3)  # 3 minutos de validez
    # Guardar el código y vencimiento en una tabla temporal (puedes crear una tabla o usar un diccionario en memoria para demo)
    # Aquí se usa una tabla simple en la base de datos
    # Guardar el código
    nuevo = CodigoInvitacion(codigo=codigo, creado=datetime.utcnow(), vence=vencimiento)
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'codigo': codigo, 'vence': vencimiento.isoformat()})



# --- Decorador de autenticación JWT con control de token en base de datos ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'error': 'Token requerido'}), 401
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            empresa = Empresa.query.get(data['empresa_id'])
            if not empresa:
                return jsonify({'error': 'Empresa no encontrada'}), 401
            # Validar que el token coincida con el token_activo de la empresa
            if not empresa.token_activo or empresa.token_activo != token:
                return jsonify({'error': 'Token inválido o sesión cerrada'}), 401
        except Exception as e:
            return jsonify({'error': 'Token inválido', 'detail': str(e)}), 401
        return f(empresa, *args, **kwargs)
    return decorated

# --- Endpoint de registro de empresa ---
@cotizacion_bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    required = ["nombre", "email", "password", "nit", "direccion", "telefono", "contacto", "logo_url", "codigo_invitacion"]
    for k in required:
        if not data.get(k):
            return jsonify({'error': f'Campo requerido: {k}'}), 400
    # Validar código de invitación
    codigo = data['codigo_invitacion']
    invitacion = CodigoInvitacion.query.filter_by(codigo=codigo, usado=0).first()
    if not invitacion:
        return jsonify({'error': 'Código de invitación inválido'}), 400
    if invitacion.vence < datetime.utcnow():
        return jsonify({'error': 'Código de invitación vencido'}), 400
    # Marcar el código como usado
    invitacion.usado = 1
    db.session.commit()
    if Empresa.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email ya registrado'}), 400
    empresa = Empresa(
        nombre=data['nombre'],
        email=data['email'],
        nit=data['nit'],
        direccion=data['direccion'],
        telefono=data['telefono'],
        contacto=data['contacto'],
        logo_url=data['logo_url']
    )
    empresa.set_password(data['password'])
    try:
        db.session.add(empresa)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al registrar empresa', 'detail': str(e)}), 500
    return jsonify({'mensaje': 'Empresa registrada correctamente'}), 201

# --- Endpoint de login de empresa ---
@cotizacion_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    if not data.get("email") or not data.get("password"):
        return jsonify({'error': 'Email y password requeridos'}), 400
    empresa = Empresa.query.filter_by(email=data['email']).first()
    if not empresa or not empresa.check_password(data['password']):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    token = jwt.encode({'empresa_id': empresa.id}, current_app.config['SECRET_KEY'], algorithm="HS256")
    # Guardar el token en la base de datos como token_activo
    empresa.token_activo = token
    db.session.commit()
    # Devuelve también los datos de la empresa
    return jsonify({'token': token, 'empresa': {
        'nombre': empresa.nombre,
        'email': empresa.email,
        'nit': empresa.nit,
        'direccion': empresa.direccion,
        'telefono': empresa.telefono,
        'contacto': empresa.contacto,
        'logo_url': empresa.logo_url
    }})

# --- CRUD de productos ---
@cotizacion_bp.route('/producto', methods=['POST'])
@token_required
def crear_producto(empresa):
    data = request.json or {}
    nombre = data.get('nombre')
    precio = data.get('precio')
    if not nombre or precio is None:
        return jsonify({'error': 'Nombre y precio son requeridos'}), 400
    producto = Producto(
        empresa_id=empresa.id,
        nombre=nombre,
        descripcion=data.get('descripcion'),
        precio=precio,
        unidad=data.get('unidad'),
        codigo=data.get('codigo')
    )
    db.session.add(producto)
    db.session.commit()
    return jsonify({'mensaje': 'Producto creado', 'id': producto.id}), 201

@cotizacion_bp.route('/producto', methods=['GET'])
@token_required
def listar_productos(empresa):
    productos = Producto.query.filter_by(empresa_id=empresa.id).all()
    return jsonify([
        {
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'precio': p.precio,
            'unidad': p.unidad,
            'codigo': p.codigo
        } for p in productos
    ])

@cotizacion_bp.route('/producto/<int:producto_id>', methods=['GET'])
@token_required
def obtener_producto(empresa, producto_id):
    p = Producto.query.filter_by(id=producto_id, empresa_id=empresa.id).first()
    if not p:
        return jsonify({'error': 'Producto no encontrado'}), 404
    return jsonify({
        'id': p.id,
        'nombre': p.nombre,
        'descripcion': p.descripcion,
        'precio': p.precio,
        'unidad': p.unidad,
        'codigo': p.codigo
    })

@cotizacion_bp.route('/producto/<int:producto_id>', methods=['PUT'])
@token_required
def actualizar_producto(empresa, producto_id):
    p = Producto.query.filter_by(id=producto_id, empresa_id=empresa.id).first()
    if not p:
        return jsonify({'error': 'Producto no encontrado'}), 404
    data = request.json or {}
    for field in ['nombre', 'descripcion', 'precio', 'unidad', 'codigo']:
        if field in data:
            setattr(p, field, data[field])
    db.session.commit()
    return jsonify({'mensaje': 'Producto actualizado'}), 200

@cotizacion_bp.route('/producto/<int:producto_id>', methods=['DELETE'])
@token_required
def eliminar_producto(empresa, producto_id):
    p = Producto.query.filter_by(id=producto_id, empresa_id=empresa.id).first()
    if not p:
        return jsonify({'error': 'Producto no encontrado'}), 404
    db.session.delete(p)
    db.session.commit()
    return jsonify({'mensaje': 'Producto eliminado'}), 200

# --- CRUD de cotizaciones ---
@cotizacion_bp.route("/cotizacion", methods=["POST"])
@token_required
def crear_cotizacion(empresa):
    data = request.json or {}
    if not all(data.get(k) for k in ("cliente", "correo", "productos")):
        return jsonify({"error": "Datos incompletos"}), 400
    import json
    productos_input = data["productos"]
    if isinstance(productos_input, str):
        try:
            productos_input = json.loads(productos_input)
        except Exception:
            return jsonify({"error": "El campo 'productos' no es un JSON válido"}), 400
    if not isinstance(productos_input, list) or not productos_input:
        return jsonify({"error": "Debe enviar al menos un producto válido"}), 400

    # Validar que todos los productos existan en la base de datos y pertenezcan a la empresa
    productos_db = {p.id: p for p in Producto.query.filter_by(empresa_id=empresa.id).all()}
    productos_final = []
    for p in productos_input:
        prod_id = p.get("id")
        cantidad = p.get("cantidad", 1)
        if not prod_id or prod_id not in productos_db:
            return jsonify({"error": f"Producto con id {prod_id} no existe o no pertenece a la empresa"}), 400
        prod_db = productos_db[prod_id]
        # Usar datos reales del producto de la base de datos
        productos_final.append({
            "id": prod_db.id,
            "nombre": prod_db.nombre,
            "descripcion": prod_db.descripcion,
            "precio": prod_db.precio,
            "unidad": prod_db.unidad,
            "codigo": prod_db.codigo,
            "cantidad": cantidad
        })

    subtotal = sum(p["cantidad"] * p["precio"] for p in productos_final)
    descuento = float(data.get("descuento", 0))
    iva = float(data.get("iva", 0))
    total = subtotal - descuento
    if iva > 0:
        total += total * (iva / 100)
    codigo_cotizacion = data.get("codigo_cotizacion")
    if not codigo_cotizacion:
        codigo_cotizacion = f"COT-{int(datetime.utcnow().timestamp())}"
    data["subtotal"] = subtotal
    data["descuento"] = descuento
    data["iva"] = iva
    data["total"] = total
    data["codigo_cotizacion"] = codigo_cotizacion
    # --- Agregar datos de empresa al PDF ---
    data["empresa"] = {
        "nombre": empresa.nombre,
        "nit": empresa.nit,
        "direccion": empresa.direccion,
        "telefono": empresa.telefono,
        "contacto": empresa.contacto,
        "logo_url": empresa.logo_url,
        "email": empresa.email
    }
    data["productos"] = productos_final
    filename = f"cotizacion_{codigo_cotizacion}.pdf"
    try:
        pdf_bytes, _ = generar_pdf(data, filename)
    except Exception as e:
        return jsonify({"error": "Error generando PDF", "detail": str(e)}), 500
    try:
        enviado = enviar_email(data["correo"], "Cotización", "Adjunto PDF de cotización", pdf_bytes)
    except Exception as e:
        enviado = False
    estado = "Enviado" if enviado else "Fallido"
    cotizacion = Cotizacion(
        empresa_id=empresa.id,
        cliente=data["cliente"],
        correo=data["correo"],
        telefono=data.get("telefono"),
        direccion=data.get("direccion"),
        vendedor=data.get("vendedor"),
        fecha=data.get("fecha"),
        validez=data.get("validez"),
        forma_pago=data.get("forma_pago"),
        tiempo_entrega=data.get("tiempo_entrega"),
        estado_cotizacion=data.get("estado_cotizacion"),
        notas_legales=data.get("notas_legales"),
        firma=data.get("firma"),
        codigo_cotizacion=codigo_cotizacion,
        observaciones=data.get("observaciones"),
        productos=productos_final,
        subtotal=subtotal,
        descuento=descuento,
        iva=iva,
        total=total,
        condiciones=data.get("condiciones", ""),
        estado_envio=estado,
        archivo_pdf=pdf_bytes
    )
    try:
        db.session.add(cotizacion)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error guardando cotización", "detail": str(e)}), 500
    return jsonify({
        "mensaje": "Cotización procesada",
        "total": total,
        "estado": estado
    }), 200

# Listar cotizaciones de la empresa autenticada
@cotizacion_bp.route("/cotizacion", methods=["GET"])
@token_required
def listar_cotizaciones(empresa):
    cotizaciones = Cotizacion.query.filter_by(empresa_id=empresa.id).all()
    return jsonify([
        {
            'id': c.id,
            'empresa_id': c.empresa_id,
            'codigo_cotizacion': c.codigo_cotizacion,
            'cliente': c.cliente,
            'correo': c.correo,
            'telefono': c.telefono,
            'direccion': c.direccion,
            'vendedor': c.vendedor,
            'fecha': c.fecha,
            'validez': c.validez,
            'forma_pago': c.forma_pago,
            'tiempo_entrega': c.tiempo_entrega,
            'estado_cotizacion': c.estado_cotizacion,
            'notas_legales': c.notas_legales,
            'firma': c.firma,
            'observaciones': c.observaciones,
            'productos': c.productos,
            'subtotal': c.subtotal,
            'descuento': c.descuento,
            'iva': c.iva,
            'total': c.total,
            'condiciones': c.condiciones,
            'estado_envio': c.estado_envio,
            'archivo_pdf': True if c.archivo_pdf else False
        } for c in cotizaciones
    ])

# Obtener cotización por ID (solo si pertenece a la empresa)
@cotizacion_bp.route("/cotizacion/<int:cotizacion_id>", methods=["GET"])
@token_required
def obtener_cotizacion(empresa, cotizacion_id):
    c = Cotizacion.query.filter_by(id=cotizacion_id, empresa_id=empresa.id).first()
    if not c:
        return jsonify({'error': 'Cotización no encontrada'}), 404
    return jsonify({
        'id': c.id,
        'codigo_cotizacion': c.codigo_cotizacion,
        'cliente': c.cliente,
        'correo': c.correo,
        'telefono': c.telefono,
        'direccion': c.direccion,
        'vendedor': c.vendedor,
        'fecha': c.fecha,
        'validez': c.validez,
        'forma_pago': c.forma_pago,
        'tiempo_entrega': c.tiempo_entrega,
        'estado_cotizacion': c.estado_cotizacion,
        'notas_legales': c.notas_legales,
        'firma': c.firma,
        'observaciones': c.observaciones,
        'productos': c.productos,
        'subtotal': c.subtotal,
        'descuento': c.descuento,
        'iva': c.iva,
        'total': c.total,
        'condiciones': c.condiciones,
        'estado_envio': c.estado_envio
    })

# Eliminar cotización (solo si pertenece a la empresa)
@cotizacion_bp.route("/cotizacion/<int:cotizacion_id>", methods=["DELETE"])
@token_required
def eliminar_cotizacion(empresa, cotizacion_id):
    c = Cotizacion.query.filter_by(id=cotizacion_id, empresa_id=empresa.id).first()
    if not c:
        return jsonify({'error': 'Cotización no encontrada'}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({'mensaje': 'Cotización eliminada'}), 200

# Actualizar cotización (solo si pertenece a la empresa)
@cotizacion_bp.route("/cotizacion/<int:cotizacion_id>", methods=["PUT"])
@token_required
def actualizar_cotizacion(empresa, cotizacion_id):
    c = Cotizacion.query.filter_by(id=cotizacion_id, empresa_id=empresa.id).first()
    if not c:
        return jsonify({'error': 'Cotización no encontrada'}), 404
    data = request.json or {}
    # Si se actualizan productos, validar que existan y pertenezcan a la empresa
    if 'productos' in data:
        import json
        productos_input = data['productos']
        if isinstance(productos_input, str):
            try:
                productos_input = json.loads(productos_input)
            except Exception:
                return jsonify({'error': "El campo 'productos' no es un JSON válido"}), 400
        if not isinstance(productos_input, list) or not productos_input:
            return jsonify({'error': 'Debe enviar al menos un producto válido'}), 400
        productos_db = {p.id: p for p in Producto.query.filter_by(empresa_id=empresa.id).all()}
        productos_final = []
        for p in productos_input:
            prod_id = p.get('id')
            cantidad = p.get('cantidad', 1)
            if not prod_id or prod_id not in productos_db:
                return jsonify({'error': f'Producto con id {prod_id} no existe o no pertenece a la empresa'}), 400
            prod_db = productos_db[prod_id]
            productos_final.append({
                'id': prod_db.id,
                'nombre': prod_db.nombre,
                'descripcion': prod_db.descripcion,
                'precio': prod_db.precio,
                'unidad': prod_db.unidad,
                'codigo': prod_db.codigo,
                'cantidad': cantidad
            })
        c.productos = productos_final
        # Recalcular subtotal, total, etc. si se actualizan productos
        subtotal = sum(p['cantidad'] * p['precio'] for p in productos_final)
        c.subtotal = subtotal
        descuento = float(data.get('descuento', c.descuento or 0))
        iva = float(data.get('iva', c.iva or 0))
        total = subtotal - descuento
        if iva > 0:
            total += total * (iva / 100)
        c.descuento = descuento
        c.iva = iva
        c.total = total
    # Actualizar otros campos
    for field in [
        'cliente','correo','telefono','direccion','vendedor','fecha','validez','forma_pago','tiempo_entrega','estado_cotizacion','notas_legales','firma','observaciones','condiciones','estado_envio']:
        if field in data:
            setattr(c, field, data[field])
    db.session.commit()
    return jsonify({'mensaje': 'Cotización actualizada'}), 200

# --- Endpoint de logout (cierre de sesión) ---
@cotizacion_bp.route('/logout', methods=['POST'])
@token_required
def logout(empresa):
    # Elimina el token activo de la empresa
    empresa.token_activo = None
    db.session.commit()
    return jsonify({'mensaje': 'Sesión cerrada.'}), 200

@cotizacion_bp.route('/', methods=['GET'])
def home():
    return jsonify({"mensaje": "Bienvenido a la API de Cotizador"}), 200

