# db_setup.py - Versión PostgreSQL

import os
import psycopg2

def crear_base_datos():
    """
    Crea la base de datos PostgreSQL y las tablas necesarias para el proyecto de transporte.
    """
    # Obtener la URL de la base de datos desde las variables de entorno
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("ERROR: La variable de entorno 'DATABASE_URL' no está configurada.")
        return
    
    conn = None
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("DEBUG: Conexión a PostgreSQL exitosa.")

        # Tabla Rutas
        print("DEBUG: Intentando crear tabla Rutas...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Rutas (
                id_ruta SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                recorrido TEXT NOT NULL
            )
        ''')
        print("DEBUG: Tabla Rutas creada o ya existente.")

        # Tabla Camiones
        print("DEBUG: Intentando crear tabla Camiones...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Camiones (
                id_camion SERIAL PRIMARY KEY,
                numero VARCHAR(255) NOT NULL UNIQUE,
                capacidad INTEGER,
                modelo VARCHAR(255)
            )
        ''')
        print("DEBUG: Tabla Camiones creada o ya existente.")

        # Tabla HorariosSalida
        print("DEBUG: Intentando crear tabla HorariosSalida...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS HorariosSalida (
                id_horario SERIAL PRIMARY KEY,
                hora_salida VARCHAR(5) NOT NULL,
                dias_semana TEXT NOT NULL,
                es_especial BOOLEAN DEFAULT FALSE
            )
        ''')
        print("DEBUG: Tabla HorariosSalida creada o ya existente.")

        # Tabla Asignaciones
        print("DEBUG: Intentando crear tabla Asignaciones...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Asignaciones (
                id_asignacion SERIAL PRIMARY KEY,
                id_horario INTEGER NOT NULL REFERENCES HorariosSalida(id_horario),
                id_ruta INTEGER NOT NULL REFERENCES Rutas(id_ruta),
                numero_camion_manual VARCHAR(255),
                fecha DATE NOT NULL
            )
        ''')
        print("DEBUG: Tabla Asignaciones creada o ya existente.")

        conn.commit()
        print("Base de datos PostgreSQL y tablas creadas exitosamente.")

    except psycopg2.Error as e:
        print(f"ERROR: Falló la conexión o la ejecución SQL en PostgreSQL: {e}")
        if hasattr(e, 'pgcode'):
            print(f"SQLSTATE: {e.pgcode}")
        if hasattr(e, 'pgerror'):
            print(f"Detalle: {e.pgerror}")
    except Exception as e:
        print(f"ERROR: Ocurrió un error inesperado: {e}")
    finally:
        if conn:
            conn.close()

def get_db_connection():
    """
    Función helper para obtener una conexión a la base de datos PostgreSQL.
    Úsala en tu app.py en lugar de sqlite3.connect()
    """
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise Exception("DATABASE_URL no está configurada")
    
    return psycopg2.connect(DATABASE_URL)

if __name__ == "__main__":
    crear_base_datos()