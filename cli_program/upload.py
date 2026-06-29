import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from format_setlist import get_data_from_text, create_tuples_for_performance
import psycopg2 as pg
from psycopg2 import extras 
from dotenv import load_dotenv


#python cli_program/cli_program.py --mode upload
#python cli_program/cli_program.py --mode upload --date 2026-01-01


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

@contextmanager
def get_db_cursor():
    """
    gets a cursor to the db with a context manager that yields
    """
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

def _single_upload(query:str, data:list, temp:str=None):
    """
    this functions upload the data to the db 
    """
    print("Uploading data...")
    try:
        with get_db_cursor() as cur:
            extras.execute_values(cur, query, data, template=temp)
            print("uploaded successfully")
    except Exception as e:
        print(f"Error: {e}")

def upload_data_to_db(data:tuple[list[str], list[str], list[str]], date:str): 
    """
    upload all the data to the db, we have 3 tables:
    -artist
    -songs
    -performance
    """
    titles, artists, links = data
    artist_tuple = [(artist,) for artist in artists]
    songs_tuple = [(title, artist, link) for title, artist, link in zip(titles, artists, links)]
    performance_tuple = create_tuples_for_performance((titles, artists), date)

    
    query_artist = """
        INSERT INTO artist (name) VALUES %s
        ON CONFLICT (name) DO NOTHING;
    """
    
    query_songs = """
        INSERT INTO songs (title, artist_id, link_yt) 
        VALUES %s
        ON CONFLICT (title, link_yt) DO NOTHING;
    """

    query_performance = """
        INSERT INTO performance (song_id, artist_id, played_at)
        VALUES %s
        ON CONFLICT (played_at, song_id) DO NOTHING;
    """

    template_songs = """
        (%s, 
        (SELECT id FROM artist WHERE name = %s),
        %s)
    """

    template_performance = """
        ((SELECT id FROM songs WHERE title = %s),
        (SELECT id FROM artist WHERE name = %s),
        %s)
    """

    #ARTIST UPLOAD
    print("ARTIST UPLOAD --------------------->")
    _single_upload(query_artist, artist_tuple)

    #SONGS UPLOAD
    print("SONGS UPLOAD --------------------->")
    _single_upload(query_songs, songs_tuple, temp=template_songs)
    
    #PERFOMANCE UPLOAD
    print("PERFOMANCE UPLOAD --------------------->")
    _single_upload(query_performance, performance_tuple, temp=template_performance)
    print("ALL DATA UPLOADED SUCCESSFULLY!!")





if __name__ == "__main__":
    text3 = """
    Eres Señor Vencedor
    Abba Padre
    Él es más grande
    El poderoso de Israel
    Grande y fuerte (Proezas)
    ---
    Juan Carlos Alvarado
    Marco Barrientos
    Avivamiento
    Juan Carlos Alvarado
    Miel San Marcos
    ---
    https://youtu.be/YgzL38Uh3z0?si=RwJbv-TRYr0CArYO
    https://youtu.be/TzC42TFbB2Y?si=R4uiW-9e4d96t1XZ
    https://www.youtube.com/watch?v=c_7xEmW8RxM
    https://youtu.be/2cbVxPKaik4?si=fjG4yF0niQUsG_TO
    https://youtu.be/WZC9RAk7dOI?si=ma74qgy1Kc5PNkRy
    """
    data = get_data_from_text(text3)
    upload_data_to_db(data, "2026-01-01")