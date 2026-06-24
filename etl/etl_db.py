import os 
import pandas as pd
import psycopg2 as pg 
from psycopg2 import extras #para poder insertar valores 
from dotenv import load_dotenv


load_dotenv()

conn = pg.connect(f"dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} host={os.getenv('DB_HOST')} port={os.getenv('DB_PORT')}")
cur = conn.cursor()

if cur:
    print("connected to db")


path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Setlist_completo.csv')

def sql_query(query:str ):
    cur.execute(query)
    return cur.fetchall()


def create_table(query:str, cur=cur, conn=conn, ):
    cur.execute(query)
    conn.commit()

#-----------------------
#tables schemas
#-----------------------

schema = """
CREATE TABLE IF NOT EXISTS artist (
    id SERIAL PRIMARY KEY,
    name VARCHAR(60) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS genre (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS songs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(60),
    artist_id INTEGER REFERENCES artist(id),
    genre_id INTEGER REFERENCES genre(id),
    tempo INTEGER CHECK (tempo > 0),
    tone VARCHAR(10),
    link_yt TEXT,
    UNIQUE (title, link_yt)
);

CREATE TABLE IF NOT EXISTS performance (
    id SERIAL PRIMARY KEY,
    song_id INTEGER REFERENCES songs(id),
    artist_id INTEGER REFERENCES artist(id),
    played_at DATE DEFAULT CURRENT_DATE,
    UNIQUE (played_at, song_id)
);
"""

# Creates all tables in a single query execution
create_table(schema)


#-----------------------
# dataframes processing
#-----------------------

setlist = pd.read_csv(path)

setlist = setlist.drop('To-play', axis=1) #esta columna ya no la vamos a necesitar
setlist = setlist.drop(['LastPlay', 'TimesPlayed'], axis=1)

#-------------------------
# artists
#-------------------------

#CLEAN ALL NAMES TO MAKE UNIFORM

setlist['Artist'] = setlist['Artist'].str.strip() #remove empty strings and white spaces
setlist['Artist'] = setlist['Artist'].str.title() #Le hacemos un title para tener el mismo formato
artist_tuple= [(artist, ) for artist in setlist['Artist'].unique().dropna()]




query = """
    INSERT INTO artist (name) 
    VALUES %s
    ON CONFLICT (name) DO NOTHING;
"""
extras.execute_values(cur, query, artist_tuple)
conn.commit()
    


#------------------------
#genres
#------------------------
setlist['Genre'] = setlist['Genre'].str.title()
setlist['Genre'] = setlist['Genre'].str.strip()
genres_tuple = [(genre, ) for genre in setlist['Genre'].unique().dropna()]

cur.executemany("""
    INSERT INTO genre (name)
    VALUES (%s)
    ON CONFLICT DO NOTHING;
""", genres_tuple)
conn.commit()



#------------------------
#songs
#------------------------

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




rows_with_nan.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Rows To Clean"))


