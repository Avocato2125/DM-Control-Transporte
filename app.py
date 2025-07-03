# Tu get_db_connection() actual:
def get_db_connection():
    # ...
    try:
        conn = psycopg2.connect(DATABASE_URL)
        # ¡AQUÍ NO ESTÁ LA LÍNEA PARA RealDictCursor!
        # conn.cursor_factory = psycopg2.extras.RealDictCursor  <-- ¡FALTA ESTA LÍNEA AQUÍ!
        
        logger.info("Conexión a la base de datos PostgreSQL exitosa.")
        return conn 
    except Exception as e:
        # ...