
import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2 as pg

load_dotenv()

@contextmanager
def get_db_cursor():
    #CONNECTING TO DB 
    print("Connectin to the DB...")
    conn = pg.connect(f"""
        dbname={os.getenv("DB_NAME")}
        user={os.getenv("DB_USER")}
        password={os.getenv("DB_PASSWORD")}
        host={os.getenv("DB_HOST")}
        port={os.getenv("DB_PORT")}"""
    )
    
    #CREATING CURSOR AND YIELDING
    with conn, conn.cursor() as cur:
        print("Connection and cursor are ready.")
        yield cur 
        #Psycopg manages the conn.commit if the cursor is succesful 

    conn.close()
    print("Connection closed.")

if __name__ == "__main__":
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT version();")
            db_version = cur.fetchone()
            print(f"Versión de la BD: {db_version}")
            
    except pg.Error as e:
        # Atrapamos errores específicos de PostgreSQL si la conexión o la query fallan
        print(f"Error crítico en la base de datos: {e}")

