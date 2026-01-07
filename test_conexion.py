#!/usr/bin/env python3
"""
Script de prueba de conexión a MySQL
Verifica que las credenciales en .env sean correctas
"""
import os
import sys
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Cargar variables de entorno
load_dotenv()

# Configuración desde .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'confirmacion_db')
}

print("=" * 60)
print("PRUEBA DE CONEXIÓN A MYSQL")
print("=" * 60)
print(f"\n📋 Configuración cargada desde .env:")
print(f"   Host: {DB_CONFIG['host']}")
print(f"   Port: {DB_CONFIG['port']}")
print(f"   User: {DB_CONFIG['user']}")
print(f"   Password: {'*' * len(DB_CONFIG['password']) if DB_CONFIG['password'] else '(vacío)'}")
print(f"   Database: {DB_CONFIG['database']}")

# Intentar conexión sin especificar BD primero
print(f"\n🔄 Intentando conectar al servidor MySQL...")
try:
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    print("✅ Conexión al servidor MySQL exitosa!")
    
    # Verificar si la base de datos existe
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES LIKE %s", (DB_CONFIG['database'],))
    db_exists = cursor.fetchone()
    
    if db_exists:
        print(f"✅ La base de datos '{DB_CONFIG['database']}' existe!")
        
        # Conectar a la BD específica
        conn.close()
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"✅ Tablas encontradas en '{DB_CONFIG['database']}':")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print(f"⚠️  La base de datos '{DB_CONFIG['database']}' existe pero está vacía.")
            print(f"   Ejecuta: mysql -u {DB_CONFIG['user']} -p{DB_CONFIG['password']} < schema.sql")
        
        cursor.close()
    else:
        print(f"⚠️  La base de datos '{DB_CONFIG['database']}' NO existe!")
        print(f"\n💡 Para crearla, ejecuta:")
        print(f"   mysql -u {DB_CONFIG['user']} -p{DB_CONFIG['password']} < schema.sql")
        print(f"\n   O manualmente:")
        print(f"   mysql -u {DB_CONFIG['user']} -p")
        print(f"   CREATE DATABASE {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"   USE {DB_CONFIG['database']};")
        print(f"   source schema.sql;")
    
    conn.close()
    print("\n" + "=" * 60)
    print("✅ PRUEBA COMPLETADA - Conexión OK")
    print("=" * 60)
    sys.exit(0)
    
except Error as e:
    print(f"\n❌ ERROR DE CONEXIÓN:")
    print(f"   {e}")
    print("\n💡 Posibles soluciones:")
    print("   1. Verifica que MySQL esté corriendo:")
    print("      sudo systemctl status mysql")
    print("   2. Verifica las credenciales en .env")
    print("   3. Verifica que el usuario tenga permisos:")
    print(f"      mysql -u root -p")
    print(f"      GRANT ALL PRIVILEGES ON {DB_CONFIG['database']}.* TO '{DB_CONFIG['user']}'@'localhost';")
    print(f"      FLUSH PRIVILEGES;")
    print("\n" + "=" * 60)
    print("❌ PRUEBA FALLIDA - Error de conexión")
    print("=" * 60)
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERROR INESPERADO: {e}")
    sys.exit(1)
