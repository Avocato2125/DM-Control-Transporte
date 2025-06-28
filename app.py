# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui' # ¡Asegúrate de que esta clave sea única y segura!

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
            A.id_horario, -- Añadido para edición/copia
            A.id_ruta    -- Añadido para edición/copia
        FROM Asignaciones AS A
        JOIN HorariosSalida AS HS ON A.id_horario = HS.id_horario
        JOIN Rutas AS R ON A.id_ruta = R.id_ruta
        WHERE A.fecha >= ?
        ORDER BY A.fecha, HS.hora_salida
    ''', (datetime.date.today().strftime('%Y-%m-%d'),)).fetchall()
    conn.close()
    return render_template('admin_dashboard.html', asignaciones=asignaciones)

@app.route('/nueva_asignacion', methods=('GET', 'POST'))
def nueva_asignacion():
    conn = get_db_connection()
    
    # Definir el orden personalizado de las rutas
    orden_rutas = [
        'NUEVA ROSITA', 'CLOETE', 'AGUJITA', 'SABINAS', 'BARROTERAN',
        'ESPERANZAS', 'AURA', 'MUZQUIZ', 'PALAU', 'MANANTIALES'
    ]
    
    # Crear una cláusula CASE para el ORDER BY en SQL
    order_case = "CASE nombre "
    for i, ruta_name in enumerate(orden_rutas):
        order_case += f"WHEN '{ruta_name}' THEN {i} "
    order_case += "ELSE 99 END"
    
    # Consultar rutas de la base de datos con el orden personalizado
    rutas = conn.execute(f'SELECT id_ruta, nombre, recorrido FROM Rutas ORDER BY {order_case}, nombre').fetchall()
    
    horarios = conn.execute('SELECT id_horario, hora_salida, dias_semana FROM HorariosSalida ORDER BY hora_salida').fetchall()
    conn.close()

    if request.method == 'POST':
        id_horario = request.form['id_horario']
        id_ruta = request.form['id_ruta']
        numero_camion_manual = request.form.get('numero_camion')
        fecha = request.form['fecha']

        if not id_horario or not id_ruta or not fecha:
            flash('Error: Faltan datos obligatorios para la asignación.', 'error')
        else:
            conn = get_db_connection()
            try:
                conn.execute('INSERT INTO Asignaciones (id_horario, id_ruta, numero_camion_manual, fecha) VALUES (?, ?, ?, ?)',
                            (id_horario, id_ruta, numero_camion_manual, fecha))
                conn.commit()
                flash('Asignación creada exitosamente.', 'success')
                return redirect(url_for('admin_dashboard'))
            except sqlite3.Error as e:
                flash(f'Error al insertar asignación: {e}', 'error')
            finally:
                conn.close()

    return render_template('nueva_asignacion.html', rutas=rutas, horarios=horarios)

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


# NUEVA RUTA: Editar Asignación
@app.route('/editar_asignacion/<int:id_asignacion>', methods=('GET', 'POST'))
def editar_asignacion(id_asignacion):
    conn = get_db_connection()
    asignacion = conn.execute('SELECT * FROM Asignaciones WHERE id_asignacion = ?', (id_asignacion,)).fetchone()

    if asignacion is None:
        flash('Asignación no encontrada.', 'error')
        conn.close()
        return redirect(url_for('admin_dashboard'))

    # Definir el orden personalizado de las rutas (igual que en nueva_asignacion)
    orden_rutas = [
        'NUEVA ROSITA', 'CLOETE', 'AGUJITA', 'SABINAS', 'BARROTERAN',
        'ESPERANZAS', 'AURA', 'MUZQUIZ', 'PALAU', 'MANANTIALES'
    ]
    order_case = "CASE nombre "
    for i, ruta_name in enumerate(orden_rutas):
        order_case += f"WHEN '{ruta_name}' THEN {i} "
    order_case += "ELSE 99 END"
    rutas = conn.execute(f'SELECT id_ruta, nombre, recorrido FROM Rutas ORDER BY {order_case}, nombre').fetchall()
    
    horarios = conn.execute('SELECT id_horario, hora_salida, dias_semana FROM HorariosSalida ORDER BY hora_salida').fetchall()
    conn.close()

    if request.method == 'POST':
        id_horario = request.form['id_horario']
        id_ruta = request.form['id_ruta']
        numero_camion_manual = request.form.get('numero_camion')
        fecha = request.form['fecha']

        if not id_horario or not id_ruta or not fecha:
            flash('Error: Faltan datos obligatorios para la asignación.', 'error')
        else:
            conn = get_db_connection()
            try:
                conn.execute('''
                    UPDATE Asignaciones
                    SET id_horario = ?, id_ruta = ?, numero_camion_manual = ?, fecha = ?
                    WHERE id_asignacion = ?
                ''', (id_horario, id_ruta, numero_camion_manual, fecha, id_asignacion))
                conn.commit()
                flash('Asignación actualizada exitosamente.', 'success')
                return redirect(url_for('admin_dashboard'))
            except sqlite3.Error as e:
                flash(f'Error al actualizar asignación: {e}', 'error')
            finally:
                conn.close()
    
    # Para GET request, renderizar el formulario con los datos existentes
    return render_template('editar_asignacion.html', 
                        asignacion=asignacion, 
                        rutas=rutas, 
                        horarios=horarios)

# NUEVA RUTA: Copiar Asignación
@app.route('/copiar_asignacion/<int:id_asignacion>', methods=('POST',))
def copiar_asignacion(id_asignacion):
    conn = get_db_connection()
    asignacion = conn.execute('SELECT * FROM Asignaciones WHERE id_asignacion = ?', (id_asignacion,)).fetchone()

    if asignacion is None:
        flash('Asignación original no encontrada para copiar.', 'error')
        conn.close()
        return redirect(url_for('admin_dashboard'))

    try:
        # Copiamos la asignación, la fecha podría ser la misma o podrías querer forzarla a hoy
        # Por simplicidad, copiaremos la asignación tal cual, sin cambiar la fecha.
        # Si quieres que la fecha de la copia sea siempre la de hoy, usa datetime.date.today().strftime('%Y-%m-%d')
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
    
    now = datetime.datetime.now()
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
    hora_activa_para_display = None
    fecha_activa_para_display = None
    
    # Lógica para determinar la salida activa (con ventana de 30 minutos)
    for i, salida in enumerate(all_relevant_departures):
        salida_fecha_str = salida['fecha']
        salida_hora_str = salida['hora_salida']
        
        salida_datetime_obj = datetime.datetime.strptime(f"{salida_fecha_str} {salida_hora_str}", '%Y-%m-%d %H:%M')
        
        hora_activacion = salida_datetime_obj - datetime.timedelta(minutes=30)
        
        if now >= hora_activacion:
            if i + 1 == len(all_relevant_departures):
                hora_activa_para_display = salida_hora_str
                fecha_activa_para_display = salida_fecha_str
                break
            else:
                siguiente_salida = all_relevant_departures[i+1]
                siguiente_salida_fecha_str = siguiente_salida['fecha']
                siguiente_salida_hora_str = siguiente_salida['hora_salida']
                siguiente_salida_datetime_obj = datetime.datetime.strptime(f"{siguiente_salida_fecha_str} {siguiente_salida_hora_str}", '%Y-%m-%d %H:%M')
                siguiente_hora_activacion = siguiente_salida_datetime_obj - datetime.timedelta(minutes=30)

                if now < siguiente_hora_activacion:
                    hora_activa_para_display = salida_hora_str
                    fecha_activa_para_display = salida_fecha_str
                    break
        else:
            break 
    
    # Filtrado para "Salidas Programadas Ahora" (AGRUPACIÓN POR RUTA)
    salidas_ahora_agrupadas_por_ruta = defaultdict(lambda: defaultdict(list))
    if hora_activa_para_display and fecha_activa_para_display:
        salidas_ahora_raw = [s for s in all_relevant_departures if 
                        s['fecha'] == fecha_activa_para_display and 
                        s['hora_salida'] == hora_activa_para_display]
        
        for salida in salidas_ahora_raw:
            ruta_nombre = salida['nombre_ruta']
            fecha_hora_key = f"{salida['fecha']} {salida['hora_salida']}" 
            salidas_ahora_agrupadas_por_ruta[ruta_nombre][fecha_hora_key].append(salida)
    
    # Convertir a una lista de diccionarios ordenados por nombre de ruta
    salidas_ahora_para_plantilla = []
    # Definir el orden personalizado de las rutas para el display
    orden_rutas_display = [
        'NUEVA ROSITA', 'CLOETE', 'AGUJITA', 'SABINAS', 'BARROTERAN',
        'ESPERANZAS', 'AURA', 'MUZQUIZ', 'PALAU', 'MANANTIALES'
    ]
    # Mapear rutas a su índice en el orden personalizado
    ruta_orden_map_display = {ruta: i for i, ruta in enumerate(orden_rutas_display)}

    for ruta_nombre, fecha_horas_dict in sorted(salidas_ahora_agrupadas_por_ruta.items(), key=lambda item: ruta_orden_map_display.get(item[0], 999)):
        grupos_por_fecha_hora_ordenados = []
        for fecha_hora_key, salidas_list in sorted(fecha_horas_dict.items()):
            hora_display = salidas_list[0]['hora_salida'] 
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
    
    if hora_activa_para_display and fecha_activa_para_display:
        fecha_hora_activa_completa = datetime.datetime.strptime(f"{fecha_activa_para_display} {hora_activa_para_display}", '%Y-%m-%d %H:%M')
        for salida in all_relevant_departures:
            salida_dt_completa = datetime.datetime.strptime(f"{salida['fecha']} {salida['hora_salida']}", '%Y-%m-%d %H:%M')
            if salida_dt_completa > fecha_hora_activa_completa:
                proximas_salidas_raw.append(salida)
    else:
        proximas_salidas_raw = all_relevant_departures
    
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
            hora_display = salidas_list[0]['hora_salida'] 
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


    return render_template('pantalla_personal.html', 
                        salidas_ahora_agrupadas_por_ruta=salidas_ahora_para_plantilla, 
                        hora_activa_para_display=hora_activa_para_display,
                        fecha_activa_para_display=fecha_activa_para_display, 
                        proximas_salidas_agrupadas_por_ruta=proximas_salidas_para_plantilla, 
                        hora_actual=datetime.datetime.now().strftime('%H:%M:%S'),
                        fecha_actual=datetime.datetime.now().strftime('%d/%m/%Y'))

if __name__ == '__main__':
    app.run(debug=True)