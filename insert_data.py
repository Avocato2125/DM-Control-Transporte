# insert_data.py

import os
import psycopg2 # Necesario para la conexión
import psycopg2.extras # Puede ser necesario dependiendo de cómo se maneje en get_db_connection
# Importa la función de conexión desde app.py
# Asegúrate de que app.py esté en el mismo nivel de directorio
from app import get_db_connection # ¡IMPORTACIÓN CLAVE!

# Nota: sqlite3 ya no es necesario si solo usas PostgreSQL. Puedes eliminar la línea de importación.
# import sqlite3 

def insertar_rutas():
    """
    Inserta los datos de las rutas en la tabla 'Rutas' de la base de datos PostgreSQL.
    """
    rutas = [
        ("NUEVA ROSITA", "LIBRAMIENTO SUR - PLAZA CALLE 9"),
        ("NUEVA ROSITA", "MASECA - FUTURA"),
        ("NUEVA ROSITA", "JUNCO"),
        ("NUEVA ROSITA", "ROVIROSA - MARIA - AMELIA"),
        ("NUEVA ROSITA", "MURALLA- SANCHEZ GARZA - VADO"),
        ("AGUJITA", "CLOETE"), # Agrupé esta como AGUJITA, pero en tu imagen original CLOETE era una ruta principal. Asegúrate del nombre principal si es diferente.
        ("AGUJITA", "TECNOLOGICO - LOMAS"),
        ("AGUJITA", "AGUJITA - ESTACA"),
        ("SABINAS", "INFONAVIT - SAN ANTONIO"),
        ("SABINAS", "SARABIA - BOLIVAR"),
        ("SABINAS", "CERESO"),
        ("SABINAS", "BIMBO - EJIDO"),
        ("SABINAS", "PANTEON - LA JOYA - MANZANOS"),
        ("SABINAS", "PUERTA NEGRA - SANTO DOMINGO"),
        ("SABINAS", "SIX VIRGENES - VISTA HERMOSA"),
        ("SABINAS", "EXA-OCAMPO-ZARAGOZA"),
        ("BARROTERAN", "GNOSTICOS - VALLE DORADO"), # Corregido a BARROTERAN
        ("BARROTERAN", "TACOS JUNIOR"),
        ("BARROTERAN", "RANCHERIAS"),
        ("BARROTERAN", "ESPERANZAS"), # Asegúrate si este ESPERANZAS es un recorrido de BARROTERAN o una ruta principal. En tu tabla original "ESPERANZAS" era un nombre de ruta principal.
        ("BARROTERAN", "AURA"), # Asegúrate si este AURA es un recorrido de BARROTERAN o una ruta principal. En tu tabla original "AURA" era un nombre de ruta principal.
        ("MUZQUIZ", "DIRECTO"),
        ("MUZQUIZ", "MISIONES"),
        ("MUZQUIZ", "NOGALERA"),
        ("MUZQUIZ", "PALAU PLAZA"),
        ("MUZQUIZ", "CUCHILLA"),
        ("MUZQUIZ", "SAN JUAN"),
        ("MUZQUIZ", "SANTA MARIA"),
        ("MANANTIALES", "VILLA UNION - LA LUZ - AMAPOLA"),
        ("MANANTIALES", "NAVA - RIO BRAVO"),
        ("MANANTIALES", "ZARAGOZA - MORELOS - ALAMOS"),
        ("MANANTIALES", "ALLENDE"),
        # NOTA: He mantenido las rutas como las pasaste. Si "CLOETE", "ESPERANZAS", "AURA",
        # "PALAU PLAZA", "CUCHILLA", "SAN JUAN", "SANTA MARIA" son nombres de RUTAS principales
        # y no RECORRIDOS de otra ruta, necesitarías ajustarlos para que sean ("CLOETE", "CLOETE")
        # o similar, si ese es su recorrido por defecto, o definir un recorrido explícito.
        # Basado en tu imagen original, CLOETE, ESPERANZAS, AURA, PALAU eran Rutas Principales.
        # He asumido que quieres que se inserten como (Nombre_Ruta, Recorrido)
    ]

    conn = None
    try:
        conn = get_db_connection() # Obtiene la conexión a PostgreSQL desde app.py
        cursor = conn.cursor() # Obtiene un cursor para ejecutar consultas

        for ruta in rutas:
            # Lógica para corregir la ruta si estaba mal asignada a SABINAS
            if ruta[0] == "BARROTERAN" and ruta[1] == "GNOSTICOS - VALLE DORADO":
                cursor.execute("SELECT id_ruta FROM Rutas WHERE nombre = %s AND recorrido = %s", ("SABINAS", "GNOSTICOS - VALLE DORADO"))
                if cursor.fetchone():
                    print("DEBUG: Corrigiendo 'GNOSTICOS - VALLE DORADO' de SABINAS a BARROTERAN.")
                    cursor.execute("DELETE FROM Rutas WHERE nombre = %s AND recorrido = %s", ("SABINAS", "GNOSTICOS - VALLE DORADO"))
            
            # Verificar si la ruta ya existe antes de insertarla
            cursor.execute("SELECT id_ruta FROM Rutas WHERE nombre = %s AND recorrido = %s", ruta)
            existe = cursor.fetchone()
            if not existe:
                cursor.execute("INSERT INTO Rutas (nombre, recorrido) VALUES (%s, %s)", ruta)
            else:
                print(f"Ruta '{ruta[0]} - {ruta[1]}' ya existe, saltando inserción.")

        conn.commit()
        print("Rutas insertadas exitosamente o ya existentes.")

    except Exception as e: # Captura cualquier excepción de la base de datos
        print(f"ERROR al insertar rutas: {e}")
    finally:
        if conn:
            conn.close()

def insertar_horarios():
    """
    Inserta los horarios de salida predefinidos en la tabla 'HorariosSalida' de PostgreSQL.
    """
    horarios = [
        ("03:45", "Todos", False), # False para BOOLEAN en PG
        ("05:30", "Martes,Viernes", True), # True para BOOLEAN en PG
        ("07:15", "Todos", False),
        ("15:15", "Sabado,Domingo", True),
        ("16:45", "Lunes,Martes,Miercoles,Jueves,Viernes", True),
        ("19:15", "Todos", False),
    ]

    conn = None
    try:
        conn = get_db_connection() # Obtiene la conexión a PostgreSQL
        cursor = conn.cursor() # Obtiene un cursor

        for horario_data in horarios:
            hora, dias, especial = horario_data
            cursor.execute("SELECT id_horario FROM HorariosSalida WHERE hora_salida = %s AND dias_semana = %s", (hora, dias))
            existe = cursor.fetchone()
            if not existe:
                cursor.execute("INSERT INTO HorariosSalida (hora_salida, dias_semana, es_especial) VALUES (%s, %s, %s)", horario_data)
            else:
                print(f"Horario '{hora} ({dias})' ya existe, saltando inserción.")

        conn.commit()
        print("Horarios de salida insertados exitosamente o ya existentes.")

    except Exception as e:
        print(f"ERROR al insertar horarios: {e}")
    finally:
        if conn:
            conn.close()

def insertar_camiones():
    """
    Inserta algunos camiones de ejemplo en la tabla 'Camiones' de PostgreSQL.
    """
    camiones = [
        ("C-001", 40, "Mercedes-Benz"),
        ("C-002", 35, "Volvo"),
        ("C-003", 50, "International"),
        ("C-004", 30, "Kenworth"),
        ("C-005", 45, "Freightliner"),
    ]
    conn = None
    try:
        conn = get_db_connection() # Obtiene la conexión a PostgreSQL
        cursor = conn.cursor() # Obtiene un cursor
        for camion_data in camiones:
            numero, capacidad, modelo = camion_data
            cursor.execute("SELECT id_camion FROM Camiones WHERE numero = %s", (numero,))
            existe = cursor.fetchone()
            if not existe:
                cursor.execute("INSERT INTO Camiones (numero, capacidad, modelo) VALUES (%s, %s, %s)", camion_data)
            else:
                print(f"Camión '{numero}' ya existe, saltando inserción.")
        conn.commit()
        print("Camiones insertados exitosamente o ya existentes.")
    except Exception as e:
        print(f"ERROR al insertar camiones: {e}")
    finally:
        if conn:
            conn.close()

# Este bloque se ejecuta cuando haces 'python insert_data.py'
if __name__ == "__main__":
    # Asegúrate de que DATABASE_URL esté disponible en el entorno donde se ejecute.
    # En Railway Exec, lo estará. En local, necesitarías configurarla como variable de entorno.
    if not os.environ.get('DATABASE_URL'):
        print("\nERROR: La variable de entorno 'DATABASE_URL' no está configurada.")
        print("Este script necesita 'DATABASE_URL' para conectarse a PostgreSQL.")
        print("Asegúrate de ejecutarlo en un entorno de Railway (o Render) donde esta variable sea inyectada.")
        print("En desarrollo local, puedes configurarla manualmente (ej. 'set DATABASE_URL=...') antes de ejecutar el script.")
    else:
        print("\n--- Ejecutando inserción de datos iniciales en PostgreSQL ---")
        insertar_rutas()
        insertar_horarios()
        insertar_camiones()
        print("--- Inserción de datos iniciales completada ---")