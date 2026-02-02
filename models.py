from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    es_admin = db.Column(db.Boolean, default=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    ventas = db.relationship('Venta', backref='vendedor', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Usuario {self.email}>'


class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_documento = db.Column(db.String(3), nullable=False)
    numero_documento = db.Column(db.String(11), unique=True, nullable=False)
    nombres = db.Column(db.String(200), nullable=False)
    apellido_paterno = db.Column(db.String(100))
    apellido_materno = db.Column(db.String(100))
    razon_social = db.Column(db.String(200))
    direccion = db.Column(db.String(200))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    ventas = db.relationship('Venta', backref='cliente', lazy=True)
    
    @property
    def nombre_completo(self):
        if self.tipo_documento == 'DNI':
            return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}".strip()
        else:
            return self.razon_social
    
    def __repr__(self):
        return f'<Cliente {self.numero_documento}>'


class Venta(db.Model):
    __tablename__ = 'ventas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_orden = db.Column(db.String(20), nullable=True)
    serie = db.Column(db.String(10), nullable=False, default='B001')
    correlativo = db.Column(db.String(10), nullable=False)
    numero_completo = db.Column(db.String(20), nullable=False)
    
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    descuento = db.Column(db.Numeric(10, 2), default=0.00)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    estado = db.Column(db.String(20), default='BORRADOR')
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_envio_sunat = db.Column(db.DateTime, nullable=True)
    
    xml_path = db.Column(db.String(255))
    pdf_path = db.Column(db.String(255))
    cdr_path = db.Column(db.String(255))
    hash_cpe = db.Column(db.String(100))
    mensaje_sunat = db.Column(db.Text)
    codigo_sunat = db.Column(db.String(10))
    
    items = db.relationship('VentaItem', backref='venta', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Venta {self.numero_completo}>'


class VentaItem(db.Model):
    __tablename__ = 'venta_items'
    
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    
    producto_nombre = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    def __repr__(self):
        return f'<VentaItem {self.producto_nombre}>'
