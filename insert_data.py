# insert_data.py

import os
import psycopg2 
import psycopg2.extras 

def get_db_connection():
    """
    Función de conexión a PostgreSQL (copiada de app.py para evitar imports circulares)
    """
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL no configurada para la base de datos PostgreSQL.")
    
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    conn.autocommit = False
    return conn

# --- Funciones de Inserción de Datos ---

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
        ("CLOETE", "CLOETE"),
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
        ("BARROTERAN", "GNOSTICOS - VALLE DORADO"), 
        ("BARROTERAN", "TACOS JUNIOR"),
        ("ESPERANZAS", "RANCHERIAS"),
        ("ESPERANZAS", "ESPERANZAS"),
        ("AURA", "SAN JOSE DE AURA"),
        ("MUZQUIZ", "DIRECTO"),
        ("MUZQUIZ", "MISIONES"),
        ("MUZQUIZ", "NOGALERA"),
        ("PALAU", "PALAU PLAZA"),
        ("PALAU", "CUCHILLA"),
        ("PALAU", "SAN JUAN"),
        ("PALAU", "SANTA MARIA"),
        ("MANANTIALES", "VILLA UNION - LA LUZ - AMAPOLA"),
        ("MANANTIALES", "NAVA - RIO BRAVO"),
        ("MANANTIALES", "ZARAGOZA - MORELOS - ALAMOS"),
        ("MANANTIALES", "ALLENDE"),
    ]

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        rutas_insertadas = 0
        for ruta in rutas:
            # Lógica para corregir la ruta si estaba mal asignada a SABINAS
            if ruta[0] == "BARROTERAN" and ruta[1] == "GNOSTICOS - VALLE DORADO":
                cursor.execute("SELECT id_ruta FROM rutas WHERE nombre = %s AND recorrido = %s", ("SABINAS", "GNOSTICOS - VALLE DORADO"))
                if cursor.fetchone():
                    print("DEBUG: Corrigiendo 'GNOSTICOS - VALLE DORADO' de SABINAS a BARROTERAN.")
                    cursor.execute("DELETE FROM rutas WHERE nombre = %s AND recorrido = %s", ("SABINAS", "GNOSTICOS - VALLE DORADO"))
            
            # Verificar si la ruta ya existe antes de insertarla
            cursor.execute("SELECT id_ruta FROM rutas WHERE nombre = %s AND recorrido = %s", ruta)
            existe = cursor.fetchone()
            if not existe:
                cursor.execute("INSERT INTO rutas (nombre, recorrido) VALUES (%s, %s)", ruta)
                rutas_insertadas += 1
                print(f"✓ Ruta '{ruta[0]} - {ruta[1]}' insertada exitosamente")
            else:
                print(f"⚠ Ruta '{ruta[0]} - {ruta[1]}' ya existe, saltando inserción.")

        conn.commit()
        print(f"\n🎉 {rutas_insertadas} rutas insertadas exitosamente o ya existentes.")

    except Exception as e:
        print(f"ERROR al insertar rutas: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def insertar_horarios():
    """
    Inserta los horarios de salida predefinidos en la tabla 'HorariosSalida' de PostgreSQL.
    """
    horarios = [
        ("03:45", "Todos", False),
        ("05:30", "Martes,Viernes", True),
        ("07:15", "Todos", False),
        ("15:15", "Sabado,Domingo", True),
        ("16:45", "Lunes,Martes,Miercoles,Jueves,Viernes", True),
        ("19:15", "Todos", False),
    ]

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        horarios_insertados = 0
        for horario_data in horarios:
            hora, dias, especial = horario_data
            cursor.execute("SELECT id_horario FROM horariossalida WHERE hora_salida = %s AND dias_semana = %s", (hora, dias))
            existe = cursor.fetchone()
            if not existe:
                cursor.execute("INSERT INTO horariossalida (hora_salida, dias_semana, es_especial) VALUES (%s, %s, %s)", horario_data)
                horarios_insertados += 1
                print(f"✓ Horario '{hora} ({dias})' insertado exitosamente")
            else:
                print(f"⚠ Horario '{hora} ({dias})' ya existe, saltando inserción.")

        conn.commit()
        print(f"\n🎉 {horarios_insertados} horarios de salida insertados exitosamente o ya existentes.")

    except Exception as e:
        print(f"ERROR al insertar horarios: {e}")
        if conn:
            conn.rollback()
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        camiones_insertados = 0
        for camion_data in camiones:
            numero, capacidad, modelo = camion_data
            cursor.execute("SELECT id_camion FROM camiones WHERE numero = %s", (numero,))
            existe = cursor.fetchone()
            if not existe:
                cursor.execute("INSERT INTO camiones (numero, capacidad, modelo) VALUES (%s, %s, %s)", camion_data)
                camiones_insertados += 1
                print(f"✓ Camión '{numero}' insertado exitosamente")
            else:
                print(f"⚠ Camión '{numero}' ya existe, saltando inserción.")
                
        conn.commit()
        print(f"\n🎉 {camiones_insertados} camiones insertados exitosamente o ya existentes.")
        
    except Exception as e:
        print(f"ERROR al insertar camiones: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# Este bloque se ejecuta cuando haces 'python insert_data.py'
if __name__ == "__main__":
    if not os.environ.get('DATABASE_URL'):
        print("\nERROR: La variable de entorno 'DATABASE_URL' no está configurada.")
        print("Este script necesita 'DATABASE_URL' para conectarse a PostgreSQL.")
        print("Asegúrate de ejecutarlo en un entorno de Railway donde esta variable sea inyectada.")
    else:
        print("\n--- Ejecutando inserción de datos iniciales en PostgreSQL ---")
        print("🚀 Insertando rutas...")
        insertar_rutas()
        print("\n🚀 Insertando horarios...")
        insertar_horarios()
        print("\n🚀 Insertando camiones...")
        insertar_camiones()
        print("\n✅ --- Inserción de datos iniciales completada ---")