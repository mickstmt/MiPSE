from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Tablas intermedias para RBAC (Roles y Permisos)
usuario_roles = db.Table('usuario_roles',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('rol_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

rol_permisos = db.Table('rol_permisos',
    db.Column('rol_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permiso_id', db.Integer, db.ForeignKey('permisos.id'), primary_key=True)
)

class Permiso(db.Model):
    __tablename__ = 'permisos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False) # ej: 'ventas.crear'
    
    def __repr__(self):
        return f'<Permiso {self.codigo}>'

class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    
    permisos = db.relationship('Permiso', secondary=rol_permisos, lazy='subquery',
                               backref=db.backref('roles', lazy=True))
    
    def __repr__(self):
        return f'<Rol {self.nombre}>'


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
    
    # Nuevos campos para auditoría y RBAC
    ultimo_login = db.Column(db.DateTime)
    ip_registro = db.Column(db.String(45))
    
    roles = db.relationship('Rol', secondary=usuario_roles, lazy='subquery',
                            backref=db.backref('usuarios', lazy=True))
    
    ventas = db.relationship('Venta', backref='vendedor', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def tiene_permiso(self, codigo_permiso):
        """Verifica si el usuario tiene un permiso específico a través de sus roles."""
        if self.es_admin:
            return True
        for rol in self.roles:
            for permiso in rol.permisos:
                if permiso.codigo == codigo_permiso:
                    return True
        return False
    
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
            # Filtrar valores None para evitar "Nombre None None"
            partes = [self.nombres, self.apellido_paterno, self.apellido_materno]
            return " ".join(filter(None, partes)).strip()
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
    costo_envio = db.Column(db.Numeric(10, 2), default=0.00)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    estado = db.Column(db.String(20), default='BORRADOR')
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_pedido = db.Column(db.DateTime, nullable=True) # Fecha original de WooCommerce
    fecha_envio_sunat = db.Column(db.DateTime, nullable=True)
    
    xml_path = db.Column(db.String(255))
    pdf_path = db.Column(db.String(255))
    cdr_path = db.Column(db.String(255))
    hash_cpe = db.Column(db.String(100))
    mensaje_sunat = db.Column(db.Text)
    codigo_sunat = db.Column(db.String(10))
    external_id = db.Column(db.String(100))  # ID único de MiPSE

    # Notas de Crédito
    tipo_comprobante = db.Column(db.String(20), default='BOLETA')  # 'BOLETA' | 'NOTA_CREDITO'
    venta_referencia_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=True)
    motivo_nc_codigo = db.Column(db.String(5), nullable=True)       # SUNAT catálogo 09
    motivo_nc_descripcion = db.Column(db.String(255), nullable=True)

    items = db.relationship('VentaItem', backref='venta', lazy=True, cascade='all, delete-orphan')
    venta_referencia = db.relationship('Venta', remote_side='Venta.id',
                                       foreign_keys='Venta.venta_referencia_id',
                                       backref=db.backref('notas_credito', lazy=True))
    
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


class InvoiceTemplate(db.Model):
    __tablename__ = 'invoice_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False) # ej: "A4 Estándar", "Ticket 80mm"
    es_activo = db.Column(db.Boolean, default=False)
    
    # Contenido del diseño
    html_content = db.Column(db.Text, nullable=False)
    css_content = db.Column(db.Text)
    
    # Configuraciones extras en JSON (márgenes, fuentes, etc.)
    config_json = db.Column(db.JSON, default={})
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<InvoiceTemplate {self.nombre}>'


class CostoProducto(db.Model):
    __tablename__ = 'costos_productos'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), index=True)
    desc = db.Column(db.String(255))
    colorcode = db.Column(db.String(100))
    sizecode = db.Column(db.String(100))
    costo = db.Column(db.Numeric(10, 2), default=0.00)

    def __repr__(self):
        return f'<CostoProducto {self.sku}>'
