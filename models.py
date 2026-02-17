from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
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
        return f'<Usuario {self.username}>'


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
    external_id = db.Column(db.String(100))  # ID único de MiPSE
    
    items = db.relationship('VentaItem', backref='venta', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Venta {self.numero_completo}>'


class VentaItem(db.Model):
    __tablename__ = 'venta_items'
    
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    
    producto_nombre = db.Column(db.String(200), nullable=False)
    producto_sku = db.Column(db.String(100), nullable=True)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Nuevo: Referencia opcional a la variación vendida
    variacion_id = db.Column(db.Integer, nullable=True) # ID de WooCommerce
    atributos_json = db.Column(db.JSON, nullable=True) # Para guardar color, talla, etc.

    def __repr__(self):
        return f'<VentaItem {self.producto_nombre}>'


# Tabla de asociación muchos-a-muchos entre Productos y Categorías
producto_categorias = db.Table('producto_categorias',
    db.Column('producto_id', db.Integer, db.ForeignKey('productos.id'), primary_key=True),
    db.Column('categoria_id', db.Integer, db.ForeignKey('categorias.id'), primary_key=True)
)


class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True) # ID de WooCommerce
    nombre = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100))
    padre_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=True)
    count = db.Column(db.Integer, default=0)
    
    hijos = db.relationship('Categoria', backref=db.backref('padre', remote_side=[id]), lazy=True)
    # Relación muchos-a-muchos con productos
    productos = db.relationship('Producto', secondary=producto_categorias, lazy='subquery',
                               backref=db.backref('categorias', lazy=True))

    def __repr__(self):
        return f'<Categoria {self.nombre}>'


class Producto(db.Model):
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True) # ID de WooCommerce
    nombre = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), index=True)
    precio = db.Column(db.Numeric(10, 2), default=0.00)
    stock_status = db.Column(db.String(20), default='instock')
    imagen_url = db.Column(db.Text, nullable=True)
    
    # Nuevo: Tipo de producto (simple o variable)
    tipo = db.Column(db.String(20), default='simple') # simple, variable
    
    # Mantenemos por compatibilidad temporal, pero usaremos la relación categorias
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=True)
    
    fecha_sincronizacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con sus variaciones
    variaciones = db.relationship('Variacion', backref='producto', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Producto {self.nombre}>'


class Variacion(db.Model):
    __tablename__ = 'variaciones'
    
    id = db.Column(db.Integer, primary_key=True) # ID de WooCommerce
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    sku = db.Column(db.String(100), index=True)
    precio = db.Column(db.Numeric(10, 2), default=0.00)
    stock_status = db.Column(db.String(20), default='instock')
    imagen_url = db.Column(db.Text, nullable=True)
    
    # Atributos en formato JSON: {"Color": "Negro", "Talla": "XL"}
    atributos = db.Column(db.JSON, nullable=False)

    def __repr__(self):
        return f'<Variacion {self.sku} (Prod: {self.producto_id})>'
