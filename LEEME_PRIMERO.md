# ✅ SISTEMA LISTO PARA USAR

## 🎯 Cambios Realizados

✅ **Base de datos**: Configurado para `confirmacion_db`
✅ **Archivo .env**: Ya incluido con tu configuración (password: wavedlizard2115)
✅ **Eliminados**: .env.example y .env.usuario (solo queda .env)
✅ **Script de prueba**: Incluido `test_conexion.py` para verificar la BD

---

## 🚀 INSTALACIÓN EN 3 PASOS

### 1️⃣ Probar Conexión

```bash
cd nuevo-formulario
python3 test_conexion.py
```

**✅ Si sale todo OK:** Continúa al paso 2
**❌ Si hay error:** El script te dirá qué hacer

### 2️⃣ Crear Base de Datos

```bash
mysql -u root -pwavedlizard2115 < schema.sql
```

Esto crea:
- Base de datos: `confirmacion_db`
- Tablas necesarias
- Un evento de ejemplo activo

### 3️⃣ Ejecutar la Aplicación

```bash
pip install -r requirements.txt
python app.py
```

**URLs:**
- 🌐 Público: http://localhost:5000/asistencia_eventos/
- 🔐 Admin: http://localhost:5000/asistencia_eventos/admin/login
  - Usuario: `admin`
  - Password: `admin_fesar`

---

## 📋 Contenido del .env

El archivo `.env` ya está configurado:

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

**No necesitas modificar nada**, pero si quieres cambiar algo (ej: el password de admin), edita `.env`:

```bash
nano .env
```

---

## 🆘 Solución de Problemas

### MySQL no conecta

```bash
# Verifica que MySQL esté corriendo
sudo systemctl status mysql
# o
sudo service mysql status

# Si no está corriendo:
sudo systemctl start mysql
```

### Error "Access denied"

Verifica que el password en `.env` sea correcto:
```env
DB_PASSWORD=wavedlizard2115
```

### Error "Database doesn't exist"

Ejecuta el schema nuevamente:
```bash
mysql -u root -pwavedlizard2115 < schema.sql
```

### Puerto 5000 ya en uso

Busca qué proceso lo usa:
```bash
lsof -i :5000
```

Y mata el proceso o cambia el puerto en `app.py` (última línea).

---

## 📁 Estructura del Proyecto

```
nuevo-formulario/
├── .env                    ← Tu configuración (ya lista)
├── test_conexion.py        ← Script de prueba de BD
├── schema.sql              ← Crea la base de datos
├── app.py                  ← Aplicación principal
├── wsgi.py                 ← Para producción
├── requirements.txt        ← Dependencias
├── INICIO_RAPIDO.md        ← Guía rápida
├── README.md               ← Documentación completa
├── templates/              ← 6 plantillas HTML
└── static/                 ← CSS y JavaScript
```

---

## 🎯 Primer Uso

El schema ya crea un evento de ejemplo activo. Solo:

1. Ejecuta la app: `python app.py`
2. Ve a: http://localhost:5000/asistencia_eventos/
3. Verás el formulario del evento
4. Llena una confirmación de prueba
5. Ve al admin para verla registrada

---

## 🔧 Para Producción

Usa Gunicorn:

```bash
pip install gunicorn
gunicorn wsgi:application --bind 0.0.0.0:5000 --workers 4 --daemon
```

---

**¿Todo funcionó?** 🎉
- Lee `INICIO_RAPIDO.md` para más detalles
- Lee `README.md` para documentación completa
