# 🔧 GUÍA DE INTEGRACIÓN CON TU SERVIDOR

Esta guía te ayudará a integrar el sistema de confirmación de asistencia con tu configuración existente.

## 📋 Opciones de Integración

Tienes dos opciones:

### Opción 1: Base de Datos Separada (RECOMENDADA)
Usar una base de datos nueva específica para este sistema.

### Opción 2: Base de Datos Compartida
Usar la misma base de datos `asistenciaqr` que tu otro proyecto.

---

## 🚀 INSTALACIÓN PASO A PASO

### 1. Copiar el Proyecto al Servidor

```bash
# En tu servidor, navega al directorio de aplicaciones
cd /ruta/a/tus/aplicaciones

# Copia la carpeta del proyecto
# (asumiendo que subiste el ZIP)
unzip nuevo-formulario.zip
cd nuevo-formulario
```

### 2. Configurar Variables de Entorno

**He preparado un archivo `.env.usuario` con tu configuración:**

```bash
# Renombra .env.usuario a .env
mv .env.usuario .env

# O copia el contenido:
cp .env.usuario .env
```

**Contenido del .env (ya adaptado a tu configuración):**

```env
FLASK_ENV=development
SECRET_KEY=tu_secreto_superseguro
ADMIN_USER=admin
ADMIN_PASSWORD=admin_fesar
APP_PREFIX=/asistencia_eventos

DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=wavedlizard2115
DB_NAME=fes_aragon_eventos
DB_PORT=3306
```

### 3. Opción A - Base de Datos Separada (Recomendada)

```bash
# Crear nueva base de datos
mysql -u root -pwavedlizard2115 -e "CREATE DATABASE fes_aragon_eventos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Importar el schema
mysql -u root -pwavedlizard2115 fes_aragon_eventos < schema.sql
```

### 3. Opción B - Compartir Base de Datos con QR

Si prefieres usar la misma base de datos `asistenciaqr`:

```bash
# 1. Editar el .env y cambiar:
# DB_NAME=asistenciaqr

# 2. Importar solo las tablas a la BD existente:
mysql -u root -pwavedlizard2115 asistenciaqr < schema.sql
```

**NOTA:** Las tablas se llaman `evento` y `confirmacion_asistencia`, así que NO entrarán en conflicto con tus tablas existentes del sistema QR.

### 4. Instalar Dependencias

```bash
# Si usas un entorno virtual (recomendado):
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias:
pip install -r requirements.txt
```

### 5. Probar Localmente

```bash
# Ejecutar en modo desarrollo:
python app.py

# O con el WSGI (prueba el prefijo):
python wsgi.py
```

**URLs de acceso:**
- Con `APP_PREFIX=/asistencia_eventos`:
  - Público: `http://localhost:5000/asistencia_eventos/`
  - Admin: `http://localhost:5000/asistencia_eventos/admin/login`

---

## 🌐 DESPLIEGUE EN PRODUCCIÓN

### Si usas Gunicorn

```bash
# Instalar gunicorn si no lo tienes:
pip install gunicorn

# Ejecutar en producción:
gunicorn wsgi:application --bind 0.0.0.0:5000 --workers 4 --daemon
```

### Si usas Apache + mod_wsgi

Agrega a tu configuración de Apache:

```apache
WSGIScriptAlias /asistencia_eventos /ruta/a/nuevo-formulario/wsgi.py
WSGIDaemonProcess nuevo-formulario python-path=/ruta/a/nuevo-formulario:/ruta/a/venv/lib/python3.x/site-packages
WSGIProcessGroup nuevo-formulario

<Directory /ruta/a/nuevo-formulario>
    Require all granted
</Directory>
```

### Si usas Nginx + uWSGI

Configuración de uWSGI (`uwsgi.ini`):

```ini
[uwsgi]
module = wsgi:application
master = true
processes = 4
socket = /tmp/nuevo-formulario.sock
chmod-socket = 666
vacuum = true
die-on-term = true
```

Configuración de Nginx:

```nginx
location /asistencia_eventos {
    include uwsgi_params;
    uwsgi_pass unix:/tmp/nuevo-formulario.sock;
}
```

---

## 🔑 CREDENCIALES DE ACCESO

**Panel de Administración:**
- URL: `http://tuservidor.com/asistencia_eventos/admin/login`
- Usuario: `admin`
- Contraseña: `admin_fesar`

**⚠️ IMPORTANTE:** Cambia la contraseña de admin en producción:
```env
ADMIN_PASSWORD=una_contraseña_mucho_mas_segura
```

---

## 📊 CÓMO USAR EL SISTEMA

### 1. Crear el Primer Evento

1. Accede al panel admin: `/asistencia_eventos/admin/login`
2. Completa el formulario "Crear Nuevo Evento":
   - **Slug**: `informe-gestion-2025` (solo minúsculas, números y guiones)
   - **Título**: `Primer Informe de Gestión 2025`
   - **Fechas**: Opcional (puedes agregar fecha inicio/fin)
   - **Lugar**: Opcional (ej: "Auditorio Principal")
   - ✅ **Marcar "Activar este evento"**
3. Clic en "Crear Evento"

### 2. Los Usuarios Podrán Acceder

Una vez el evento esté activo:
- URL pública: `http://tuservidor.com/asistencia_eventos/`
- Se redirige automáticamente al evento activo
- Los usuarios llenan el formulario de confirmación

### 3. Exportar Datos

1. En el panel admin, clic en el ícono 👁 del evento
2. Ver todas las confirmaciones
3. Clic en "Exportar CSV"
4. Se descarga un archivo Excel-compatible con todas las confirmaciones

---

## 🔧 CONFIGURACIONES AVANZADAS

### Cambiar el Prefijo de la Ruta

En el `.env`:
```env
APP_PREFIX=/confirmaciones
# o
APP_PREFIX=/eventos
# o
APP_PREFIX=    # Para montar en la raíz /
```

### Aumentar el Pool de Conexiones

Si tienes muchos usuarios concurrentes:
```env
DB_POOL_SIZE=10
```

### Habilitar/Deshabilitar Debug

```env
FLASK_ENV=production    # Para producción
FLASK_DEBUG=False       # Desactivar debug en producción
```

---

## 📝 DIFERENCIAS CON TU PROYECTO QR

| Aspecto | Sistema QR | Sistema Confirmación |
|---------|-----------|---------------------|
| Base de datos | `asistenciaqr` | `fes_aragon_eventos` (o compartir) |
| Prefijo ruta | `/asistencia_qr` | `/asistencia_eventos` |
| Tablas | (tus tablas QR) | `evento`, `confirmacion_asistencia` |
| Puerto | (tu puerto) | Configurable (5000 por defecto) |

**✅ COMPATIBILIDAD:** Pueden coexistir en el mismo servidor sin problemas.

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Error: "Access denied for user 'root'@'localhost'"

Verifica la contraseña en `.env`:
```env
DB_PASSWORD=wavedlizard2115
```

### Error: "Table 'fes_aragon_eventos.evento' doesn't exist"

Necesitas importar el schema:
```bash
mysql -u root -pwavedlizard2115 fes_aragon_eventos < schema.sql
```

### No aparece el formulario público

1. Verifica que hay un evento activo en el panel admin
2. Revisa los logs de la aplicación
3. Confirma que `APP_PREFIX` esté correcto

### Error 409 - Duplicado

Es el comportamiento esperado. El sistema previene que la misma persona confirme dos veces para el mismo evento. Es una característica de seguridad.

---

## 📞 SIGUIENTE PASO

Una vez instalado:

1. **Crea un evento de prueba** en el panel admin
2. **Actívalo** marcando el checkbox
3. **Accede a la URL pública** y haz una confirmación de prueba
4. **Verifica** que aparece en el panel admin
5. **Exporta el CSV** para confirmar que funciona

¡Listo para producción! 🎉
