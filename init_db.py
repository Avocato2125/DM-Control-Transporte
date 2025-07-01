# init_db.py

import os
import psycopg2 # Importa la librería para conectar con PostgreSQL

# Recupera la URL de la base de datos de las variables de entorno
# Railway (o Render) inyectará esta variable automáticamente cuando se conecte tu servicio de PostgreSQL
# El nombre de esta variable suele ser 'DATABASE_URL' por convención.
DATABASE_URL = os.environ.get('DATABASE_URL')

def create_tables():
    """
    Crea las tablas necesarias en la base de datos PostgreSQL.
    Este script está diseñado para ejecutarse una única vez para inicializar el esquema.
    """
    conn = None # Inicializa la conexión a None
    try:
        # Intenta conectar a la base de datos PostgreSQL usando la URL obtenida del entorno
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor() # Crea un cursor para ejecutar comandos SQL

        print("DEBUG: Intentando crear tabla Rutas...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Rutas (
                id_ruta SERIAL PRIMARY KEY, -- SERIAL para auto-incremento de ID en PostgreSQL
                nombre VARCHAR(255) NOT NULL, -- VARCHAR para cadenas de texto, longitud máxima 255
                recorrido TEXT NOT NULL       -- TEXT para cadenas de texto de longitud variable, sin límite específico
            );
        """)
        print("DEBUG: Tabla Rutas creada o ya existente.")

        print("DEBUG: Intentando crear tabla Camiones...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Camiones (
                id_camion SERIAL PRIMARY KEY,
                numero VARCHAR(255) NOT NULL UNIQUE,
                capacidad INTEGER,
                modelo VARCHAR(255)
            );
        """)
        print("DEBUG: Tabla Camiones creada o ya existente.")

        print("DEBUG: Intentando crear tabla HorariosSalida...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS HorariosSalida (
                id_horario SERIAL PRIMARY KEY,
                hora_salida VARCHAR(5) NOT NULL, -- HH:MM, por ejemplo '14:30'
                dias_semana TEXT NOT NULL,       -- Por ejemplo, "Lunes,Martes,Viernes" o "Todos"
                es_especial BOOLEAN DEFAULT FALSE -- BOOLEAN para verdadero/falso (FALSE es el valor por defecto)
            );
        """)
        print("DEBUG: Tabla HorariosSalida creada o ya existente.")

        print("DEBUG: Intentando crear tabla Asignaciones...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Asignaciones (
                id_asignacion SERIAL PRIMARY KEY,
                id_horario INTEGER NOT NULL REFERENCES HorariosSalida(id_horario), -- Clave foránea a HorariosSalida
                id_ruta INTEGER NOT NULL REFERENCES Rutas(id_ruta),               -- Clave foránea a Rutas
                numero_camion_manual VARCHAR(255),                                -- Texto libre para el número de camión
                fecha DATE NOT NULL                                               -- Tipo DATE para almacenar solo la fecha (YYYY-MM-DD)
            );
        """)
        print("DEBUG: Tabla Asignaciones creada o ya existente.")

        conn.commit() # Confirma todos los cambios en la base de datos
        print("Tablas de PostgreSQL creadas exitosamente.")

    except psycopg2.Error as e:
        # Captura errores específicos de psycopg2 (conexión, sintaxis SQL, etc.)
        print(f"ERROR: Falló la conexión o la ejecución SQL en PostgreSQL: {e}")
        print(f"SQLSTATE: {e.pgcode}") # Código de error SQL (ej. 42P07 para tabla ya existe)
        print(f"Detalle: {e.pgerror}") # Mensaje de error detallado de PostgreSQL
    except Exception as e:
        # Captura cualquier otro tipo de error inesperado
        print(f"ERROR: Ocurrió un error inesperado al crear tablas: {e}")
    finally:
        # Asegura que la conexión a la base de datos se cierre siempre
        if conn:
            conn.close()

# Esto asegura que la función create_tables() se ejecute solo cuando el script se llama directamente.
if __name__ == "__main__":
    # Verifica si la variable de entorno DATABASE_URL está configurada.
    # Es crucial que este script se ejecute en un entorno donde esta URL esté disponible.
    if not DATABASE_URL:
        print("\nERROR: La variable de entorno 'DATABASE_URL' no está configurada.")
        print("Este script necesita 'DATABASE_URL' para conectarse a PostgreSQL.")
        print("Asegúrate de ejecutarlo en un entorno de Railway (o Render) donde esta variable sea inyectada.")
        print("En desarrollo local, puedes configurarla manualmente antes de ejecutar el script.")
    else:
        create_tables()