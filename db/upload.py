from datetime import datetime, timedelta
from connect import get_db_cursor # Importamos el gestor de cursor
import create_setlist as cl 
from psycopg2 import extras 

def get_timestamp_for_Sunday()->str:
    """
    gets the Sunday date to upload it to the db 
    """
    #the number for the Sunday
    SUNDAY = 6 
    today = datetime.now()

    #0 = mon, 1 = tue, 2=wed, 3=thu, 4=fri, 5=sat, 6=sun
    day_n = today.weekday() 
    remaining_days = SUNDAY - day_n

    #get the te date of Sunday
    sunday_date = (today + timedelta(days=remaining_days)).strftime("%Y-%m-%d") 
    #POSTGRES USES ISO 8601 format (YYYY-MM-DD)
    return sunday_date
        
def _create_table_perfomance(title:list, artist:list)->list:
    """
    This function creates the table with the songs and the date when they were played.
    we only need the titles and the date
    """
    sunday_date = get_timestamp_for_Sunday()
    #we only need the titles
    return [(title, artist, sunday_date) for title, artist in zip(title, artist)] 

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

def _upload_data_to_db(titles:list, artists:list, links:list): 
    #this list is only to upload the performance table
    perfomance_list = _create_table_perfomance(titles, artists)  
    artist_tuple = [(artist,) for artist in artists]
    songs_tuple = [(title, artist, link) for title, artist, link in zip(titles, artists, links)]
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
    _single_upload(query_performance, perfomance_list, temp=template_performance)
    print("ALL DATA UPLOADED SUCCESSFULLY!!")


def upload_and_format(text:str):
    title, artist, link = cl.format(text)
    _upload_data_to_db(title, artist, link)
    

if __name__ == "__main__":
    upload_and_format(cl.text3)
    