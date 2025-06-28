# db_setup.py

import sqlite3

def crear_base_datos():
    """
    Crea la base de datos SQLite y las tablas necesarias para el proyecto de transporte.
    """
    try:
        conn = sqlite3.connect('transporte.db')
        cursor = conn.cursor()

        # Tabla Rutas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Rutas (
                id_ruta INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                recorrido TEXT NOT NULL
            )
        ''')

        # Tabla Camiones (Se mantiene por si en el futuro se quiere una lista predefinida)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Camiones (
                id_camion INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT NOT NULL UNIQUE,
                capacidad INTEGER,
                modelo TEXT
            )
        ''')

        # Tabla HorariosSalida
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS HorariosSalida (
                id_horario INTEGER PRIMARY KEY AUTOINCREMENT,
                hora_salida TEXT NOT NULL, -- Formato HH:MM
                dias_semana TEXT NOT NULL, -- Ej. "Lunes,Martes", "Todos", "Sabado,Domingo"
                es_especial BOOLEAN DEFAULT 0 -- 0 para falso, 1 para verdadero
            )
        ''')

        # Tabla Asignaciones (MODIFICADA: Ahora usa numero_camion_manual TEXT)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Asignaciones (
                id_asignacion INTEGER PRIMARY KEY AUTOINCREMENT,
                id_horario INTEGER NOT NULL,
                id_ruta INTEGER NOT NULL,
                numero_camion_manual TEXT, -- AHORA ES UN CAMPO DE TEXTO, NO NECESITA NOT NULL
                fecha TEXT NOT NULL, -- Formato YYYY-MM-DD
                FOREIGN KEY (id_horario) REFERENCES HorariosSalida(id_horario),
                FOREIGN KEY (id_ruta) REFERENCES Rutas(id_ruta)
                -- Ya no hay FOREIGN KEY a Camiones, ya que el campo es de texto libre
            )
        ''')

        conn.commit()
        print("Base de datos 'transporte.db' y tablas creadas exitosamente.")

    except sqlite3.Error as e:
        print(f"Error al crear la base de datos: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    crear_base_datos()