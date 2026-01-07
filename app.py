"""
Sistema de Confirmación de Asistencia - FES Aragón
Aplicación Flask para gestión de eventos y confirmaciones
"""
import os
import csv
import io
import logging
import re
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

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask
app = Flask(__name__)
# Soportar tanto SECRET_KEY como FLASK_SECRET_KEY para compatibilidad
app.secret_key = os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

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

# Pool de conexiones
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="fes_pool",
        pool_size=int(os.getenv('DB_POOL_SIZE', 5)),
        pool_reset_session=True,
        **DB_CONFIG
    )
    logger.info("Pool de conexiones MySQL creado exitosamente")
except MySQLError as e:
    logger.error(f"Error al crear pool de conexiones: {e}")
    connection_pool = None


# Función para obtener conexión del pool
def db_conn():
    """Obtiene una conexión del pool"""
    if not connection_pool:
        raise Exception("Pool de conexiones no disponible")
    try:
        return connection_pool.get_connection()
    except pooling.PoolError as e:
        logger.error(f"Error al obtener conexión del pool: {e}")
        raise


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
        conn = db_conn()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar evento activo más reciente
        cursor.execute("""
            SELECT slug FROM evento 
            WHERE activo = TRUE 
            ORDER BY creado_en DESC 
            LIMIT 1
        """)
        evento = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if evento:
            return redirect(url_for('evento_form', slug=evento['slug']))
        else:
            return render_template('no_event.html')
            
    except Exception as e:
        logger.error(f"Error en index: {e}")
        return render_template('no_event.html')


@app.route('/evento/<slug>')
def evento_form(slug):
    """Formulario de confirmación para un evento específico"""
    try:
        conn = db_conn()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar evento por slug
        cursor.execute("""
            SELECT * FROM evento 
            WHERE slug = %s AND activo = TRUE
        """, (slug,))
        evento = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not evento:
            return render_template('no_event.html'), 404
            
        return render_template('form.html', evento=evento)
        
    except Exception as e:
        logger.error(f"Error al cargar formulario de evento: {e}")
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

        trae_vehiculo = parse_trae_vehiculo(data.get('trae_vehiculo') if isinstance(data, dict) else None)
        if trae_vehiculo is None:
            return jsonify({
                'ok': False,
                'error': 'Debe seleccionar si asistirá con vehículo'
            }), 400

        # Normalizar valor en data para consistencia
        data['trae_vehiculo'] = trae_vehiculo
        
        # Validar campos requeridos
        required_fields = ['id_evento', 'dependencia', 'puesto', 'grado', 'nombre_completo']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'ok': False,
                    'error': f'El campo {field} es obligatorio'
                }), 400
        
        # Validación condicional de vehículo
        if trae_vehiculo:
            vehiculo_fields = ['vehiculo_modelo', 'vehiculo_color', 'vehiculo_placas']
            for field in vehiculo_fields:
                if not data.get(field):
                    return jsonify({
                        'ok': False,
                        'error': f'El campo {field} es obligatorio si trae vehículo'
                    }), 400
        
        # Normalizar placas (mayúsculas, sin espacios ni guiones)
        vehiculo_placas = data.get('vehiculo_placas', '')
        if vehiculo_placas:
            vehiculo_placas = vehiculo_placas.upper().replace(' ', '').replace('-', '')
        
        # Capturar información de la solicitud
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Insertar en base de datos
        conn = db_conn()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO confirmacion_asistencia 
                (id_evento, dependencia, puesto, grado, nombre_completo,
                 trae_vehiculo, vehiculo_modelo, vehiculo_color, vehiculo_placas,
                 ip, user_agent, confirmado_en)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                data['id_evento'],
                data['dependencia'],
                data['puesto'],
                data['grado'],
                data['nombre_completo'],
                trae_vehiculo,
                data.get('vehiculo_modelo') if trae_vehiculo else None,
                data.get('vehiculo_color') if trae_vehiculo else None,
                vehiculo_placas if trae_vehiculo else None,
                ip_address,
                user_agent
            ))

            confirmacion_id = cursor.lastrowid
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Confirmación registrada: {data['nombre_completo']} - Evento ID: {data['id_evento']}")
            
            return jsonify({
                'ok': True,
                'redirect': url_for('success', conf_id=confirmacion_id)
            }), 200
            
        except MySQLError as e:
            cursor.close()
            conn.close()
            
            # Detectar error de duplicado
            if e.errno == 1062:  # Duplicate entry
                return jsonify({
                    'ok': False,
                    'error': 'Esta persona ya tiene una confirmación registrada para este evento'
                }), 409
            else:
                logger.error(f"Error MySQL al insertar confirmación: {e}")
                return jsonify({
                    'ok': False,
                    'error': 'Error al registrar la confirmación. Por favor intente nuevamente.'
                }), 500
                
    except Exception as e:
        logger.error(f"Error en api_confirmacion: {e}")
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
        username = request.form.get('username')
        password = request.form.get('password')
        
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
        conn = db_conn()
        cursor = conn.cursor(dictionary=True)
        
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
        
        cursor.close()
        conn.close()
        
        return render_template('todas_confirmaciones.html',
                             confirmaciones=todas_confirmaciones,
                             total=stats['total'])
        
    except Exception as e:
        logger.error(f"Error al cargar todas las confirmaciones: {e}")
        flash('Error al cargar las confirmaciones', 'danger')
        return redirect(url_for('admin_panel'))


@app.route('/admin')
@admin_required
def admin_panel():
    """Panel de administración"""
    try:
        conn = db_conn()
        cursor = conn.cursor(dictionary=True)
        
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
        
        cursor.close()
        conn.close()
        
        return render_template('admin.html', 
                             eventos=eventos, 
                             confirmaciones=confirmaciones,
                             selected_evento=selected_evento,
                             selected_slug=selected_slug)
        
    except Exception as e:
        logger.error(f"Error en admin_panel: {e}")
        flash('Error al cargar el panel de administración', 'danger')
        return render_template('admin.html', eventos=[], confirmaciones=[])


@app.route('/admin/evento/crear', methods=['POST'])
@admin_required
def crear_evento():
    """Crear nuevo evento"""
    try:
        slug = request.form.get('slug', '').strip()
        titulo = request.form.get('titulo', '').strip()
        fecha_inicio = request.form.get('fecha_inicio') or None
        fecha_fin = request.form.get('fecha_fin') or None
        lugar = request.form.get('lugar', '').strip() or None
        activo = request.form.get('activo') == 'on'
        
        # Validación
        if not slug or not titulo:
            flash('El slug y el título son obligatorios', 'danger')
            return redirect(url_for('admin_panel'))
        
        conn = db_conn()
        cursor = conn.cursor()
        
        # Si se activa este evento, desactivar todos los demás
        if activo:
            cursor.execute("UPDATE evento SET activo = FALSE")
        
        # Insertar evento
        cursor.execute("""
            INSERT INTO evento (slug, titulo, fecha_inicio, fecha_fin, lugar, activo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (slug, titulo, fecha_inicio, fecha_fin, lugar, activo))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Evento "{titulo}" creado exitosamente', 'success')
        logger.info(f"Evento creado: {slug}")
        
    except MySQLError as e:
        if e.errno == 1062:  # Duplicate entry
            flash('Ya existe un evento con ese slug', 'danger')
        else:
            logger.error(f"Error MySQL al crear evento: {e}")
            flash('Error al crear el evento', 'danger')
    except Exception as e:
        logger.error(f"Error al crear evento: {e}")
        flash('Error al crear el evento', 'danger')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/evento/<int:evento_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_evento(evento_id):
    """Editar un evento existente"""
    try:
        conn = db_conn()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM evento WHERE id = %s", (evento_id,))
        evento = cursor.fetchone()

        if not evento:
            cursor.close()
            conn.close()
            flash('Evento no encontrado', 'danger')
            return redirect(url_for('admin_panel'))

        if request.method == 'GET':
            cursor.close()
            conn.close()
            return render_template('editar_evento.html', evento=evento)

        # POST: actualizar
        slug = (request.form.get('slug') or '').strip()
        titulo = (request.form.get('titulo') or '').strip()
        fecha_inicio = request.form.get('fecha_inicio') or None
        fecha_fin = request.form.get('fecha_fin') or None
        lugar = (request.form.get('lugar') or '').strip() or None
        activo = request.form.get('activo') == 'on'

        if not slug or not titulo:
            cursor.close()
            conn.close()
            flash('El slug y el título son obligatorios', 'danger')
            return redirect(url_for('editar_evento', evento_id=evento_id))

        if not re.fullmatch(r'[a-z0-9\-]+', slug):
            cursor.close()
            conn.close()
            flash('Slug inválido. Usa solo minúsculas, números y guiones.', 'danger')
            return redirect(url_for('editar_evento', evento_id=evento_id))

        # Si se marca activo, desactivar todos los demás
        cursor2 = conn.cursor()
        try:
            if activo:
                cursor2.execute("UPDATE evento SET activo = FALSE WHERE id <> %s", (evento_id,))

            cursor2.execute(
                """
                UPDATE evento
                SET slug = %s,
                    titulo = %s,
                    fecha_inicio = %s,
                    fecha_fin = %s,
                    lugar = %s,
                    activo = %s
                WHERE id = %s
                """,
                (slug, titulo, fecha_inicio, fecha_fin, lugar, activo, evento_id)
            )

            conn.commit()

        except MySQLError as e:
            conn.rollback()
            if e.errno == 1062:
                flash('Ya existe un evento con ese slug', 'danger')
                return redirect(url_for('editar_evento', evento_id=evento_id))
            logger.error(f"Error MySQL al editar evento: {e}")
            flash('Error al actualizar el evento', 'danger')
            return redirect(url_for('editar_evento', evento_id=evento_id))
        finally:
            cursor2.close()
            cursor.close()
            conn.close()

        flash('Evento actualizado exitosamente', 'success')
        return redirect(url_for('admin_panel'))

    except Exception as e:
        logger.error(f"Error al editar evento: {e}")
        flash('Error al editar el evento', 'danger')
        return redirect(url_for('admin_panel'))


@app.route('/admin/evento/<int:evento_id>/activar', methods=['POST'])
@admin_required
def activar_evento(evento_id):
    """Activar un evento (desactiva todos los demás)"""
    try:
        conn = db_conn()
        cursor = conn.cursor()
        
        # Desactivar todos
        cursor.execute("UPDATE evento SET activo = FALSE")
        
        # Activar el seleccionado
        cursor.execute("UPDATE evento SET activo = TRUE WHERE id = %s", (evento_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Evento activado exitosamente', 'success')
        
    except Exception as e:
        logger.error(f"Error al activar evento: {e}")
        flash('Error al activar el evento', 'danger')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/evento/<int:evento_id>/desactivar', methods=['POST'])
@admin_required
def desactivar_evento(evento_id):
    """Desactivar un evento"""
    try:
        conn = db_conn()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE evento SET activo = FALSE WHERE id = %s", (evento_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Evento desactivado exitosamente', 'success')
        
    except Exception as e:
        logger.error(f"Error al desactivar evento: {e}")
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
        
        conn = db_conn()
        cursor = conn.cursor(dictionary=True)
        
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
        
        cursor.close()
        conn.close()
        
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            'Slug', 'Título Evento', 'Dependencia', 'Puesto', 'Grado', 
            'Nombre Completo', 'Trae Vehículo', 'Modelo', 'Color', 'Placas',
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
        logger.error(f"Error al exportar CSV: {e}")
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
