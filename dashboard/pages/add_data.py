import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from queries import add_song_to_db

conn = st.connection("postgres", type="sql")

st.title("Agregar canción")
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
    add_song_to_db(title, artist, genre, tempo, tone_complete, link)




