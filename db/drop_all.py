import connect as pg

def drop_all_tables():
    try:
        with pg.get_db_cursor() as cur:
            # Drops the public schema and all objects (tables, views, etc.) inside it
            cur.execute("DROP SCHEMA public CASCADE;")
            
            # Recreates the public schema
            cur.execute("CREATE SCHEMA public;")
            
            # Restore default permissions on the public schema
            cur.execute("GRANT ALL ON SCHEMA public TO public;")
            
            print("Successfully deleted all tables and data.")
    except pg.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    drop_all_tables()
