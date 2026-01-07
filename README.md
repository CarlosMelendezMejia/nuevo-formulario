# Sistema de Confirmación de Asistencia - FES Aragón

Sistema web institucional para la gestión de confirmaciones de asistencia a eventos de la Facultad de Estudios Superiores Aragón.

## 📋 Características

- ✅ Formulario público de confirmación de asistencia
- 🎯 Gestión de eventos con activación/desactivación
- 🚗 Captura opcional de información de vehículo
- 📊 Panel de administración completo
- 📤 Exportación de datos a CSV (con BOM UTF-8 para Excel)
- 🔒 Deduplicación de registros
- 🎨 Diseño institucional con paleta de colores FES Aragón
- 🌐 Soporte para montaje en subruta (APP_PREFIX)

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.8+ con Flask
- **Base de Datos**: MySQL 5.7+
- **Frontend**: Bootstrap 5 + CSS personalizado
- **Templates**: Jinja2
- **Configuración**: python-dotenv

## 📂 Estructura del Proyecto

```
nuevo-formulario/
├── app.py                  # Aplicación Flask principal
├── wsgi.py                 # Configuración WSGI con DispatcherMiddleware
├── schema.sql              # Esquema de base de datos
├── requirements.txt        # Dependencias Python
├── .env.example           # Variables de entorno de ejemplo
├── README.md              # Este archivo
├── templates/             # Templates Jinja2
│   ├── base.html
│   ├── no_event.html
│   ├── form.html
│   ├── success.html
│   ├── admin_login.html
│   └── admin.html
└── static/                # Archivos estáticos
    ├── css/
    │   └── main.css       # Estilos institucionales
    └── js/
        └── form.js        # Lógica del formulario
```

## 🚀 Instalación Local

### 1. Requisitos Previos

- Python 3.8 o superior
- MySQL 5.7 o superior
- pip (gestor de paquetes Python)

### 2. Clonar o Descargar el Proyecto

```bash
cd nuevo-formulario
```

### 3. Crear Entorno Virtual (Recomendado)

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
venv\Scripts\activate
```

### 4. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 7. Crear Base de Datos

```bash
# Ejecutar el schema (creará la BD y las tablas)
mysql -u root -pwavedlizard2115 < schema.sql

# O si prefieres hacerlo manualmente:
mysql -u root -pwavedlizard2115
```

Luego en el prompt de MySQL:
```sql
source schema.sql;
exit;
```

El schema creará:
- Base de datos `confirmacion_db`
- Tablas `evento` y `confirmacion_asistencia`  
- Un evento de ejemplo ya activo

### 5. Configurar Variables de Entorno

El proyecto incluye un archivo `.env` pre-configurado con tus valores:

```env
FLASK_ENV=development
SECRET_KEY=tu_secreto_superseguro
ADMIN_USER=admin
ADMIN_PASSWORD=admin_fesar
APP_PREFIX=/asistencia_eventos

DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=wavedlizard2115
DB_NAME=confirmacion_db
DB_PORT=3306
```

**Si necesitas cambiar algo**, edita el archivo `.env`:
```bash
nano .env
```

### 6. Probar Conexión a MySQL (Recomendado)

Antes de ejecutar la app, verifica que MySQL esté accesible:

```bash
python3 test_conexion.py
```

Este script te dirá si hay problemas de conexión y cómo solucionarlos.

### 8. Ejecutar la Aplicación

```bash
# Modo desarrollo
python app.py

# O usando WSGI (recomendado para producción)
gunicorn wsgi:application --bind 0.0.0.0:5000
```

La aplicación estará disponible en: `http://localhost:5000/asistencia_eventos/`

## 🔐 Acceso al Panel de Administración

1. Navegar a: `http://localhost:5000/asistencia_eventos/admin/login`
2. Credenciales por defecto:
   - Usuario: `admin`
   - Contraseña: `admin_fesar`

**⚠️ IMPORTANTE:** Cambia la contraseña en el archivo `.env` antes de usar en producción.

## 📝 Uso del Sistema

### Para Administradores

1. **Crear un Evento**:
   - Acceder al panel de administración
   - Completar el formulario "Crear Nuevo Evento"
   - Marcar "Activar este evento" para hacerlo público
   - Clic en "Crear Evento"

2. **Gestionar Eventos**:
   - Ver lista de todos los eventos
   - Activar/desactivar eventos (solo uno puede estar activo)
   - Ver número de confirmaciones por evento

3. **Ver Confirmaciones**:
   - Clic en el ícono 👁 junto al evento
   - Ver tabla completa de confirmaciones
   - Información de vehículos cuando aplique

4. **Exportar Datos**:
   - Clic en "Exportar CSV" en el panel o en la lista
   - Se descarga archivo CSV con codificación UTF-8 BOM
   - Compatible con Excel (acentos y caracteres especiales)

### Para Usuarios Finales

1. **Acceder al Formulario**:
   - Ir a la URL raíz: `http://localhost:5000`
   - Se redirige automáticamente al evento activo

2. **Completar Confirmación**:
   - Llenar todos los campos obligatorios
   - Si trae vehículo, marcar checkbox y llenar datos adicionales
   - Clic en "Confirmar Asistencia"

3. **Recibir Confirmación**:
   - Pantalla de éxito con mensaje de confirmación
   - Opción para volver al inicio

## 🌐 Despliegue con Prefijo de Ruta

El sistema soporta montaje en subruta usando la variable `APP_PREFIX`.

### Configuración

En el archivo `.env`:

```env
APP_PREFIX=eventos
```

Esto montará la aplicación en: `http://tuservidor.com/eventos/`

### URLs Resultantes

- Formulario público: `http://tuservidor.com/eventos/`
- Admin login: `http://tuservidor.com/eventos/admin/login`
- API: `http://tuservidor.com/eventos/api/confirmacion`

### Ejemplo con Gunicorn

```bash
# Sin prefijo (raíz)
gunicorn wsgi:application --bind 0.0.0.0:5000

# Con prefijo
APP_PREFIX=eventos gunicorn wsgi:application --bind 0.0.0.0:5000
```

## 🎨 Paleta de Colores Institucional

El sistema utiliza la paleta oficial de FES Aragón:

- **--c1**: `#BF871F` (Dorado principal)
- **--c2**: `#F2BC57` (Dorado claro)
- **--c3**: `#73654D` (Café oscuro)
- **--c4**: `#726C6E` (Gris)

Estos colores están definidos en `/static/css/main.css` y se usan consistentemente en toda la aplicación.

## 🔍 Funcionalidades Destacadas

### Deduplicación Automática

El sistema previene registros duplicados usando la combinación:
- ID del evento
- Nombre completo
- Dependencia

Si se intenta un duplicado, retorna HTTP 409 con mensaje claro.

### Normalización de Datos

- Las placas vehiculares se convierten automáticamente a MAYÚSCULAS
- Se eliminan espacios y guiones de las placas antes de guardar
- Validación condicional: campos de vehículo solo son requeridos si se marca el checkbox

### Connection Pooling

- Pool de conexiones MySQL para mejor rendimiento
- Configuración de tamaño del pool via `DB_POOL_SIZE`
- Manejo robusto de errores de conexión

## 📊 Estructura de Base de Datos

### Tabla: evento

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INT | Identificador único |
| slug | VARCHAR(100) | Identificador URL-friendly |
| titulo | VARCHAR(255) | Título del evento |
| fecha_inicio | DATETIME | Fecha de inicio (opcional) |
| fecha_fin | DATETIME | Fecha de término (opcional) |
| lugar | VARCHAR(255) | Ubicación (opcional) |
| activo | BOOLEAN | Estado del evento |
| creado_en | TIMESTAMP | Fecha de creación |
| actualizado_en | TIMESTAMP | Última actualización |

### Tabla: confirmacion_asistencia

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INT | Identificador único |
| id_evento | INT | FK a evento |
| dependencia | VARCHAR(255) | Dependencia del asistente |
| puesto | VARCHAR(255) | Cargo/puesto |
| grado | VARCHAR(20) | Grado académico |
| nombre_completo | VARCHAR(255) | Nombre sin grado |
| trae_vehiculo | BOOLEAN | Indica si trae vehículo |
| vehiculo_modelo | VARCHAR(100) | Modelo del vehículo |
| vehiculo_color | VARCHAR(50) | Color del vehículo |
| vehiculo_placas | VARCHAR(20) | Placas (normalizadas) |
| ip | VARCHAR(45) | IP del registro |
| user_agent | TEXT | User agent del navegador |
| confirmado_en | TIMESTAMP | Fecha/hora de confirmación |
| creado_en | TIMESTAMP | Fecha de creación |
| actualizado_en | TIMESTAMP | Última actualización |

## 🐛 Solución de Problemas

### Error de Conexión a Base de Datos

```
PoolError: Failed getting connection; pool exhausted
```

**Solución**: Aumentar `DB_POOL_SIZE` en `.env`:

```env
DB_POOL_SIZE=10
```

### Error 404 en rutas con APP_PREFIX

**Causa**: El JavaScript no está usando `window.API_BASE`

**Solución**: Verificar que `form.js` use:
```javascript
const apiUrl = `${window.API_BASE}/api/confirmacion`;
```

### Caracteres especiales mal codificados en CSV

**Solución**: El sistema ya usa UTF-8 con BOM. Verificar que Excel esté configurado para detectar automáticamente la codificación.

## 📄 Licencia

Este proyecto ha sido desarrollado para uso institucional de la FES Aragón - UNAM.

## 👥 Soporte

Para soporte técnico o reportar problemas, contactar al área de sistemas de FES Aragón.

---

**Versión**: 1.0.0  
**Última actualización**: Enero 2025  
**Desarrollado para**: FES Aragón - UNAM
