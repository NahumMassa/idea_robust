import os
import streamlit as st
from datetime import timedelta
from datetime import datetime
from pathlib import Path

# Cambiar al directorio 'dashboard' para que streamlit encuentre la carpeta .streamlit y sus secretos
dashboard_dir = Path(__file__).resolve().parent.parent
os.chdir(dashboard_dir)

st.set_page_config(page_title="Setlist Domingo", page_icon="🎼")

conn = st.connection("postgres", type="sql")
#----------------
# SONGS FOR THIS SUNDAY
#----------------

def get_upcoming_sunday() -> str:
    today = datetime.now()
    remaining_days = 6 - today.weekday()
    return (today + timedelta(days=remaining_days)).strftime("%Y-%m-%d")

sunday = get_upcoming_sunday()


st.header("Setlist del Domingo")


songs_for_sunday = conn.query("""
SELECT
    s.title AS título,
    a.name AS artista,
    s.tempo,
    s.link_yt AS link
FROM performance p
INNER JOIN songs s ON s.id = p.song_id
INNER JOIN artist a ON a.id = p.artist_id
WHERE p.played_at = :played_at
""", params={"played_at": sunday})

st.subheader(f"Canciones para el ({sunday})")
st.dataframe(songs_for_sunday, width="stretch", hide_index=True)



conn = st.connection("postgres", type="sql")

#-----------------------
# FADD A NEW SONG
#----------------------

mode = ['Mayor', 'Menor']
tones = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'Db', 'Ab', 'Eb', 'Bb', 'F']


#TÍTULO------------------------------
title = st.text_input("Título")
title = title.title().strip()

#ARTISTA-----------------------------
check_artist = st.checkbox("Agregar artista ya existente")
if check_artist:    
    st.write("Va a agregar un artista ya existente de la base de datos")
    artist_list = conn.query("SELECT name FROM artist")
    artist = st.selectbox("Artista", artist_list)
else:
    artist = st.text_input("Nuevo artista")
    artist = artist.title().strip()

#GENRE------------------------------
genres = conn.query("SELECT name FROM genre")
genre = st.selectbox("Género", genres)

#TEMPO------------------------------
tempo = st.slider("Tempo", 40, 250)

#TONO--------------------------------
tone_selected = st.selectbox("Tono", tones)
mode_selected = st.selectbox("Modo", mode)
tone_complete = tone_selected + mode_selected

link = st.text_input("Link de YouTube")
link = link.strip()


# Usamos un botón normal
submit_button = st.button("Subir canción")

if submit_button:
    # Código para insertar...


    
    

    pass
    
    if submit_button:
        conn.execute("""
            INSERT INTO songs (title, artist_id, genre_id, tempo, tone, link_yt) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, artist, genre, tempo, tone, link))
        conn.commit()
        st.success("Canción agregada correctamente")



