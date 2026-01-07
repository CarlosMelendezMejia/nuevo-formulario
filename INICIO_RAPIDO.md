# 🚀 INICIO RÁPIDO - Sistema de Confirmación FES Aragón

## ⚡ Instalación en 5 Pasos

### 1. Crear Base de Datos
```bash
mysql -u root -p < schema.sql
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
```bash
cp .env.example .env
nano .env  # Editar con tus datos
```

**Configuración mínima:**
```env
FLASK_SECRET_KEY=cambiar_por_clave_segura
DB_USER=tu_usuario_mysql
DB_PASSWORD=tu_password_mysql
DB_NAME=fes_aragon_eventos
ADMIN_USER=admin
ADMIN_PASSWORD=cambiar_password_admin
```

### 4. Ejecutar Aplicación
```bash
python app.py
```

### 5. Acceder al Sistema
- **Sitio público**: http://localhost:5000
- **Panel admin**: http://localhost:5000/admin/login

## 📋 Primera Configuración

1. **Login como Admin**:
   - Usuario: el configurado en `ADMIN_USER`
   - Contraseña: la configurada en `ADMIN_PASSWORD`

2. **Crear un Evento**:
   - En el panel, llenar formulario "Crear Nuevo Evento"
   - Slug: `informe-gestion-2025` (solo letras minúsculas, números y guiones)
   - Título: `Primer Informe de Gestión 2025`
   - Marcar "Activar este evento"
   - Clic en "Crear Evento"

3. **Probar el Sistema**:
   - Ir a http://localhost:5000
   - Verás el formulario del evento activo
   - Completar y enviar una confirmación de prueba
   - Volver al panel admin para ver la confirmación registrada

## 🎯 Características Principales

### ✅ Validaciones Automáticas
- Campos obligatorios
- Validación condicional de vehículo
- Normalización de placas (MAYÚSCULAS, sin espacios/guiones)
- Deduplicación por evento + nombre + dependencia

### 📊 Panel de Administración
- Crear/activar/desactivar eventos
- Ver todas las confirmaciones por evento
- Exportar a CSV (compatible con Excel)
- Información de vehículos cuando aplique

### 🎨 Diseño Institucional
- Encabezado obligatorio: "Primer informe de Gestión 2025 Fes Aragón"
- Paleta de colores FES Aragón
- Diseño responsivo con Bootstrap 5

## 🌐 Despliegue en Subruta

Para montar en una subruta (ej: `/eventos`):

```bash
# En .env
APP_PREFIX=eventos

# Ejecutar
python wsgi.py
# o
gunicorn wsgi:application
```

Acceso: `http://tuservidor.com/eventos/`

## 📤 Exportar Datos

1. En el panel admin, seleccionar un evento (ícono 👁)
2. Clic en "Exportar CSV"
3. Se descarga archivo con todas las confirmaciones
4. Formato UTF-8 con BOM (compatible con Excel)

## ⚠️ Notas Importantes

- Solo puede haber **un evento activo** a la vez
- Los **duplicados se detectan** por: evento + nombre + dependencia
- Las **placas se normalizan** automáticamente
- El **sistema usa connection pooling** para mejor rendimiento
- El **panel admin está protegido** por usuario/contraseña

## 🆘 Solución Rápida de Problemas

**No aparece el formulario**:
- Verificar que hay un evento activo en el panel admin
- Revisar que la BD está correcta y accesible

**Error de conexión a BD**:
- Verificar credenciales en `.env`
- Confirmar que MySQL está corriendo
- Revisar que la BD existe: `SHOW DATABASES;`

**Error 409 (duplicado)**:
- Ya existe una confirmación con ese nombre en ese evento
- Es el comportamiento esperado (previene duplicados)

**No se exporta CSV**:
- Verificar que el evento tiene confirmaciones
- El botón solo aparece si hay datos

## 📞 Contacto

Para soporte técnico, contactar al área de sistemas de FES Aragón.

---

**¡Listo para usar!** 🎉
