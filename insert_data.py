# insert_data.py

import sqlite3

def insertar_rutas():
    """
    Inserta los datos de las rutas en la tabla 'Rutas' de la base de datos.
    """
    rutas = [
        ("NUEVA ROSITA", "LIBRAMIENTO SUR - PLAZA CALLE 9"),
        ("NUEVA ROSITA", "MASECA - FUTURA"),
        ("NUEVA ROSITA", "JUNCO"),
        ("NUEVA ROSITA", "ROVIROSA - MARIA"),
        ("NUEVA ROSITA", "AMELIA"),
        ("NUEVA ROSITA", "MURALLA- SANCHEZ GARZA - VADO"),
        ("AGUJITA", "CLOETE"),
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
        ("BARROTERAN", "RANCHERIAS"),
        ("BARROTERAN", "ESPERANZAS"),
        ("BARROTERAN", "AURA"),
        ("MUZQUIZ", "DIRECTO"),
        ("MUZQUIZ", "MISIONES"),
        ("MUZQUIZ", "NOGALERA"),
        ("MUZQUIZ", "PALAU PLAZA - CUCHILLA - SAN JUAN"),
        ("MUZQUIZ", "SANTA MARIA"),
        ("MANANTIALES", "VILLA UNION - LA LUZ - AMAPOLA"),
        ("MANANTIALES", "NAVA - RIO BRAVO"),
        ("MANANTIALES", "ZARAGOZA - MORELOS - ALAMOS"),
        ("MANANTIALES", "ALLENDE"),
    ]

    try:
        conn = sqlite3.connect('transporte.db')
        cursor = conn.cursor()
        for ruta in rutas:
            cursor.execute("SELECT id_ruta FROM Rutas WHERE nombre = ? AND recorrido = ?", ruta)
            existe = cursor.fetchone()
            if not existe:
                cursor.execute("INSERT INTO Rutas (nombre, recorrido) VALUES (?, ?)", ruta)
            else:
                print(f"Ruta '{ruta[0]} - {ruta[1]}' ya existe, saltando inserción.")
        conn.commit()
        print("Rutas insertadas exitosamente o ya existentes.")
    except sqlite3.Error as e:
        print(f"Error al insertar rutas: {e}")
    finally:
        if conn:
            conn.close()

def insertar_horarios():
    """
    Inserta los horarios de salida en la tabla 'HorariosSalida'.
    """
    horarios = [
        ("03:45", "Todos", 0),
        ("05:30", "Martes,Viernes", 1),
        ("07:15", "Todos", 0),
        ("15:15", "Sabado,Domingo", 1),
        ("16:45", "Lunes,Martes,Miercoles,Jueves,Viernes", 1),
        ("19:15", "Todos", 0),
    ]

    try:
        conn = sqlite3.connect('transporte.db')
        cursor = conn.cursor()

        for horario_data in horarios:
            hora, dias, especial = horario_data
            cursor.execute("SELECT id_horario FROM HorariosSalida WHERE hora_salida = ? AND dias_semana = ?", (hora, dias))
            existe = cursor.fetchone()
            if not existe:
                cursor.execute("INSERT INTO HorariosSalida (hora_salida, dias_semana, es_especial) VALUES (?, ?, ?)", horario_data)
            else:
                print(f"Horario '{hora} ({dias})' ya existe, saltando inserción.")

        conn.commit()
        print("Horarios de salida insertados exitosamente o ya existentes.")

    except sqlite3.Error as e:
        print(f"Error al insertar horarios: {e}")
    finally:
        if conn:
            conn.close()

def insertar_camiones():
    """
    Inserta algunos camiones de ejemplo en la tabla 'Camiones'.
    Esta función se mantiene por si la tabla Camiones se usa en el futuro.
    """
    camiones = [
        ("C-001", 40, "Mercedes-Benz"),
        ("C-002", 35, "Volvo"),
        ("C-003", 50, "International"),
        ("C-004", 30, "Kenworth"),
        ("C-005", 45, "Freightliner"),
    ]
    try:
        conn = sqlite3.connect('transporte.db')
        cursor = conn.cursor()
        for camion_data in camiones:
            numero, capacidad, modelo = camion_data
            cursor.execute("SELECT id_camion FROM Camiones WHERE numero = ?", (numero,))
            existe = cursor.fetchone()
            if not existe:
                cursor.execute("INSERT INTO Camiones (numero, capacidad, modelo) VALUES (?, ?, ?)", camion_data)
            else:
                print(f"Camión '{numero}' ya existe, saltando inserción.")
        conn.commit()
        print("Camiones insertados exitosamente o ya existentes.")
    except sqlite3.Error as e:
        print(f"Error al insertar camiones: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    insertar_rutas()
    insertar_horarios()
    insertar_camiones() # Se ejecuta, aunque no se use directamente para asignaciones manuales, por si la tabla Camiones se usa para otros propósitos.