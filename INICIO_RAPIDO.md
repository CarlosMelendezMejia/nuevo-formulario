# 🚀 INICIO RÁPIDO - 3 PASOS

## ⚡ Instalación Rápida

### 1️⃣ Probar Conexión a MySQL

```bash
python3 test_conexion.py
```

Si sale ✅ todo OK, continúa al paso 2.
Si sale ❌ error, el script te dirá qué hacer.

### 2️⃣ Crear Base de Datos

```bash
mysql -u root -pwavedlizard2115 < schema.sql
```

Esto creará:
- Base de datos: `confirmacion_db`
- Tabla: `evento`
- Tabla: `confirmacion_asistencia`
- Un evento de ejemplo ya activo

### 3️⃣ Instalar y Ejecutar

```bash
pip install -r requirements.txt
python app.py
```

**¡Listo! Accede a:**
- 🌐 Público: http://localhost:5000/asistencia_eventos/
- 🔐 Admin: http://localhost:5000/asistencia_eventos/admin/login

**Credenciales admin:**
- Usuario: `admin`
- Password: `admin_fesar`

---

## 🎯 Primer Uso

El script ya creó un evento de ejemplo activo. Solo:

1. Ve a: http://localhost:5000/asistencia_eventos/
2. Verás el formulario del evento
3. Llena una confirmación de prueba
4. Ve al admin para verla registrada

---

## 🔧 Si Cambiaste Algo en .env

El archivo `.env` ya tiene tu configuración:

```env
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=wavedlizard2115
DB_NAME=confirmacion_db
APP_PREFIX=/asistencia_eventos
```

Si modificaste algo, vuelve a ejecutar `python test_conexion.py` para verificar.

---

## 🆘 Problemas Comunes

**MySQL no conecta:**
```bash
# Verifica que MySQL esté corriendo
sudo systemctl status mysql
# o
sudo service mysql status
```

**Error "database doesn't exist":**
```bash
# Ejecuta el schema nuevamente
mysql -u root -pwavedlizard2115 < schema.sql
```

**Error "Access denied":**
- Verifica el password en `.env` (línea: `DB_PASSWORD=wavedlizard2115`)

**Puerto ya en uso:**
```bash
# Encuentra qué usa el puerto 5000
lsof -i :5000
# Mata el proceso o cambia el puerto en app.py (última línea)
```

---

## 📱 Producción

Para producción usa Gunicorn:

```bash
pip install gunicorn
gunicorn wsgi:application --bind 0.0.0.0:5000 --workers 4 --daemon
```

---

**¿Todo funcionó?** 🎉 
Lee `README.md` para funcionalidades avanzadas.
