# insert_data.py

import os
import psycopg2 
import psycopg2.extras 

def get_db_connection():
    """
    Función de conexión a PostgreSQL
    """
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL no configurada")
    
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    conn.autocommit = False
    return conn

def insertar_rutas():
    """
    Inserta las rutas en la base de datos PostgreSQL.
    """
    print("🚀 Iniciando inserción de rutas...")
    
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
            cursor.execute("SELECT id_ruta FROM rutas WHERE nombre = %s AND recorrido = %s", ruta)
            existe = cursor.fetchone()
            if not existe:
                cursor.execute("INSERT INTO rutas (nombre, recorrido) VALUES (%s, %s)", ruta)
                rutas_insertadas += 1
                print(f"✓ Ruta '{ruta[0]} - {ruta[1]}' insertada")

        conn.commit()
        print(f"🎉 {rutas_insertadas} rutas insertadas exitosamente")

    except Exception as e:
        print(f"❌ ERROR al insertar rutas: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("📋 Ejecutando inserción de datos...")
    insertar_rutas()
    print("✅ Proceso completado")