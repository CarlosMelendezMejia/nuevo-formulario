"""
Sistema de Confirmación de Asistencia - FES Aragón
Aplicación Flask para gestión de eventos y confirmaciones
"""
import os
import csv
import io
import logging
from logging.handlers import TimedRotatingFileHandler
import re
from contextlib import contextmanager
from functools import wraps
from datetime import datetime

from flask import (
    Flask, request, render_template, redirect, url_for, 
    jsonify, session, Response, flash
)
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from werkzeug.security import check_password_hash, generate_password_hash

def configure_logging():
    """Configura logging a consola + archivo persistente (rotación diaria)."""
    # Permite controlar por variables de entorno / .env
    level_name = (os.getenv('LOG_LEVEL') or 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_log_dir = os.path.join(base_dir, 'logs')
    log_dir = os.getenv('LOG_DIR') or default_log_dir
    log_file = os.getenv('LOG_FILE') or os.path.join(log_dir, 'app.log')

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    fmt = logging.Formatter(
        '%(asctime)s %(levelname)s pid=%(process)d %(name)s: %(message)s'
    )

    root = logging.getLogger()
    root.setLevel(level)

    # Evitar duplicar handlers si Gunicorn/uWSGI ya configuraron logging
    has_file_handler = any(isinstance(h, TimedRotatingFileHandler) for h in root.handlers)
    if not has_file_handler:
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            backupCount=int(os.getenv('LOG_BACKUP_COUNT', '14')),
            encoding='utf-8',
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)

    has_stream_handler = any(isinstance(h, logging.StreamHandler) for h in root.handlers)
    if not has_stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(fmt)
        root.addHandler(stream_handler)

    # Mantener el nivel de werkzeug alineado
    logging.getLogger('werkzeug').setLevel(level)


# Cargar variables de entorno antes de configurar logging
load_dotenv()

# Configurar logging (archivo + consola)
configure_logging()
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)
# Soportar tanto SECRET_KEY como FLASK_SECRET_KEY para compatibilidad
app.secret_key = os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')


@app.before_request
def log_request_summary():
    """Log de monitoreo: solo rutas relevantes para admin/API."""
    try:
        path = request.path or ''
        if path.startswith('/admin') or path.startswith('/api/'):
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            ua = (request.headers.get('User-Agent') or '')
            if len(ua) > 160:
                ua = ua[:160] + '...'
            logger.info('HTTP %s %s ip=%s', request.method, path, ip)
    except Exception:
        # Nunca romper la request por logging
        pass

# Ubicaciones predefinidas (requeridas para eventos)
PREDEFINED_LOCATIONS = {
    'teatro-jose-vasconcelos': {
        'nombre': 'Teatro José Vasconcelos',
        'lat': 19.476396427168083,
        'lng': -99.04633425890201,
    },
    'duacyd': {
        'nombre': 'Auditorio DUACyD',
        'lat': 19.47446595918309,
        'lng': -99.04368228623203,
    },
    'gimnasio-parquet': {
        'nombre': 'Gimnasio de Parquet',
        'lat': 19.474965205436593,
        'lng': -99.04218644726495,
    },
    'centro-tecnologico-aragon': {
        'nombre': 'Centro Tecnológico Aragón',
        'lat': 19.473643812212256,
        'lng': -99.04651282145399,
    },
}


def list_predefined_locations():
    """Lista de ubicaciones para UI (admin)."""
    return [
        {
            'key': key,
            'nombre': value['nombre'],
            'lat': value['lat'],
            'lng': value['lng'],
        }
        for key, value in PREDEFINED_LOCATIONS.items()
    ]

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'confirmacion_db'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True
}

connection_pool = None


def init_connection_pool():
    """Inicializa el pool una vez por proceso (y deja el error real en logs)."""
    global connection_pool
    if connection_pool is not None:
        return connection_pool

    try:
        pool_size = int(os.getenv('DB_POOL_SIZE', 5))
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="fes_pool",
            pool_size=pool_size,
            pool_reset_session=True,
            **DB_CONFIG
        )
        logger.info(
            "Pool MySQL listo (pool_size=%s host=%s port=%s db=%s user=%s)",
            pool_size,
            DB_CONFIG.get('host'),
            DB_CONFIG.get('port'),
            DB_CONFIG.get('database'),
            DB_CONFIG.get('user'),
        )
        return connection_pool
    except MySQLError:
        logger.exception(
            "Error al crear pool MySQL (host=%s port=%s db=%s user=%s)",
            DB_CONFIG.get('host'),
            DB_CONFIG.get('port'),
            DB_CONFIG.get('database'),
            DB_CONFIG.get('user'),
        )
        connection_pool = None
        return None


# Intento inicial (en arranque); si falla, se reintenta en la primera petición
init_connection_pool()


# Función para obtener conexión del pool
def db_conn():
    """Obtiene una conexión del pool"""
    pool = init_connection_pool()
    if not pool:
        raise Exception("Pool de conexiones no disponible")
    try:
        return pool.get_connection()
    except pooling.PoolError:
        logger.exception("Error al obtener conexión del pool")
        raise


@contextmanager
def db_cursor(dictionary=False):
    """Cursor protegido: siempre cierra cursor y devuelve conexión al pool."""
    conn = None
    cursor = None
    try:
        conn = db_conn()
        cursor = conn.cursor(dictionary=dictionary)
        yield conn, cursor
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                logger.exception("Error al cerrar cursor")
        if conn is not None:
            try:
                conn.close()  # devuelve al pool
            except Exception:
                logger.exception("Error al cerrar conexión")


@contextmanager
def db_transaction(dictionary=False):
    """Transacción protegida: commit/rollback y cierre seguro (pool)."""
    conn = None
    cursor = None
    try:
        conn = db_conn()
        cursor = conn.cursor(dictionary=dictionary)
        yield conn, cursor
        try:
            conn.commit()
        except Exception:
            logger.exception("Error al hacer commit")
            raise
    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                logger.exception("Error al hacer rollback")
        raise
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                logger.exception("Error al cerrar cursor")
        if conn is not None:
            try:
                conn.close()  # devuelve al pool
            except Exception:
                logger.exception("Error al cerrar conexión")


# Decorador para rutas de administrador
def admin_required(f):
    """Decorador para proteger rutas de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Acceso denegado. Por favor inicia sesión.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# RUTAS PÚBLICAS
# ============================================================================

@app.route('/')
def index():
    """Página principal - redirige al evento activo más reciente"""
    try:
        with db_cursor(dictionary=True) as (_, cursor):
            # Buscar evento activo más reciente
            cursor.execute("""
                SELECT slug FROM evento 
                WHERE activo = TRUE 
                ORDER BY creado_en DESC 
                LIMIT 1
            """)
            evento = cursor.fetchone()
        
        if evento:
            return redirect(url_for('evento_form', slug=evento['slug']))
        else:
            return render_template('no_event.html')
            
    except Exception as e:
        logger.exception("Error en index")
        return render_template('no_event.html')


@app.route('/evento/<slug>')
def evento_form(slug):
    """Formulario de confirmación para un evento específico"""
    try:
        with db_cursor(dictionary=True) as (_, cursor):
            # Buscar evento por slug
            cursor.execute("""
                SELECT * FROM evento 
                WHERE slug = %s AND activo = TRUE
            """, (slug,))
            evento = cursor.fetchone()
        
        if not evento:
            return render_template('no_event.html'), 404
            
        return render_template('form.html', evento=evento)
        
    except Exception as e:
        logger.exception("Error al cargar formulario de evento (slug=%s)", slug)
        return render_template('no_event.html'), 500


@app.route('/success')
def success():
    """Página de confirmación exitosa"""
    conf_id = request.args.get('conf_id')
    if conf_id is not None and str(conf_id).isdigit():
        conf_id = int(conf_id)
    else:
        conf_id = None
    return render_template('success.html', conf_id=conf_id)


@app.route('/api/confirmacion', methods=['POST'])
def api_confirmacion():
    """Endpoint para registrar confirmación de asistencia"""
    try:
        class ValidationError(Exception):
            def __init__(self, message, field=None, code=None, meta=None):
                super().__init__(message)
                self.message = message
                self.field = field
                self.code = code
                self.meta = meta or {}

        def normalize_text(value):
            if value is None:
                return None
            text = str(value)
            # Convertir saltos de línea/tabulaciones en espacios y colapsar espacios
            text = re.sub(r"[\r\n\t]+", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text

        def require_text(field, max_len, label=None):
            label = label or field
            value = normalize_text(data.get(field))
            if not value:
                raise ValidationError(f'El campo {label} es obligatorio', field=field, code='required')
            if len(value) > max_len:
                raise ValidationError(
                    f'El campo {label} excede el límite de {max_len} caracteres',
                    field=field,
                    code='max_length',
                    meta={'max': max_len}
                )
            return value

        def optional_text(field, max_len, label=None):
            label = label or field
            value = normalize_text(data.get(field))
            if not value:
                return None
            if len(value) > max_len:
                raise ValidationError(
                    f'El campo {label} excede el límite de {max_len} caracteres',
                    field=field,
                    code='max_length',
                    meta={'max': max_len}
                )
            return value

        EMAIL_REGEX = re.compile(
            r"^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
            r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
            r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$",
            re.IGNORECASE,
        )

        def require_email(field='email', max_len=254, label='correo electrónico'):
            raw = data.get(field)
            if raw is None:
                raise ValidationError(f'El campo {label} es obligatorio', field=field, code='required')
            email = str(raw).strip().lower()
            # Sanitización: eliminar cualquier whitespace (pega con espacios, saltos de línea, etc.)
            email = re.sub(r"\s+", "", email)
            if not email:
                raise ValidationError(f'El campo {label} es obligatorio', field=field, code='required')
            if len(email) > max_len:
                raise ValidationError(
                    f'El campo {label} excede el límite de {max_len} caracteres',
                    field=field,
                    code='max_length',
                    meta={'max': max_len}
                )
            if not EMAIL_REGEX.fullmatch(email):
                raise ValidationError(f'El campo {label} es inválido', field=field, code='invalid')
            return email

        def parse_id_evento(value):
            value = normalize_text(value)
            if not value or not value.isdigit():
                raise ValidationError('El campo id_evento es obligatorio', field='id_evento', code='required')
            evento_id = int(value)
            if evento_id <= 0:
                raise ValidationError('El campo id_evento es inválido', field='id_evento', code='invalid')
            return evento_id

        def parse_trae_vehiculo(value):
            if value is None:
                return None
            if isinstance(value, bool):
                return value
            text = str(value).strip().lower()
            if text in ('true', '1', 'si', 'sí', 'yes', 'on'):
                return True
            if text in ('false', '0', 'no', 'off'):
                return False
            return None

        # Obtener datos del formulario (JSON o form-data)
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        if not isinstance(data, dict):
            return jsonify({'ok': False, 'error': 'Datos inválidos'}), 400

        trae_vehiculo = parse_trae_vehiculo(data.get('trae_vehiculo') if isinstance(data, dict) else None)
        if trae_vehiculo is None:
            return jsonify({
                'ok': False,
                'error': 'Debe seleccionar si asistirá con vehículo',
                'field': 'trae_vehiculo',
                'code': 'required'
            }), 400

        # Normalizar valor en data para consistencia
        data['trae_vehiculo'] = trae_vehiculo

        try:
            id_evento = parse_id_evento(data.get('id_evento'))
            dependencia = require_text('dependencia', 255, 'dependencia')
            puesto = require_text('puesto', 255, 'puesto')
            grado = require_text('grado', 50, 'grado')
            nombre_completo = require_text('nombre_completo', 255, 'nombre_completo')
            email = require_email('email', 254, 'correo electrónico')

            allowed_grados = {'Dr.', 'Dra.', 'Mtro.', 'Mtra.', 'Lic.', 'Ing.', 'Arq.', 'Otro'}
            if grado not in allowed_grados:
                raise ValidationError('El campo grado es inválido', field='grado', code='invalid_choice')

            if grado == 'Otro':
                grado_otro = require_text('grado_otro', 20, 'grado (otro)')
                # Permitir solo letras (incluye acentos), puntos y espacios (abreviado)
                if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ. ]+", grado_otro):
                    raise ValidationError('El campo grado (otro) contiene caracteres inválidos', field='grado_otro', code='invalid_characters')
                grado = grado_otro

            vehiculo_modelo = optional_text('vehiculo_modelo', 100, 'vehiculo_modelo')
            vehiculo_color = optional_text('vehiculo_color', 50, 'vehiculo_color')
            vehiculo_placas_raw = optional_text('vehiculo_placas', 60, 'vehiculo_placas')

            vehiculo_placas = None
            if vehiculo_placas_raw:
                vehiculo_placas = vehiculo_placas_raw.upper().replace(' ', '').replace('-', '')
                if len(vehiculo_placas) > 20:
                    raise ValidationError(
                        'El campo vehiculo_placas excede el límite de 20 caracteres',
                        field='vehiculo_placas',
                        code='max_length',
                        meta={'max': 20}
                    )
                if not re.fullmatch(r"[A-Z0-9]+", vehiculo_placas):
                    raise ValidationError(
                        'El campo vehiculo_placas contiene caracteres inválidos',
                        field='vehiculo_placas',
                        code='invalid_characters'
                    )

            if trae_vehiculo:
                if not vehiculo_modelo:
                    raise ValidationError('El campo vehiculo_modelo es obligatorio si trae vehículo', field='vehiculo_modelo', code='required')
                if not vehiculo_color:
                    raise ValidationError('El campo vehiculo_color es obligatorio si trae vehículo', field='vehiculo_color', code='required')
                if not vehiculo_placas:
                    raise ValidationError('El campo vehiculo_placas es obligatorio si trae vehículo', field='vehiculo_placas', code='required')
            else:
                vehiculo_modelo = None
                vehiculo_color = None
                vehiculo_placas = None

        except ValidationError as ve:
            payload = {'ok': False, 'error': ve.message}
            if ve.field:
                payload['field'] = ve.field
            if ve.code:
                payload['code'] = ve.code
            if ve.meta:
                payload.update(ve.meta)
            return jsonify(payload), 400
        
        # Capturar información de la solicitud
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        try:
            with db_transaction() as (_, cursor):
                cursor.execute("""
                    INSERT INTO confirmacion_asistencia 
                    (id_evento, dependencia, puesto, grado, nombre_completo, email,
                     trae_vehiculo, vehiculo_modelo, vehiculo_color, vehiculo_placas,
                     ip, user_agent, confirmado_en)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (
                    id_evento,
                    dependencia,
                    puesto,
                    grado,
                    nombre_completo,
                    email,
                    trae_vehiculo,
                    vehiculo_modelo,
                    vehiculo_color,
                    vehiculo_placas,
                    ip_address,
                    user_agent
                ))

                confirmacion_id = cursor.lastrowid

            # Evitar PII en logs: registrar IDs y metadatos operativos
            logger.info(
                "Confirmación registrada (confirmacion_id=%s evento_id=%s trae_vehiculo=%s ip=%s)",
                confirmacion_id,
                id_evento,
                trae_vehiculo,
                ip_address,
            )

            return jsonify({
                'ok': True,
                'redirect': url_for('success', conf_id=confirmacion_id)
            }), 200

        except MySQLError as e:
            # Detectar error de duplicado
            if e.errno == 1062:  # Duplicate entry
                logger.info(
                    "Confirmación duplicada (evento_id=%s ip=%s)",
                    id_evento,
                    ip_address,
                )
                return jsonify({
                    'ok': False,
                    'error': 'Esta persona ya tiene una confirmación registrada para este evento'
                }), 409

            logger.exception(
                "Error MySQL al insertar confirmación (evento_id=%s ip=%s)",
                id_evento,
                ip_address,
            )
            return jsonify({
                'ok': False,
                'error': 'Error al registrar la confirmación. Por favor intente nuevamente.'
            }), 500
                
    except Exception:
        logger.exception("Error en api_confirmacion")
        return jsonify({
            'ok': False,
            'error': 'Error interno del servidor'
        }), 500


# ============================================================================
# RUTAS DE ADMINISTRACIÓN
# ============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login de administrador"""
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        
        admin_user = os.getenv('ADMIN_USER', 'admin')
        admin_pass = os.getenv('ADMIN_PASSWORD', 'admin')
        
        if username == admin_user and password == admin_pass:
            session['is_admin'] = True
            session['admin_user'] = username
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """Logout de administrador"""
    session.pop('is_admin', None)
    session.pop('admin_user', None)
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin/todas-confirmaciones')
@admin_required
def ver_todas_confirmaciones():
    """Ver todas las confirmaciones de todos los eventos"""
    try:
        with db_cursor(dictionary=True) as (_, cursor):
            # Obtener todas las confirmaciones con información del evento
            cursor.execute("""
                SELECT 
                    e.titulo as evento_titulo,
                    e.slug as evento_slug,
                    c.*
                FROM confirmacion_asistencia c
                JOIN evento e ON c.id_evento = e.id
                ORDER BY c.confirmado_en DESC
            """)
            todas_confirmaciones = cursor.fetchall()

            # Obtener estadísticas
            cursor.execute("SELECT COUNT(*) as total FROM confirmacion_asistencia")
            stats = cursor.fetchone()
        
        return render_template('todas_confirmaciones.html',
                             confirmaciones=todas_confirmaciones,
                             total=stats['total'])
        
    except Exception as e:
        logger.exception("Error al cargar todas las confirmaciones")
        flash('Error al cargar las confirmaciones', 'danger')
        return redirect(url_for('admin_panel'))


@app.route('/admin')
@admin_required
def admin_panel():
    """Panel de administración"""
    try:
        with db_cursor(dictionary=True) as (_, cursor):
            # Obtener todos los eventos
            cursor.execute("""
                SELECT e.*, 
                       COUNT(c.id) as total_confirmaciones
                FROM evento e
                LEFT JOIN confirmacion_asistencia c ON e.id = c.id_evento
                GROUP BY e.id
                ORDER BY e.creado_en DESC
            """)
            eventos = cursor.fetchall()

            # Obtener confirmaciones si se seleccionó un slug
            confirmaciones = []
            selected_slug = request.args.get('slug')
            selected_evento = None

            if selected_slug:
                cursor.execute("SELECT id, titulo, slug FROM evento WHERE slug = %s", (selected_slug,))
                selected_evento = cursor.fetchone()

                if selected_evento:
                    cursor.execute("""
                        SELECT * FROM confirmacion_asistencia 
                        WHERE id_evento = %s
                        ORDER BY confirmado_en DESC
                    """, (selected_evento['id'],))
                    confirmaciones = cursor.fetchall()
        
        return render_template('admin.html', 
                             eventos=eventos, 
                             confirmaciones=confirmaciones,
                             selected_evento=selected_evento,
                             selected_slug=selected_slug,
                             ubicaciones=list_predefined_locations())
        
    except Exception as e:
        logger.exception("Error en admin_panel")
        flash('Error al cargar el panel de administración', 'danger')
        return render_template('admin.html', eventos=[], confirmaciones=[])


@app.route('/admin/evento/crear', methods=['POST'])
@admin_required
def crear_evento():
    """Crear nuevo evento"""
    try:
        slug = request.form.get('slug', '').strip()
        titulo = request.form.get('titulo', '').strip()
        fecha_recepcion = request.form.get('fecha_recepcion') or None
        fecha_inicio = request.form.get('fecha_inicio') or None
        fecha_fin = request.form.get('fecha_fin') or None
        ubicacion_key = (request.form.get('ubicacion_key') or '').strip()
        activo = request.form.get('activo') == 'on'
        
        # Validación
        if not slug or not titulo:
            flash('El slug y el título son obligatorios', 'danger')
            return redirect(url_for('admin_panel'))

        if not ubicacion_key or ubicacion_key not in PREDEFINED_LOCATIONS:
            flash('Debe seleccionar una ubicación válida para el evento', 'danger')
            return redirect(url_for('admin_panel'))

        ubicacion = PREDEFINED_LOCATIONS[ubicacion_key]
        ubicacion_nombre = ubicacion['nombre']
        ubicacion_lat = ubicacion['lat']
        ubicacion_lng = ubicacion['lng']

        # Mantener lugar para compatibilidad / display legacy
        lugar = ubicacion_nombre
        
        with db_transaction() as (_, cursor):
            # Si se activa este evento, desactivar todos los demás
            if activo:
                cursor.execute("UPDATE evento SET activo = FALSE")

            # Insertar evento
            cursor.execute("""
                INSERT INTO evento (
                    slug, titulo, fecha_recepcion, fecha_inicio, fecha_fin,
                    lugar,
                    ubicacion_key, ubicacion_nombre, ubicacion_lat, ubicacion_lng,
                    activo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                slug, titulo, fecha_recepcion, fecha_inicio, fecha_fin,
                lugar,
                ubicacion_key, ubicacion_nombre, ubicacion_lat, ubicacion_lng,
                activo
            ))

            evento_id = cursor.lastrowid
        
        flash(f'Evento "{titulo}" creado exitosamente', 'success')
        logger.info(
            "Evento creado (evento_id=%s slug=%s activo=%s ubicacion_key=%s)",
            evento_id,
            slug,
            activo,
            ubicacion_key,
        )
        
    except MySQLError as e:
        if e.errno == 1062:  # Duplicate entry
            flash('Ya existe un evento con ese slug', 'danger')
        else:
            logger.exception(
                "Error MySQL al crear evento (slug=%s activo=%s ubicacion_key=%s)",
                slug,
                activo,
                ubicacion_key,
            )
            flash('Error al crear el evento', 'danger')
    except Exception as e:
        logger.exception("Error al crear evento (slug=%s)", slug)
        flash('Error al crear el evento', 'danger')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/evento/<int:evento_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_evento(evento_id):
    """Editar un evento existente"""
    try:
        with db_cursor(dictionary=True) as (_, cursor):
            cursor.execute("SELECT * FROM evento WHERE id = %s", (evento_id,))
            evento = cursor.fetchone()

        if not evento:
            flash('Evento no encontrado', 'danger')
            return redirect(url_for('admin_panel'))

        if request.method == 'GET':
            return render_template('editar_evento.html', evento=evento, ubicaciones=list_predefined_locations())

        # POST: actualizar
        slug = (request.form.get('slug') or '').strip()
        titulo = (request.form.get('titulo') or '').strip()
        fecha_recepcion = request.form.get('fecha_recepcion') or None
        fecha_inicio = request.form.get('fecha_inicio') or None
        fecha_fin = request.form.get('fecha_fin') or None
        ubicacion_key = (request.form.get('ubicacion_key') or '').strip()
        activo = request.form.get('activo') == 'on'

        if not slug or not titulo:
            flash('El slug y el título son obligatorios', 'danger')
            return redirect(url_for('editar_evento', evento_id=evento_id))

        if not re.fullmatch(r'[a-z0-9\-]+', slug):
            flash('Slug inválido. Usa solo minúsculas, números y guiones.', 'danger')
            return redirect(url_for('editar_evento', evento_id=evento_id))

        if not ubicacion_key or ubicacion_key not in PREDEFINED_LOCATIONS:
            flash('Debe seleccionar una ubicación válida para el evento', 'danger')
            return redirect(url_for('editar_evento', evento_id=evento_id))

        ubicacion = PREDEFINED_LOCATIONS[ubicacion_key]
        ubicacion_nombre = ubicacion['nombre']
        ubicacion_lat = ubicacion['lat']
        ubicacion_lng = ubicacion['lng']

        # Mantener lugar para compatibilidad / display legacy
        lugar = ubicacion_nombre

        try:
            with db_transaction() as (_, cursor):
                if activo:
                    cursor.execute("UPDATE evento SET activo = FALSE WHERE id <> %s", (evento_id,))

                cursor.execute(
                    """
                    UPDATE evento
                    SET slug = %s,
                        titulo = %s,
                        fecha_recepcion = %s,
                        fecha_inicio = %s,
                        fecha_fin = %s,
                        lugar = %s,
                        ubicacion_key = %s,
                        ubicacion_nombre = %s,
                        ubicacion_lat = %s,
                        ubicacion_lng = %s,
                        activo = %s
                    WHERE id = %s
                    """,
                    (
                        slug, titulo, fecha_recepcion, fecha_inicio, fecha_fin, lugar,
                        ubicacion_key, ubicacion_nombre, ubicacion_lat, ubicacion_lng,
                        activo, evento_id
                    )
                )

            logger.info(
                "Evento actualizado (evento_id=%s slug=%s activo=%s ubicacion_key=%s)",
                evento_id,
                slug,
                activo,
                ubicacion_key,
            )

        except MySQLError as e:
            if e.errno == 1062:
                flash('Ya existe un evento con ese slug', 'danger')
                return redirect(url_for('editar_evento', evento_id=evento_id))
            logger.exception(
                "Error MySQL al editar evento (evento_id=%s slug=%s)",
                evento_id,
                slug,
            )
            flash('Error al actualizar el evento', 'danger')
            return redirect(url_for('editar_evento', evento_id=evento_id))

        flash('Evento actualizado exitosamente', 'success')
        return redirect(url_for('admin_panel'))

    except Exception as e:
        logger.exception("Error al editar evento (evento_id=%s)", evento_id)
        flash('Error al editar el evento', 'danger')
        return redirect(url_for('admin_panel'))


@app.route('/admin/evento/<int:evento_id>/activar', methods=['POST'])
@admin_required
def activar_evento(evento_id):
    """Activar un evento (desactiva todos los demás)"""
    try:
        with db_transaction() as (_, cursor):
            # Desactivar todos
            cursor.execute("UPDATE evento SET activo = FALSE")

            # Activar el seleccionado
            cursor.execute("UPDATE evento SET activo = TRUE WHERE id = %s", (evento_id,))
        
        flash('Evento activado exitosamente', 'success')
        
    except Exception as e:
        logger.exception("Error al activar evento (evento_id=%s)", evento_id)
        flash('Error al activar el evento', 'danger')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/evento/<int:evento_id>/desactivar', methods=['POST'])
@admin_required
def desactivar_evento(evento_id):
    """Desactivar un evento"""
    try:
        with db_transaction() as (_, cursor):
            cursor.execute("UPDATE evento SET activo = FALSE WHERE id = %s", (evento_id,))
        
        flash('Evento desactivado exitosamente', 'success')
        
    except Exception as e:
        logger.exception("Error al desactivar evento (evento_id=%s)", evento_id)
        flash('Error al desactivar el evento', 'danger')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/export')
@admin_required
def export_csv():
    """Exportar confirmaciones a CSV"""
    try:
        slug = request.args.get('slug')
        if not slug:
            flash('Slug no especificado', 'danger')
            return redirect(url_for('admin_panel'))
        
        with db_cursor(dictionary=True) as (_, cursor):
            # Obtener evento
            cursor.execute("SELECT * FROM evento WHERE slug = %s", (slug,))
            evento = cursor.fetchone()

            if not evento:
                flash('Evento no encontrado', 'danger')
                return redirect(url_for('admin_panel'))

            # Obtener confirmaciones
            cursor.execute("""
                SELECT 
                    e.slug,
                    e.titulo,
                    c.dependencia,
                    c.puesto,
                    c.grado,
                    c.nombre_completo,
                    c.email,
                    c.trae_vehiculo,
                    c.vehiculo_modelo,
                    c.vehiculo_color,
                    c.vehiculo_placas,
                    c.confirmado_en,
                    c.creado_en
                FROM confirmacion_asistencia c
                JOIN evento e ON c.id_evento = e.id
                WHERE c.id_evento = %s
                ORDER BY c.confirmado_en DESC
            """, (evento['id'],))

            confirmaciones = cursor.fetchall()

            logger.info(
                "Export CSV (slug=%s evento_id=%s filas=%s)",
                slug,
                evento['id'],
                len(confirmaciones),
            )
        
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            'Slug', 'Título Evento', 'Dependencia', 'Puesto', 'Grado', 
            'Nombre Completo', 'Correo', 'Trae Vehículo', 'Modelo', 'Color', 'Placas',
            'Confirmado En', 'Creado En'
        ])
        
        # Datos
        for c in confirmaciones:
            writer.writerow([
                c['slug'],
                c['titulo'],
                c['dependencia'],
                c['puesto'],
                c['grado'],
                c['nombre_completo'],
                c.get('email') or '',
                'Sí' if c['trae_vehiculo'] else 'No',
                c['vehiculo_modelo'] or '',
                c['vehiculo_color'] or '',
                c['vehiculo_placas'] or '',
                c['confirmado_en'].strftime('%Y-%m-%d %H:%M:%S') if c['confirmado_en'] else '',
                c['creado_en'].strftime('%Y-%m-%d %H:%M:%S') if c['creado_en'] else ''
            ])
        
        # Preparar respuesta
        output.seek(0)
        
        # Agregar BOM para UTF-8 (para Excel)
        csv_data = '\ufeff' + output.getvalue()
        
        return Response(
            csv_data,
            mimetype='text/csv; charset=utf-8-sig',
            headers={
                'Content-Disposition': f'attachment; filename=confirmaciones_{slug}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
    except Exception as e:
        logger.exception("Error al exportar CSV (slug=%s)", request.args.get('slug'))
        flash('Error al exportar datos', 'danger')
        return redirect(url_for('admin_panel'))


# ============================================================================
# MANEJO DE ERRORES
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """Página de error 404"""
    return render_template('no_event.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """Página de error 500"""
    logger.error(f"Error 500: {e}")
    return render_template('no_event.html'), 500


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )
