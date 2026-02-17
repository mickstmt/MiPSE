"""
Servicio de tareas programadas para envío automático a SUNAT
Usa APScheduler para ejecutar tareas en horarios específicos
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from config import Config
import pytz
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchedulerService:
    """Servicio de tareas programadas"""

    def __init__(self, app, db, Venta, ElectronicService):
        self.app = app
        self.db = db
        self.Venta = Venta
        self.ElectronicService = ElectronicService
        self.scheduler = BackgroundScheduler()
        self.timezone = pytz.timezone('America/Lima')  # Zona horaria de Perú

    def enviar_pendientes_automatico(self):
        """
        Tarea programada: Envía todas las ventas pendientes a SUNAT
        """
        with self.app.app_context():
            try:
                logger.info("="*60)
                logger.info("INICIO DE ENVÍO AUTOMÁTICO A SUNAT")
                logger.info(f"Hora: {datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("="*60)

                # Obtener ventas pendientes
                ventas_pendientes = self.Venta.query.filter_by(estado='PENDIENTE').all()

                if not ventas_pendientes:
                    logger.info("✓ No hay ventas pendientes para enviar")
                    return

                logger.info(f"📋 Ventas pendientes encontradas: {len(ventas_pendientes)}")

                # Inicializar servicio electrónico (PSE o direct SUNAT)
                service = self.ElectronicService(Config())

                enviadas = 0
                errores = 0

                for venta in ventas_pendientes:
                    try:
                        logger.info(f"⏳ Procesando venta {venta.numero_completo}...")

                        # Procesar venta
                        resultado = service.procesar_venta(venta)

                        if resultado['success']:
                            venta.estado = 'ENVIADO'
                            venta.fecha_envio_sunat = datetime.utcnow()
                            venta.cdr_path = resultado.get('cdr_path')
                            venta.mensaje_sunat = resultado.get('message')
                            enviadas += 1
                            logger.info(f"✓ Venta {venta.numero_completo} enviada exitosamente")
                        else:
                            errores += 1
                            logger.error(f"✗ Error en venta {venta.numero_completo}: {resultado.get('message', 'Error desconocido')}")

                    except Exception as e:
                        errores += 1
                        logger.error(f"✗ Error procesando venta {venta.numero_completo}: {str(e)}")

                # Guardar cambios
                self.db.session.commit()

                logger.info("="*60)
                logger.info(f"RESUMEN DEL ENVÍO AUTOMÁTICO:")
                logger.info(f"  ✓ Enviadas: {enviadas}")
                logger.info(f"  ✗ Errores: {errores}")
                logger.info(f"  📊 Total procesadas: {len(ventas_pendientes)}")
                logger.info("="*60)

            except Exception as e:
                logger.error(f"ERROR CRÍTICO en envío automático: {str(e)}")
                self.db.session.rollback()

    def iniciar(self):
        """Inicia el scheduler con la tarea programada"""
        try:
            # Programar envío automático a las 9:00 PM (21:00) hora Lima
            self.scheduler.add_job(
                func=self.enviar_pendientes_automatico,
                trigger=CronTrigger(hour=21, minute=0, timezone=self.timezone),
                id='envio_automatico_sunat',
                name='Envío automático de comprobantes a SUNAT',
                replace_existing=True
            )

            # Iniciar el scheduler
            self.scheduler.start()

            logger.info("="*60)
            logger.info("🚀 SCHEDULER INICIADO")
            logger.info(f"⏰ Envío automático programado para las 9:00 PM (Lima)")
            logger.info("="*60)

            # Mostrar próxima ejecución
            job = self.scheduler.get_job('envio_automatico_sunat')
            if job:
                proxima = job.next_run_time
                logger.info(f"📅 Próxima ejecución: {proxima.strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            logger.error(f"Error al iniciar el scheduler: {str(e)}")

    def detener(self):
        """Detiene el scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("⏹️  Scheduler detenido")
        except Exception as e:
            logger.error(f"Error al detener el scheduler: {str(e)}")

    def ejecutar_ahora(self):
        """Ejecuta el envío automático inmediatamente (para pruebas)"""
        logger.info("🧪 Ejecutando envío automático de forma manual...")
        self.enviar_pendientes_automatico()

    def obtener_estado(self):
        """Obtiene el estado del scheduler"""
        if self.scheduler.running:
            job = self.scheduler.get_job('envio_automatico_sunat')
            if job:
                return {
                    'activo': True,
                    'proxima_ejecucion': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'zona_horaria': str(self.timezone)
                }
        return {'activo': False}
