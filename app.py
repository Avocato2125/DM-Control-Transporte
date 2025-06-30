# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import datetime
from collections import defaultdict
import os
import pytz # Importar pytz

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'una_clave_secreta_por_defecto_para_desarrollo')

# Definir la zona horaria de Monterrey (Central Time)
MONTERREY_TZ = pytz.timezone('America/Monterrey')

# --- Funciones de Conversión de Hora ---
def convert_to_24h(time_str_12h):
    """Convierte una cadena de hora de 12 horas (ej. '3:45 PM') a 24 horas (ej. '15:45')."""
    if not time_str_12h:
        return None
    try:
        # Parsear con formato 12 horas, incluyendo AM/PM
        dt_obj = datetime.datetime.strptime(time_str_12h.strip().upper(), '%I:%M %p')
        return dt_obj.strftime('%H:%M')
    except ValueError:
        # Si no tiene AM/PM, intentar como 24h directamente
        try:
            dt_obj = datetime.datetime.strptime(time_str_12h.strip(), '%H:%M')
            return dt_obj.strftime('%H:%M')
        except ValueError:
            return None # O lanzar un error, o manejar de otra forma

def convert_to_12h(time_str_24h):
    """Convierte una cadena de hora de 24 horas (ej. '15:45') a 12 horas (ej. '03:45 PM')."""
    if not time_str_24h:
        return None
    try:
        dt_obj = datetime.datetime.strptime(time_str_24h, '%H:%M')
        return dt_obj.strftime('%I:%M %p')
    except ValueError:
        return None

# Función de ayuda para conectar a la base de datos
def get_db_connection():
    conn = sqlite3.connect('transporte.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def admin_dashboard():
    conn = get_db_connection()
    asignaciones = conn.execute('''
        SELECT
            A.id_asignacion,
            HS.hora_salida,
            HS.dias_semana,
            R.nombre AS nombre_ruta,
            R.recorrido,
            A.numero_camion_manual,
            A.fecha,
            A.id_horario, 
            A.id_ruta    
        FROM Asignaciones AS A
        JOIN HorariosSalida AS HS ON A.id_horario = HS.id_horario
        JOIN Rutas AS R ON A.id_ruta = R.id_ruta
        WHERE A.fecha >= ?
        ORDER BY A.fecha, HS.hora_salida
    ''', (datetime.date.today().strftime('%Y-%m-%d'),)).fetchall()
    conn.close()

    # Convertir hora_salida a 12h para la visualización en el dashboard
    for asignacion in asignaciones:
        asignacion['hora_salida_12h'] = convert_to_12h(asignacion['hora_salida'])

    return render_template('admin_dashboard.html', asignaciones=asignaciones)

@app.route('/nueva_asignacion', methods=('GET', 'POST'))
def nueva_asignacion():
    conn = get_db_connection()
    
    orden_rutas = [
        'NUEVA ROSITA', 'CLOETE', 'AGUJITA', 'SABINAS', 'BARROTERAN',
        'ESPERANZAS', 'AURA', 'MUZQUIZ', 'PALAU', 'MANANTIALES'
    ]
    order_case = "CASE nombre "
    for i, ruta_name in enumerate(orden_rutas):
        order_case += f"WHEN '{ruta_name}' THEN {i} "
    order_case += "ELSE 99 END"
    rutas = conn.execute(f'SELECT id_ruta, nombre, recorrido FROM Rutas ORDER BY {order_case}, nombre').fetchall()
    
    # Aquí ya no necesitamos los objetos de HorariosSalida de la DB directamente para el select,
    # el usuario ingresará la hora como texto libre.
    # horarios = conn.execute('SELECT id_horario, hora_salida, dias_semana FROM HorariosSalida ORDER BY hora_salida').fetchall()
    conn.close()

    if request.method == 'POST':
        # id_horario ya no se recibe directamente, se usará la hora ingresada
        hora_salida_12h = request.form['hora_salida_libre'] # Nuevo campo de texto
        fecha = request.form['fecha']
        id_ruta = request.form['id_ruta']
        numero_camion_manual = request.form.get('numero_camion')

        # Convertir la hora AM/PM a 24h para buscar o crear el HorarioSalida
        hora_salida_24h = convert_to_24h(hora_salida_12h)

        if not hora_salida_24h or not fecha or not id_ruta:
            flash('Error: Hora, Fecha y Ruta son campos obligatorios y la hora debe ser válida (ej. 3:00 PM).', 'error')
        else:
            conn = get_db_connection()
            try:
                # Buscamos un HorarioSalida existente o lo creamos si no existe
                # Esto es una simplificación: asumimos que todos los horarios libres aplican a "Todos" los días
                # o tendrías que añadir un campo para días aplicables en el formulario de asignación
                cursor = conn.cursor()
                cursor.execute("SELECT id_horario FROM HorariosSalida WHERE hora_salida = ?", (hora_salida_24h,))
                horario_db = cursor.fetchone()

                id_horario = None
                if horario_db:
                    id_horario = horario_db['id_horario']
                else:
                    # Crear nuevo HorarioSalida si no existe. Asumimos "Todos" los días, no especial.
                    cursor.execute("INSERT INTO HorariosSalida (hora_salida, dias_semana, es_especial) VALUES (?, ?, ?)", 
                                (hora_salida_24h, "Todos", 0))
                    conn.commit()
                    id_horario = cursor.lastrowid # Obtener el ID del nuevo horario

                if id_horario:
                    conn.execute('INSERT INTO Asignaciones (id_horario, id_ruta, numero_camion_manual, fecha) VALUES (?, ?, ?, ?)',
                                (id_horario, id_ruta, numero_camion_manual, fecha))
                    conn.commit()
                    flash('Asignación creada exitosamente.', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Error: No se pudo determinar/crear el ID de horario.', 'error')

            except sqlite3.Error as e:
                flash(f'Error al insertar asignación: {e}', 'error')
            finally:
                conn.close()

    # Para GET request, solo pasamos rutas
    return render_template('nueva_asignacion.html', rutas=rutas)

@app.route('/eliminar_asignacion/<int:id_asignacion>', methods=('POST',))
def eliminar_asignacion(id_asignacion):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM Asignaciones WHERE id_asignacion = ?', (id_asignacion,))
        conn.commit()
        flash('Asignación eliminada exitosamente.', 'success')
    except sqlite3.Error as e:
        flash(f'Error al eliminar asignación: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/limpiar_asignaciones', methods=('POST',))
def limpiar_asignaciones():
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM Asignaciones')
        conn.commit()
        flash('Todas las asignaciones han sido eliminadas.', 'success')
    except sqlite3.Error as e:
        flash(f'Error al limpiar asignaciones: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))


# RUTA: Editar Asignación
@app.route('/editar_asignacion/<int:id_asignacion>', methods=('GET', 'POST'))
def editar_asignacion(id_asignacion):
    conn = get_db_connection()
    asignacion = conn.execute('SELECT * FROM Asignaciones WHERE id_asignacion = ?', (id_asignacion,)).fetchone()

    if asignacion is None:
        flash('Asignación no encontrada.', 'error')
        conn.close()
        return redirect(url_for('admin_dashboard'))

    # Convertir hora_salida de la asignación a 12h para pre-llenar el formulario
    asignacion_hora_12h = convert_to_12h(asignacion['id_horario_db_hora_salida']) # Necesitamos la hora de la DB

    # Cargar datos adicionales para los selects (rutas)
    orden_rutas = [
        'NUEVA ROSITA', 'CLOETE', 'AGUJITA', 'SABINAS', 'BARROTERAN',
        'ESPERANZAS', 'AURA', 'MUZQUIZ', 'PALAU', 'MANANTIALES'
    ]
    order_case = "CASE nombre "
    for i, ruta_name in enumerate(orden_rutas):
        order_case += f"WHEN '{ruta_name}' THEN {i} "
    order_case += "ELSE 99 END"
    rutas = conn.execute(f'SELECT id_ruta, nombre, recorrido FROM Rutas ORDER BY {order_case}, nombre').fetchall()
    
    # No necesitamos todos los horarios de la DB para el formulario de edición con texto libre
    # horarios = conn.execute('SELECT id_horario, hora_salida, dias_semana FROM HorariosSalida ORDER BY hora_salida').fetchall()

    # Necesitamos obtener la hora_salida real del HorarioSalida para poder convertirla
    horario_actual_db = conn.execute('SELECT hora_salida FROM HorariosSalida WHERE id_horario = ?', (asignacion['id_horario'],)).fetchone()
    if horario_actual_db:
        asignacion_hora_12h = convert_to_12h(horario_actual_db['hora_salida'])
    else:
        asignacion_hora_12h = "" # Fallback si no se encuentra el horario

    conn.close()

    if request.method == 'POST':
        hora_salida_12h = request.form['hora_salida_libre']
        fecha = request.form['fecha']
        id_ruta = request.form['id_ruta']
        numero_camion_manual = request.form.get('numero_camion')

        hora_salida_24h = convert_to_24h(hora_salida_12h)

        if not hora_salida_24h or not fecha or not id_ruta:
            flash('Error: Hora, Fecha y Ruta son campos obligatorios y la hora debe ser válida (ej. 3:00 PM).', 'error')
        else:
            conn = get_db_connection()
            try:
                # Buscamos o creamos el HorarioSalida para la hora nueva
                cursor = conn.cursor()
                cursor.execute("SELECT id_horario FROM HorariosSalida WHERE hora_salida = ?", (hora_salida_24h,))
                horario_db = cursor.fetchone()

                id_horario_nuevo = None
                if horario_db:
                    id_horario_nuevo = horario_db['id_horario']
                else:
                    cursor.execute("INSERT INTO HorariosSalida (hora_salida, dias_semana, es_especial) VALUES (?, ?, ?)", 
                                (hora_salida_24h, "Todos", 0))
                    conn.commit()
                    id_horario_nuevo = cursor.lastrowid

                if id_horario_nuevo:
                    conn.execute('''
                        UPDATE Asignaciones
                        SET id_horario = ?, id_ruta = ?, numero_camion_manual = ?, fecha = ?
                        WHERE id_asignacion = ?
                    ''', (id_horario_nuevo, id_ruta, numero_camion_manual, fecha, id_asignacion))
                    conn.commit()
                    flash('Asignación actualizada exitosamente.', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Error: No se pudo determinar/crear el ID de horario para la actualización.', 'error')

            except sqlite3.Error as e:
                flash(f'Error al actualizar asignación: {e}', 'error')
            finally:
                conn.close()
    
    return render_template('editar_asignacion.html', 
                        asignacion=asignacion, 
                        rutas=rutas, 
                        asignacion_hora_12h=asignacion_hora_12h) # Pasamos la hora en 12h

# RUTA: Copiar Asignación
@app.route('/copiar_asignacion/<int:id_asignacion>', methods=('POST',))
def copiar_asignacion(id_asignacion):
    conn = get_db_connection()
    asignacion = conn.execute('SELECT * FROM Asignaciones WHERE id_asignacion = ?', (id_asignacion,)).fetchone()

    if asignacion is None:
        flash('Asignación original no encontrada para copiar.', 'error')
        conn.close()
        return redirect(url_for('admin_dashboard'))

    try:
        conn.execute('INSERT INTO Asignaciones (id_horario, id_ruta, numero_camion_manual, fecha) VALUES (?, ?, ?, ?)',
                    (asignacion['id_horario'], asignacion['id_ruta'], asignacion['numero_camion_manual'], asignacion['fecha']))
        conn.commit()
        flash('Asignación copiada exitosamente. Puedes editarla si necesitas cambiar la fecha/hora.', 'success')
    except sqlite3.Error as e:
        flash(f'Error al copiar asignación: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/pantalla')
def pantalla_personal():
    conn = get_db_connection()
    
    # Obtener la hora actual en la zona horaria de Monterrey
    utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    now = utc_now.astimezone(MONTERREY_TZ)
    
    hoy_str = now.strftime('%Y-%m-%d')
    hora_actual_dt = now.time()
    
    # Obtener TODAS las asignaciones para hoy y futuras, ordenadas cronológicamente
    all_relevant_departures = conn.execute('''
        SELECT
            HS.hora_salida,
            HS.dias_semana,
            R.nombre AS nombre_ruta,
            R.recorrido,
            A.numero_camion_manual,
            A.fecha
        FROM Asignaciones AS A
        JOIN HorariosSalida AS HS ON A.id_horario = HS.id_horario
        JOIN Rutas AS R ON A.id_ruta = R.id_ruta
        WHERE A.fecha >= ?
        ORDER BY A.fecha ASC, HS.hora_salida ASC
    ''', (hoy_str,)).fetchall()

    salidas_ahora_raw = []
    hora_activa_para_display_24h = None # Guardamos la 24h para la lógica
    fecha_activa_para_display = None
    
    # Lógica para determinar la salida activa (con ventana de 30 minutos)
    for i, salida in enumerate(all_relevant_departures):
        salida_fecha_str = salida['fecha']
        salida_hora_str = salida['hora_salida'] # Esto ya está en 24h
        
        try:
            # Es importante crear datetime objects con la zona horaria para comparaciones exactas
            salida_datetime_obj = MONTERREY_TZ.localize(datetime.datetime.strptime(f"{salida_fecha_str} {salida_hora_str}", '%Y-%m-%d %H:%M'))
        except ValueError as e:
            print(f"ERROR: No se pudo parsear la fecha/hora de la DB: {salida_fecha_str} {salida_hora_str} - Error: {e}")
            continue

        hora_activacion = salida_datetime_obj - datetime.timedelta(minutes=30)
        
        if now >= hora_activacion:
            if i + 1 == len(all_relevant_departures):
                hora_activa_para_display_24h = salida_hora_str
                fecha_activa_para_display = salida_fecha_str
                break
            else:
                siguiente_salida = all_relevant_departures[i+1]
                siguiente_salida_fecha_str = siguiente_salida['fecha']
                siguiente_salida_hora_str = siguiente_salida['hora_salida']
                
                try:
                    siguiente_salida_datetime_obj = MONTERREY_TZ.localize(datetime.datetime.strptime(f"{siguiente_salida_fecha_str} {siguiente_salida_hora_str}", '%Y-%m-%d %H:%M'))
                except ValueError as e:
                    print(f"ERROR: No se pudo parsear la siguiente fecha/hora: {siguiente_salida_fecha_str} {siguiente_salida_hora_str} - Error: {e}")
                    hora_activa_para_display_24h = salida_hora_str
                    fecha_activa_para_display = salida_fecha_str
                    break

                siguiente_hora_activacion = siguiente_salida_datetime_obj - datetime.timedelta(minutes=30)

                if now < siguiente_hora_activacion:
                    hora_activa_para_display_24h = salida_hora_str
                    fecha_activa_para_display = salida_fecha_str
                    break
        else:
            break 
    
    # Filtrado para "Salidas Programadas Ahora" (AGRUPACIÓN POR RUTA)
    salidas_ahora_agrupadas_por_ruta = defaultdict(lambda: defaultdict(list))
    if hora_activa_para_display_24h and fecha_activa_para_display:
        salidas_ahora_raw = [s for s in all_relevant_departures if 
                        s['fecha'] == fecha_activa_para_display and 
                        s['hora_salida'] == hora_activa_para_display_24h]
        
        for salida in salidas_ahora_raw:
            ruta_nombre = salida['nombre_ruta']
            # Para display, convertimos la hora a 12h
            salida['hora_salida_12h'] = convert_to_12h(salida['hora_salida'])
            fecha_hora_key = f"{salida['fecha']} {salida['hora_salida']}" 
            salidas_ahora_agrupadas_por_ruta[ruta_nombre][fecha_hora_key].append(salida)
    
    salidas_ahora_para_plantilla = []
    orden_rutas_display = [
        'NUEVA ROSITA', 'CLOETE', 'AGUJITA', 'SABINAS', 'BARROTERAN',
        'ESPERANZAS', 'AURA', 'MUZQUIZ', 'PALAU', 'MANANTIALES'
    ]
    ruta_orden_map_display = {ruta: i for i, ruta in enumerate(orden_rutas_display)}

    for ruta_nombre, fecha_horas_dict in sorted(salidas_ahora_agrupadas_por_ruta.items(), key=lambda item: ruta_orden_map_display.get(item[0], 999)):
        grupos_por_fecha_hora_ordenados = []
        for fecha_hora_key, salidas_list in sorted(fecha_horas_dict.items()):
            # La hora ya debería estar convertida en las salidas_list[0]['hora_salida_12h']
            hora_display = salidas_list[0]['hora_salida_12h'] # Usamos la versión 12h para display
            fecha_display = salidas_list[0]['fecha']
            grupos_por_fecha_hora_ordenados.append({
                'fecha': fecha_display, 
                'hora': hora_display,
                'salidas': salidas_list
            })
        salidas_ahora_para_plantilla.append({
            'nombre_ruta': ruta_nombre,
            'grupos_por_fecha_hora': grupos_por_fecha_hora_ordenados 
        })


    # --- Lógica para las PRÓXIMAS SALIDAS (Agrupadas por RUTA y luego por HORA) ---
    proximas_salidas_raw = []
    
    if hora_activa_para_display_24h and fecha_activa_para_display:
        # Aquí, fecha_hora_activa_completa debe ser un datetime object CON ZONA HORARIA
        fecha_hora_activa_completa = MONTERREY_TZ.localize(datetime.datetime.strptime(f"{fecha_activa_para_display} {hora_activa_para_display_24h}", '%Y-%m-%d %H:%M'))
        
        for salida in all_relevant_departures:
            salida_dt_completa = MONTERREY_TZ.localize(datetime.datetime.strptime(f"{salida['fecha']} {salida['hora_salida']}", '%Y-%m-%d %H:%M'))
            if salida_dt_completa > fecha_hora_activa_completa:
                salida['hora_salida_12h'] = convert_to_12h(salida['hora_salida']) # Convertir para display
                proximas_salidas_raw.append(salida)
    else:
        for salida in all_relevant_departures:
            salida['hora_salida_12h'] = convert_to_12h(salida['hora_salida']) # Convertir para display
            proximas_salidas_raw.append(salida)
    
    conn.close()

    proximas_salidas_agrupadas_por_ruta = defaultdict(lambda: defaultdict(list))
    for salida in proximas_salidas_raw:
        ruta_nombre = salida['nombre_ruta']
        fecha_hora_key = f"{salida['fecha']} {salida['hora_salida']}" 
        proximas_salidas_agrupadas_por_ruta[ruta_nombre][fecha_hora_key].append(salida)

    proximas_salidas_para_plantilla = []
    for ruta_nombre, fecha_horas_dict in sorted(proximas_salidas_agrupadas_por_ruta.items(), key=lambda item: ruta_orden_map_display.get(item[0], 999)):
        grupos_por_fecha_hora_ordenados = []
        for fecha_hora_key, salidas_list in sorted(fecha_horas_dict.items()):
            hora_display = salidas_list[0]['hora_salida_12h'] # Usamos la versión 12h para display
            fecha_display = salidas_list[0]['fecha']
            grupos_por_fecha_hora_ordenados.append({
                'fecha': fecha_display, 
                'hora': hora_display,
                'salidas': salidas_list
            })
        proximas_salidas_para_plantilla.append({
            'nombre_ruta': ruta_nombre,
            'grupos_por_fecha_hora': grupos_por_fecha_hora_ordenados 
        })

    # Hora actual para el display
    display_hora_actual = now.strftime('%I:%M:%S %p')
    display_fecha_actual = now.strftime('%d/%m/%Y')


    return render_template('pantalla_personal.html', 
                        salidas_ahora_agrupadas_por_ruta=salidas_ahora_para_plantilla, 
                        hora_activa_para_display_12h=convert_to_12h(hora_activa_para_display_24h) if hora_activa_para_display_24h else None, # Pasamos la hora activa en 12h
                        fecha_activa_para_display=fecha_activa_para_display, 
                        proximas_salidas_agrupadas_por_ruta=proximas_salidas_para_plantilla, 
                        hora_actual=display_hora_actual, # Usamos la hora de Monterrey para display
                        fecha_actual=display_fecha_actual) # Usamos la fecha de Monterrey para display

if __name__ == '__main__':
    app.run()