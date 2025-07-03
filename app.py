# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
from collections import defaultdict
import os
import pytz 
import psycopg2 
import psycopg2.extras 
import logging 

# Configurar logging básico para ver errores en la consola/logs de Railway
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    handlers=[logging.StreamHandler()]) # Directo a la consola de Railway
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'una_clave_secreta_por_defecto_para_desarrollo')

MONTERREY_TZ = pytz.timezone('America/Monterrey')

DATABASE_URL = os.environ.get('DATABASE_URL') 

# --- Funciones de Conversión de Hora ---
def convert_to_24h(time_str_12h):
    if not time_str_12h:
        return None
    try:
        dt_obj = datetime.datetime.strptime(time_str_12h.strip().upper(), '%I:%M %p')
        return dt_obj.strftime('%H:%M')
    except ValueError:
        try:
            dt_obj = datetime.datetime.strptime(time_str_12h.strip(), '%H:%M')
            return dt_obj.strftime('%H:%M')
        except ValueError:
            return None 

def convert_to_12h(time_str_24h):
    if not time_str_24h:
        return None
    try:
        dt_obj = datetime.datetime.strptime(time_str_24h, '%H:%M')
        return dt_obj.strftime('%I:%M %p')
    except ValueError:
        return None

# Función de ayuda para conectar a la base de datos (¡CORRECTA PARA POSTGRESQL!)
# ¡Esta función SOLO devuelve la conexión, NO el cursor!
def get_db_connection():
    if not DATABASE_URL:
        logger.error("ERROR CRÍTICO: La variable de entorno 'DATABASE_URL' no está configurada para la conexión a DB.")
        raise ValueError("DATABASE_URL no configurada para la base de datos PostgreSQL.")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        # NOTA: La configuración de RealDictCursor se hace al CREAR CADA CURSOR en las funciones de ruta
        logger.info("Conexión a la base de datos PostgreSQL exitosa.")
        return conn 
    except Exception as e:
        logger.error(f"ERROR: Falló la conexión a la base de datos PostgreSQL: {e}", exc_info=True)
        raise e 


@app.route('/')
def admin_dashboard():
    conn = None 
    try:
        conn = get_db_connection()
        # ¡CORRECCIÓN CLAVE! Crear un cursor con RealDictCursor para los SELECT
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) 

        asignaciones_raw = cursor.execute('''
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
            FROM asignaciones AS A
            JOIN horariossalida AS HS ON A.id_horario = HS.id_horario
            JOIN rutas AS R ON A.id_ruta = R.id_ruta
            WHERE A.fecha >= %s 
            ORDER BY A.fecha, HS.hora_salida
        ''', (datetime.date.today().strftime('%Y-%m-%d'),)).fetchall()
        
        conn.close() 

        asignaciones = []
        for asignacion_row in asignaciones_raw:
            asignacion_dict = asignacion_row 
            asignacion_dict['hora_salida_12h'] = convert_to_12h(asignacion_dict['hora_salida'])
            asignaciones.append(asignacion_dict)
        
        return render_template('admin_dashboard.html', asignaciones=asignaciones)
    except Exception as e:
        logger.error(f"Error al cargar admin_dashboard: {e}", exc_info=True)
        flash(f"Error al cargar el panel de administración: {e}. ¿Base de datos inicializada?", 'error')
        if 'conn' in locals() and conn: conn.close()
        return render_template('admin_dashboard.html', asignaciones=[]) 


@app.route('/nueva_asignacion', methods=('GET', 'POST'))
def nueva_asignacion():
    conn = None 
    rutas = [] 
    try: 
        conn = get_db_connection()
        # ¡CORRECCIÓN CLAVE! Crear un cursor con RealDictCursor para los SELECT
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) 
        
        orden_rutas = [
            'NUEVA ROSITA', 'CLOETE', 'AGUJITA', 'SABINAS', 'BARROTERAN',
            'ESPERANZAS', 'AURA', 'MUZQUIZ', 'PALAU', 'MANANTIALES'
        ]
        order_case = "CASE nombre "
        for i, ruta_name in enumerate(orden_rutas):
            order_case += f"WHEN '{ruta_name}' THEN {i} "
        order_case += "ELSE 99 END"
        rutas = cursor.execute(f'SELECT id_ruta, nombre, recorrido FROM rutas ORDER BY {order_case}, nombre').fetchall()
        
    except Exception as e:
        logger.error(f"Error al cargar formulario de nueva asignación (GET): {e}", exc_info=True)
        flash(f"Error al cargar rutas/horarios: {e}. ¿Base de datos inicializada?", 'error')
        rutas = [] 
    finally:
        if conn: conn.close()

    if request.method == 'POST':
        hora_salida_12h_input = request.form['hora_salida_libre'] 
        fecha = request.form['fecha']
        id_ruta = request.form['id_ruta']
        numero_camion_manual = request.form.get('numero_camion')

        hora_salida_24h = convert_to_24h(hora_salida_12h_input)

        if not hora_salida_24h or not fecha or not id_ruta:
            flash('Error: Hora, Fecha y Ruta son campos obligatorios y la hora debe ser válida (ej. 3:00 PM o 15:45).', 'error')
        else:
            conn = None 
            try: 
                conn = get_db_connection()
                # ¡CORRECCIÓN AQUÍ! Obtener un cursor SIN RealDictCursor para operaciones de escritura/retorno de ID
                cursor = conn.cursor() 
                cursor.execute("SELECT id_horario FROM HorariosSalida WHERE hora_salida = %s", (hora_salida_24h,))
                horario_db = cursor.fetchone() 

                id_horario = None
                if horario_db:
                    id_horario = horario_db[0] # Acceder por índice 0 si es una tupla
                else:
                    cursor.execute("INSERT INTO HorariosSalida (hora_salida, dias_semana, es_especial) VALUES (%s, %s, %s) RETURNING id_horario", 
                                   (hora_salida_24h, "Todos", False)) 
                    conn.commit()
                    id_horario = cursor.fetchone()[0] 

                if id_horario:
                    cursor.execute('INSERT INTO Asignaciones (id_horario, id_ruta, numero_camion_manual, fecha) VALUES (%s, %s, %s, %s)',
                                 (id_horario, id_ruta, numero_camion_manual, fecha)) 
                    conn.commit()
                    flash('Asignación creada exitosamente.', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Error: No se pudo determinar/crear el ID de horario.', 'error')

            except Exception as e: 
                logger.error(f"Error al guardar nueva asignación (POST): {e}", exc_info=True)
                flash(f'Error al guardar asignación: {e}. ¿Base de datos inicializada o datos inválidos?', 'error')
            finally:
                if conn: 
                    conn.close()

    return render_template('nueva_asignacion.html', rutas=rutas)


@app.route('/eliminar_asignacion/<int:id_asignacion>', methods=('POST',))
def eliminar_asignacion(id_asignacion):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor() # Obtener un cursor
        cursor.execute('DELETE FROM Asignaciones WHERE id_asignacion = %s', (id_asignacion,))
        conn.commit()
        flash('Asignación eliminada exitosamente.', 'success')
    except Exception as e:
        logger.error(f"Error al eliminar asignación: {e}", exc_info=True)
        flash(f'Error al eliminar asignación: {e}', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/limpiar_asignaciones', methods=('POST',))
def limpiar_asignaciones():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor() # Obtener un cursor
        cursor.execute('DELETE FROM Asignaciones')
        conn.commit()
        flash('Todas las asignaciones han sido eliminadas.', 'success')
    except Exception as e:
        logger.error(f"Error al limpiar asignaciones: {e}", exc_info=True)
        flash(f'Error al limpiar asignaciones: {e}', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/editar_asignacion/<int:id_asignacion>', methods=('GET', 'POST'))
def editar_asignacion(id_asignacion):
    conn = None
    asignacion = None 
    rutas = [] 
    try:
        conn = get_db_connection()
        # ¡CORRECCIÓN AQUÍ! Obtener un cursor con RealDictCursor
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) 
        asignacion_base = cursor.execute('SELECT A.*, HS.hora_salida FROM Asignaciones A JOIN HorariosSalida HS ON A.id_horario = HS.id_horario WHERE A.id_asignacion = %s', (id_asignacion,)).fetchone()
        
        if asignacion_base is None:
            flash('Asignación no encontrada.', 'error')
            if conn: conn.close() 
            return redirect(url_for('admin_dashboard'))

        asignacion = dict(asignacion_base) 
        asignacion['hora_salida_12h'] = convert_to_12h(asignacion['hora_salida'])

        orden_rutas = [
            'NUEVA ROSITA', 'CLOETE', 'AGUJITA', 'SABINAS', 'BARROTERAN',
            'ESPERANZAS', 'AURA', 'MUZQUIZ', 'PALAU', 'MANANTIALES'
        ]
        order_case = "CASE nombre "
        for i, ruta_name in enumerate(orden_rutas):
            order_case += f"WHEN '{ruta_name}' THEN {i} "
        order_case += "ELSE 99 END"
        rutas = cursor.execute(f'SELECT id_ruta, nombre, recorrido FROM rutas ORDER BY {order_case}, nombre').fetchall()
        
    except Exception as e:
        logger.error(f"Error al cargar asignación para editar (GET): {e}", exc_info=True)
        flash(f"Error al cargar asignación: {e}. ¿Base de datos inicializada?", 'error')
        if conn: conn.close()
        return redirect(url_for('admin_dashboard'))
    finally:
        if conn: conn.close() 

    if request.method == 'POST':
        hora_salida_12h_input = request.form['hora_salida_libre']
        fecha = request.form['fecha']
        id_ruta = request.form['id_ruta']
        numero_camion_manual = request.form.get('numero_camion')

        hora_salida_24h = convert_to_24h(hora_salida_12h_input)

        if not hora_salida_24h or not fecha or not id_ruta:
            flash('Error: Hora, Fecha y Ruta son campos obligatorios y la hora debe ser válida (ej. 3:00 PM).', 'error')
        else:
            conn = None 
            try:
                conn = get_db_connection()
                cursor = conn.cursor() # Obtener cursor para POST (escritura)
                cursor.execute("SELECT id_horario FROM HorariosSalida WHERE hora_salida = %s", (hora_salida_24h,))
                horario_db = cursor.fetchone()

                id_horario_nuevo = None
                if horario_db:
                    id_horario_nuevo = horario_db[0] 
                else:
                    cursor.execute("INSERT INTO HorariosSalida (hora_salida, dias_semana, es_especial) VALUES (%s, %s, %s) RETURNING id_horario", 
                                   (hora_salida_24h, "Todos", False)) 
                    conn.commit()
                    id_horario_nuevo = cursor.fetchone()[0]

                if id_horario_nuevo:
                    cursor.execute('''
                        UPDATE Asignaciones
                        SET id_horario = %s, id_ruta = %s, numero_camion_manual = %s, fecha = %s
                        WHERE id_asignacion = %s
                    ''', (id_horario_nuevo, id_ruta, numero_camion_manual, fecha, id_asignacion))
                    conn.commit()
                    flash('Asignación actualizada exitosamente.', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Error: No se pudo determinar/crear el ID de horario para la actualización.', 'error')

            except Exception as e:
                logger.error(f"Error al actualizar asignación (POST): {e}", exc_info=True)
                flash(f'Error al actualizar asignación: {e}', 'error')
            finally:
                if conn:
                    conn.close()
    
    return render_template('editar_asignacion.html', 
                           asignacion=asignacion, 
                           rutas=rutas, 
                           asignacion_hora_12h=asignacion['hora_salida_12h'])

@app.route('/copiar_asignacion/<int:id_asignacion>', methods=('POST',))
def copiar_asignacion(id_asignacion):
    conn_fetch = None
    conn_insert = None
    try:
        conn_fetch = get_db_connection()
        cursor_fetch = conn_fetch.cursor(cursor_factory=psycopg2.extras.RealDictCursor) # Obtener cursor para fetch
        asignacion_original = cursor_fetch.execute('SELECT * FROM Asignaciones WHERE id_asignacion = %s', (id_asignacion,)).fetchone()
        conn_fetch.close() 

        if asignacion_original is None:
            flash('Asignación original no encontrada para copiar.', 'error')
            return redirect(url_for('admin_dashboard'))

        conn_insert = get_db_connection() 
        cursor_insert = conn_insert.cursor() 
        cursor_insert.execute('INSERT INTO Asignaciones (id_horario, id_ruta, numero_camion_manual, fecha) VALUES (%s, %s, %s, %s)',
                     (asignacion_original['id_horario'], asignacion_original['id_ruta'], asignacion_original['numero_camion_manual'], asignacion_original['fecha']))
        conn_insert.commit()
        flash('Asignación copiada exitosamente. Puedes editarla si necesitas cambiar la fecha/hora.', 'success')
    except Exception as e:
        logger.error(f"Error al copiar asignación: {e}", exc_info=True)
        flash(f'Error al copiar asignación: {e}', 'error')
    finally:
        if conn_insert: 
            conn_insert.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/pantalla')
def pantalla_personal():
    conn = None
    try: 
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) # Obtener cursor con RealDictCursor
        
        utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        now = utc_now.astimezone(MONTERREY_TZ)
        
        hoy_str = now.strftime('%Y-%m-%d')
        hora_actual_dt = now.time()
        
        all_relevant_departures_raw = cursor.execute('''
            SELECT
                HS.hora_salida,
                HS.dias_semana,
                R.nombre AS nombre_ruta,
                R.recorrido,
                A.numero_camion_manual,
                A.fecha,
                A.id_asignacion 
            FROM Asignaciones AS A
            JOIN HorariosSalida AS HS ON A.id_horario = HS.id_horario
            JOIN Rutas AS R ON A.id_ruta = R.id_ruta
            WHERE A.fecha >= %s
            ORDER BY A.fecha ASC, HS.hora_salida ASC
        ''', (hoy_str,)).fetchall()

        all_relevant_departures = []
        for row in all_relevant_departures_raw:
            all_relevant_departures.append(row) 

        salidas_ahora_raw = []
        hora_activa_para_display_24h = None 
        fecha_activa_para_display = None
        
        for i, salida in enumerate(all_relevant_departures):
            salida_fecha_str = salida['fecha']
            salida_hora_str = salida['hora_salida'] 
            
            try:
                salida_datetime_obj = MONTERREY_TZ.localize(datetime.datetime.strptime(f"{salida_fecha_str} {salida_hora_str}", '%Y-%m-%d %H:%M'))
            except ValueError as e:
                logger.error(f"Error parseando fecha/hora '{salida_fecha_str} {salida_hora_str}': {e}", exc_info=True)
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
                        logger.error(f"Error parseando siguiente fecha/hora '{siguiente_salida_fecha_str} {siguiente_salida_hora_str}': {e}", exc_info=True)
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
        
        salidas_ahora_agrupadas_por_ruta = defaultdict(lambda: defaultdict(list))
        if hora_activa_para_display_24h and fecha_activa_para_display:
            salidas_ahora_raw = [s for s in all_relevant_departures if 
                             s['fecha'] == fecha_activa_para_display and 
                             s['hora_salida'] == hora_activa_para_display_24h]
            
            for salida in salidas_ahora_raw:
                ruta_nombre = salida['nombre_ruta']
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
                hora_display = salidas_list[0]['hora_salida_12h'] 
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


        proximas_salidas_raw = []
        
        if hora_activa_para_display_24h and fecha_activa_para_display:
            fecha_hora_activa_completa = MONTERREY_TZ.localize(datetime.datetime.strptime(f"{fecha_activa_para_display} {hora_activa_para_display_24h}", '%Y-%m-%d %H:%M'))
            
            for salida in all_relevant_departures:
                salida_dt_completa = MONTERREY_TZ.localize(datetime.datetime.strptime(f"{salida['fecha']} {salida['hora_salida']}", '%Y-%m-%d %H:%M'))
                if salida_dt_completa > fecha_hora_activa_completa:
                    salida['hora_salida_12h'] = convert_to_12h(salida['hora_salida']) 
                    proximas_salidas_raw.append(salida)
        else:
            for salida in all_relevant_departures:
                salida['hora_salida_12h'] = convert_to_12h(salida['hora_salida']) 
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
                hora_display = salidas_list[0]['hora_salida_12h'] 
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

        display_hora_actual = now.strftime('%I:%M:%S %p')
        display_fecha_actual = now.strftime('%d/%m/%Y')

        return render_template('pantalla_personal.html', 
                               salidas_ahora_agrupadas_por_ruta=salidas_ahora_para_plantilla, 
                               hora_activa_para_display_12h=convert_to_12h(hora_activa_para_display_24h) if hora_activa_para_display_24h else None, 
                               fecha_activa_para_display=fecha_activa_para_display, 
                               proximas_salidas_agrupadas_por_ruta=proximas_salidas_para_plantilla, 
                               hora_actual=display_hora_actual, 
                               fecha_actual=display_fecha_actual)
    except Exception as e:
        # Se cierra la conexión a la DB en caso de error si llegó a abrirse
        if 'conn' in locals() and conn:
            conn.close()
        logger.error(f"Error al cargar pantalla_personal: {e}", exc_info=True)
        flash(f"Error crítico al cargar la pantalla de personal: {e}. ¿Base de datos inicializada?", 'error')
        return render_template('error_page.html', error_message=str(e))


if __name__ == '__main__':
    app.run()