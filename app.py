from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, Usuario, Cliente, Venta, VentaItem
from datetime import datetime
from pdf_service import generar_pdf_boleta
from sunat_service import SUNATService
from scheduler_service import SchedulerService
import requests
import os
import atexit

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar extensiones
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Scheduler global para envío automático
scheduler = None

def iniciar_scheduler():
    """Inicia el servicio de tareas programadas"""
    global scheduler
    if scheduler is None:
        scheduler = SchedulerService(app, db, Venta, SUNATService)
        scheduler.iniciar()

def detener_scheduler():
    """Detiene el scheduler al cerrar la aplicación"""
    global scheduler
    if scheduler:
        scheduler.detener()

atexit.register(detener_scheduler)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validar que sea del dominio @izistoreperu.com
        if not email.endswith('@izistoreperu.com'):
            flash('Solo se permiten usuarios con correo @izistoreperu.com', 'danger')
            return render_template('login.html')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash('Tu cuenta está desactivada', 'danger')
                return render_template('login.html')
            
            login_user(usuario)
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validar dominio
        if not email.endswith('@izistoreperu.com'):
            flash('Solo se permiten usuarios con correo @izistoreperu.com', 'danger')
            return render_template('login.html')
        
        # Verificar si ya existe
        if Usuario.query.filter_by(email=email).first():
            flash('El correo ya está registrado', 'danger')
            return render_template('login.html')
        
        # Crear usuario
        usuario = Usuario(nombre=nombre, email=email, es_admin=True)
        usuario.set_password(password)
        
        db.session.add(usuario)
        db.session.commit()
        
        flash('Usuario registrado exitosamente', 'success')
        return redirect(url_for('login'))
    
    return render_template('login.html')

# ==================== DASHBOARD ====================

@app.route('/dashboard')
@login_required
def dashboard():
    total_ventas = Venta.query.count()
    ventas_pendientes = Venta.query.filter_by(estado='PENDIENTE').count()
    ventas_enviadas = Venta.query.filter_by(estado='ENVIADO').count()
    
    # Últimas ventas
    ultimas_ventas = Venta.query.order_by(Venta.fecha_emision.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         total_ventas=total_ventas,
                         ventas_pendientes=ventas_pendientes,
                         ventas_enviadas=ventas_enviadas,
                         ultimas_ventas=ultimas_ventas)

# ==================== API CONSULTA DNI/RUC ====================

@app.route('/api/buscar-cliente/<tipo>/<numero>')
@login_required
def buscar_cliente(tipo, numero):
    try:
        token = app.config['APISPERU_TOKEN']
        
        if tipo == 'DNI':
            url = f"{app.config['APISPERU_DNI_URL']}/{numero}?token={token}"
        else:
            url = f"{app.config['APISPERU_RUC_URL']}/{numero}?token={token}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar si la respuesta tiene datos válidos
            if tipo == 'DNI' and 'dni' not in data:
                return jsonify({'success': False, 'message': 'DNI no encontrado en RENIEC'}), 404
            
            if tipo == 'RUC' and 'ruc' not in data:
                return jsonify({'success': False, 'message': 'RUC no encontrado en SUNAT'}), 404
            
            # Verificar si el cliente ya existe en nuestra BD
            cliente_existente = Cliente.query.filter_by(numero_documento=numero).first()
            
            if cliente_existente:
                return jsonify({
                    'success': True,
                    'existe': True,
                    'cliente': {
                        'id': cliente_existente.id,
                        'nombre_completo': cliente_existente.nombre_completo,
                        'numero_documento': cliente_existente.numero_documento,
                        'tipo_documento': cliente_existente.tipo_documento
                    }
                })
            else:
                # Guardar nuevo cliente
                if tipo == 'DNI':
                    cliente = Cliente(
                        tipo_documento='DNI',
                        numero_documento=data['dni'],
                        nombres=data['nombres'],
                        apellido_paterno=data['apellidoPaterno'],
                        apellido_materno=data['apellidoMaterno']
                    )
                else:
                    cliente = Cliente(
                        tipo_documento='RUC',
                        numero_documento=data['ruc'],
                        razon_social=data['razonSocial'],
                        nombres=data['razonSocial'],  # Para RUC, usar razón social como nombre
                        direccion=data.get('direccion', '')
                    )
                
                db.session.add(cliente)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'existe': False,
                    'cliente': {
                        'id': cliente.id,
                        'nombre_completo': cliente.nombre_completo,
                        'numero_documento': cliente.numero_documento,
                        'tipo_documento': cliente.tipo_documento
                    }
                })
        else:
            return jsonify({'success': False, 'message': f'No se encontró información del {tipo}'}), 404
            
    except requests.Timeout:
        return jsonify({'success': False, 'message': 'Tiempo de espera agotado. Intenta nuevamente'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ==================== VENTAS ====================

@app.route('/ventas')
@login_required
def ventas_list():
    ventas = Venta.query.order_by(Venta.fecha_emision.desc()).all()
    return render_template('ventas_list.html', ventas=ventas)

@app.route('/nueva-venta', methods=['GET', 'POST'])
@login_required
def nueva_venta():
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            cliente_id = request.form.get('cliente_id')
            numero_orden = request.form.get('numero_orden')
            items_data = request.form.getlist('items[]')
            
            # Obtener la serie del config
            serie = app.config['SERIE_BOLETA']

            # Calcular correlativo POR SERIE (buscar el máximo correlativo de esta serie específica)
            # SUNAT requiere 8 dígitos para el correlativo
            max_correlativo = db.session.query(db.func.max(db.cast(Venta.correlativo, db.Integer)))\
                .filter(Venta.serie == serie)\
                .scalar()

            correlativo = 1 if not max_correlativo else max_correlativo + 1
            correlativo_str = str(correlativo).zfill(8)  # 8 dígitos según SUNAT

            numero_completo = f"{serie}-{correlativo_str}"
            
            # Crear venta
            venta = Venta(
                numero_orden=numero_orden if numero_orden else None,
                serie=serie,
                correlativo=correlativo_str,
                numero_completo=numero_completo,
                cliente_id=cliente_id,
                vendedor_id=current_user.id,
                subtotal=0,
                total=0,
                estado='PENDIENTE'
            )
            
            db.session.add(venta)
            db.session.flush()
            
            # Agregar items
            total = 0
            items = request.form.getlist('producto_nombre[]')
            cantidades = request.form.getlist('cantidad[]')
            precios = request.form.getlist('precio_unitario[]')
            
            for i in range(len(items)):
                cantidad = float(cantidades[i])
                precio = float(precios[i])
                subtotal = cantidad * precio
                total += subtotal
                
                item = VentaItem(
                    venta_id=venta.id,
                    producto_nombre=items[i],
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=subtotal
                )
                db.session.add(item)
            
            venta.subtotal = total
            venta.total = total
            
            db.session.commit()
            
            flash(f'Venta {numero_completo} creada exitosamente', 'success')
            return redirect(url_for('ventas_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la venta: {str(e)}', 'danger')
    
    return render_template('nueva_venta.html')

# ==================== VER DETALLES DE VENTA ====================

@app.route('/venta/<int:venta_id>')
@login_required
def ver_venta(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    return render_template('detalle_venta.html', venta=venta)

# ==================== GENERAR Y DESCARGAR PDF ====================

@app.route('/venta/<int:venta_id>/pdf')
@login_required
def descargar_pdf(venta_id):
    venta = Venta.query.get_or_404(venta_id)

    # Crear carpeta de comprobantes si no existe
    os.makedirs(app.config['COMPROBANTES_PATH'], exist_ok=True)

    # Nombre del archivo
    # Nombre del archivo según formato: N°orden_N°documento o solo N°documento
    if venta.numero_orden:
    # Formato: 012345678_000001.pdf
     filename = f"{venta.numero_orden}_{venta.correlativo}.pdf"
    else:
    # Formato: BB001_000001.pdf
        filename = f"{venta.numero_completo.replace('-', '_')}.pdf"


    pdf_path = os.path.join(app.config['COMPROBANTES_PATH'], filename)

    # Generar PDF
    if generar_pdf_boleta(venta, pdf_path):
        # Guardar la ruta en la base de datos
        venta.pdf_path = pdf_path
        db.session.commit()

        # Enviar el archivo
        return send_file(pdf_path, as_attachment=True, download_name=filename)
    else:
        flash('Error al generar el PDF', 'danger')
        return redirect(url_for('ventas_list'))

# ==================== ENVÍO A SUNAT ====================

@app.route('/venta/<int:venta_id>/enviar-sunat', methods=['POST'])
@login_required
def enviar_sunat(venta_id):
    """Envía la boleta a SUNAT"""
    venta = Venta.query.get_or_404(venta_id)

    # Verificar que no haya sido enviada antes
    if venta.estado == 'ENVIADO':
        flash('Esta venta ya fue enviada a SUNAT', 'warning')
        return redirect(url_for('ver_venta', venta_id=venta_id))

    try:
        # Inicializar servicio SUNAT
        sunat_service = SUNATService(Config())

        # Procesar venta (generar XML, firmar y enviar)
        resultado = sunat_service.procesar_venta(venta)

        if resultado['success']:
            # Actualizar estado de la venta
            venta.estado = 'ENVIADO'
            venta.fecha_envio_sunat = datetime.now()
            venta.cdr_path = resultado.get('cdr_path')
            venta.mensaje_sunat = resultado.get('message')

            db.session.commit()

            flash(f'Comprobante enviado exitosamente a SUNAT', 'success')
        else:
            flash(f'Error al enviar a SUNAT: {resultado["message"]}', 'danger')

    except Exception as e:
        flash(f'Error al procesar el envío: {str(e)}', 'danger')

    return redirect(url_for('ver_venta', venta_id=venta_id))

@app.route('/venta/<int:venta_id>/xml')
@login_required
def descargar_xml(venta_id):
    """Descarga el XML de la boleta"""
    venta = Venta.query.get_or_404(venta_id)

    if not venta.xml_path or not os.path.exists(venta.xml_path):
        flash('El XML no está disponible', 'warning')
        return redirect(url_for('ver_venta', venta_id=venta_id))

    return send_file(venta.xml_path, as_attachment=True)

@app.route('/venta/<int:venta_id>/cdr')
@login_required
def descargar_cdr(venta_id):
    """Descarga el CDR (Constancia de Recepción) de SUNAT"""
    venta = Venta.query.get_or_404(venta_id)

    if not venta.cdr_path or not os.path.exists(venta.cdr_path):
        flash('El CDR no está disponible', 'warning')
        return redirect(url_for('ver_venta', venta_id=venta_id))

    return send_file(venta.cdr_path, as_attachment=True)

# ==================== ELIMINACIÓN DE VENTAS ====================

@app.route('/venta/<int:venta_id>/eliminar', methods=['DELETE'])
@login_required
def eliminar_venta(venta_id):
    """Elimina una venta individual"""
    try:
        venta = Venta.query.get_or_404(venta_id)

        # No permitir eliminar ventas enviadas a SUNAT
        if venta.estado == 'ENVIADO':
            return jsonify({
                'success': False,
                'message': 'No se puede eliminar una venta enviada a SUNAT'
            }), 400

        numero_completo = venta.numero_completo

        # Eliminar archivos asociados
        if venta.pdf_path and os.path.exists(venta.pdf_path):
            os.remove(venta.pdf_path)
        if venta.xml_path and os.path.exists(venta.xml_path):
            os.remove(venta.xml_path)

        # Eliminar venta (los items se eliminan en cascada)
        db.session.delete(venta)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Venta {numero_completo} eliminada exitosamente'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al eliminar la venta: {str(e)}'
        }), 500

@app.route('/ventas/eliminar-lote', methods=['DELETE'])
@login_required
def eliminar_lote():
    """Elimina múltiples ventas"""
    try:
        data = request.get_json()
        venta_ids = data.get('venta_ids', [])

        if not venta_ids:
            return jsonify({
                'success': False,
                'message': 'No se seleccionaron ventas'
            }), 400

        eliminadas = 0
        errores = []

        for venta_id in venta_ids:
            try:
                venta = Venta.query.get(venta_id)
                if not venta:
                    continue

                # No eliminar ventas enviadas a SUNAT
                if venta.estado == 'ENVIADO':
                    errores.append(f'{venta.numero_completo} (enviado a SUNAT)')
                    continue

                # Eliminar archivos asociados
                if venta.pdf_path and os.path.exists(venta.pdf_path):
                    os.remove(venta.pdf_path)
                if venta.xml_path and os.path.exists(venta.xml_path):
                    os.remove(venta.xml_path)

                db.session.delete(venta)
                eliminadas += 1

            except Exception as e:
                errores.append(f'Error en venta {venta_id}: {str(e)}')

        db.session.commit()

        mensaje = f'{eliminadas} venta(s) eliminada(s)'
        if errores:
            mensaje += f'. Errores: {", ".join(errores)}'

        return jsonify({
            'success': True,
            'eliminadas': eliminadas,
            'message': mensaje
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al eliminar ventas: {str(e)}'
        }), 500

# ==================== ENVÍO EN LOTE ====================

@app.route('/ventas/enviar-lote', methods=['POST'])
@login_required
def enviar_lote():
    """Envía múltiples ventas a SUNAT"""
    try:
        data = request.get_json()
        venta_ids = data.get('venta_ids', [])

        if not venta_ids:
            return jsonify({
                'success': False,
                'message': 'No se seleccionaron ventas'
            }), 400

        sunat_service = SUNATService(Config())
        enviadas = 0
        errores = []

        for venta_id in venta_ids:
            try:
                venta = Venta.query.get(venta_id)
                if not venta:
                    continue

                # Solo enviar ventas pendientes
                if venta.estado != 'PENDIENTE':
                    continue

                # Procesar venta
                resultado = sunat_service.procesar_venta(venta)

                if resultado['success']:
                    venta.estado = 'ENVIADO'
                    venta.fecha_envio_sunat = datetime.utcnow()
                    venta.cdr_path = resultado.get('cdr_path')
                    venta.mensaje_sunat = resultado.get('message')
                    enviadas += 1
                else:
                    errores.append(f'{venta.numero_completo}: {resultado["message"]}')

            except Exception as e:
                errores.append(f'{venta.numero_completo}: {str(e)}')

        db.session.commit()

        mensaje = f'{enviadas} venta(s) enviada(s)'
        if errores:
            mensaje += f'. Errores: {", ".join(errores[:3])}'  # Mostrar solo 3 primeros errores

        return jsonify({
            'success': True,
            'enviadas': enviadas,
            'message': mensaje
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al enviar ventas: {str(e)}'
        }), 500

# ==================== CONTROL DE SCHEDULER ====================

@app.route('/admin/scheduler/estado')
@login_required
def scheduler_estado():
    """Obtiene el estado del scheduler"""
    global scheduler
    if scheduler:
        estado = scheduler.obtener_estado()
        return jsonify(estado)
    return jsonify({'activo': False})

@app.route('/admin/scheduler/ejecutar-ahora', methods=['POST'])
@login_required
def scheduler_ejecutar_ahora():
    """Ejecuta el envío automático inmediatamente (para pruebas)"""
    global scheduler
    if not scheduler:
        return jsonify({
            'success': False,
            'message': 'El scheduler no está activo'
        }), 400

    try:
        scheduler.ejecutar_ahora()
        return jsonify({
            'success': True,
            'message': 'Envío automático ejecutado exitosamente'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al ejecutar: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Iniciar el scheduler antes de correr la aplicación
    with app.app_context():
        iniciar_scheduler()

    app.run(debug=True, host='0.0.0.0', port=5000)
