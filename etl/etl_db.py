
import pandas as pd
import psycopg2 as pg 
from psycopg2 import extras #para poder insertar valores 


conn = pg.connect('dbname=postgres user=postgres password=mypassword host=localhost port=5432')
cur = conn.cursor()

path = 'setlist.csv'


def sql_query(query:str ):
    cur.execute(query)
    return cur.fetchall()


def create_table(query:str, cur=cur, conn=conn, ):
    cur.execute(query)
    conn.commit()


artist_table = "CREATE TABLE IF NOT EXISTS artist (\
    id SERIAL PRIMARY KEY, \
    name VARCHAR(60) UNIQUE NOT NULL \
    )"
  

genre_table = """
CREATE TABLE IF NOT EXISTS genre (
    id serial PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
    );
"""

songs_table = """
CREATE TABLE IF NOT EXISTS songs (
    id Serial PRIMARY KEY,
    title VARCHAR(60),
    artist_id INTEGER REFERENCES artist(id),
    genre_id INTEGER REFERENCES genre(id),
    tempo INTEGER CHECK (tempo>0),
    tone VARCHAR(10),
    link_yt TEXT
);
"""
performance_table = """
CREATE TABLE IF NOT EXISTS performance (
    id SERIAL PRIMARY KEY, 
    song_id INTEGER REFERENCES songs(id),
    played_at DATE DEFAULT CURRENT_DATE
    );
"""

create_table(artist_table)
create_table(genre_table)
create_table(songs_table) 
create_table(performance_table)



setlist = pd.read_csv(path)
setlist.keys()


setlist = setlist.drop('To-play', axis=1) #esta columna ya no la vamos a necesitar

setlist['Artist'] = setlist['Artist'].str.title() #CLEAN ALL NAMES TO MAKE UNIFORM
artist = setlist['Artist'].unique().dropna() 


artist_list = list(artist)
artist_list


db_artist = sql_query('SELECT * FROM artist')

db_artist = [(artist[1], ) for artist in db_artist]
db_artist

query = """
    INSERT INTO artist (name) 
    VALUES %s
    ON CONFLICT (name) DO NOTHING;
"""
extras.execute_values(cur, query, db_artist)
conn.commit()
    
conn.commit()


genres = setlist['Genre'].value_counts()
genres

genres = setlist['Genre'].unique().dropna()
genres_tuple = [(genre, ) for genre in genres] #psycopg mmangaes list of tuples

cur.executemany("""
    INSERT INTO genre (name)
    VALUES (%s)
    ON CONFLICT DO NOTHING;
""", genres_tuple)
conn.commit()

rows_with_nan = setlist[setlist.isna().any(axis=1)]
print(f"hay {len(rows_with_nan)} filas con Nan que deben ser filtrados")
setlist_clean = setlist.dropna()
setlist_clean.info()


list_clean = list(setlist_clean[['Song', 'Artist', 'Genre', 'Tempo', 'Tone', 'link']].itertuples(index=False, name=None))
list_clean

query = """
    INSERT INTO songs (title, artist_id, genre_id, tempo, tone, link_yt) 
    VALUES %s
    ON CONFLICT DO NOTHING;
"""

template = """(
    %s, 
    (SELECT (id) FROM artist WHERE name = %s LIMIT 1),
    (SELECT (id) FROM genre WHERE name = %s LIMIT 1),
    %s,
    %s,
    %s
)"""
try:
    extras.execute_values(cur, query, list_clean, template=template) #extra.execute_values inserts all the info at one time, not every row at a time.
    conn.commit()
    print('data uploaded')

except Exception as e:
    print(f"Detected Error: {e}")
    conn.rollback() #volver al estado anterior para volver a intentar la query




rows_with_nan.to_csv("Rows To Clean")


