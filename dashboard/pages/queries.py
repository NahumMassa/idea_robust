import sys
from pathlib import Path
import pandas as pd
import streamlit as st

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models import Artist, Genre, Songs, session, TONALIDADES

conn = st.connection("postgres", type="sql")

# token from streamlit secrets
ADMIN_SECRET = st.secrets["ADMIN_TOKEN"]

# token from parameters
admin = st.query_params.get("admin")

if admin != ADMIN_SECRET:
    st.error("❌ Acceso denegado")
    st.stop()

st.header("Panel de administrador")

tonos = TONALIDADES[:]

#---------------------
# FUNCIONES 

def get_or_create_artist(name: str) -> Artist:
    normalized = name.strip().title()
    artist = session.query(Artist).filter_by(name=normalized).first()
    if artist:
        return artist
    artist = Artist(name=normalized)
    session.add(artist)
    session.flush()
    return artist


def get_genre_id(name: str) -> int:
    genre = session.query(Genre).filter_by(name=name).first()
    if not genre:
        raise ValueError(f"Género no encontrado: {name}")
    return genre.id

#--------------------------
# AGREGAR CANCIÓN

with st.expander("agregar canción"):
    # TÍTULO
    title = st.text_input("Título")
    title = title.title().strip()

    # ARTISTA
    check_artist = st.checkbox("Agregar artista ya existente")
    if check_artist:
        st.write("Va a agregar un artista ya existente de la base de datos")
        artist_names = conn.query("SELECT name FROM artist")["name"].tolist()
        artist = st.selectbox("Artista", artist_names)
    else:
        artist = st.text_input("Nuevo artista")
        artist = artist.title().strip()

    # GÉNERO
    genre_names = conn.query("SELECT name FROM genre")["name"].tolist()
    genre = st.selectbox("Género", genre_names)

    # TEMPO
    tempo = st.slider("Tempo", 40, 250)

    # TONO
    tone_selected = st.selectbox("Tono", tonos)

    #LINK
    link = st.text_input("Link de YouTube")
    link = link.strip()

    submit_button = st.button("Subir canción")

    if submit_button:
        try:
            if check_artist:
                artist_obj = session.query(Artist).filter_by(name=artist).first()
                if not artist_obj:
                    raise ValueError(f"Artista no encontrado: {artist}")
            else:
                artist_obj = get_or_create_artist(artist)

            if Songs.exists(session, title, link):
                st.warning("Esta canción ya existe en la base de datos")
            else:
                song = Songs(
                    title=title,
                    artist_id=artist_obj.id,
                    genre_id=get_genre_id(genre),
                    tempo=tempo,
                    tone=tone_selected,
                    link_yt=link,
                )
                session.add(song)
                session.commit()
                st.success(f"✅ Canción agregada: {song.title} ({tone_selected} con link {song.link_yt})")
        except Exception as e:
            session.rollback()
            st.error(f"❌ Error al agregar la canción: {e}")

#-------------------------
# CREAR SETLIST 

with st.expander("creat setlist"):

    st.subheader("📋 Seleccionar Setlist del Domingo")

    # 1. Simulación de datos (o tu df obtenido de PostgreSQL)
    df_canciones = pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 6, 7],
        "titulo": ["Gracia Sublime", "Rey de Reyes", "Abre Mis Ojos", "La Bendición", "Way Maker", "Hermoso Dios", "Cuan Grande es Dios"],
        "artista": ["Phil Wickham", "Hillsong", "Paul Baloche", "Kari Jobe", "Sinach", "Un Corazón", "Chris Tomlin"],
        "tono": ["G", "D", "E-", "B", "A", "C", "C#"],
        "tempo": [102, 130, 110, 70, 68, 75, 78]
    })




    df = df_canciones.copy() 
    # Creamos una columna auxiliar descriptiva para identificar cada opción
    df["etiqueta"] = df["titulo"] + " - " + df["artista"] + " (" + df["tono"] + ")"

    seleccion = st.multiselect(
        label="Busca y elige las 5-6 canciones:",
        options=df["etiqueta"].tolist(),
        max_selections=6
    )

    if seleccion:
        df_setlist = df[df["etiqueta"].isin(seleccion)]
        
        mensaje = "*🎶 SETLIST DEL SERVICIO 🎶*\n\n"
        for idx, (_, row) in enumerate(df_setlist.iterrows(), 1):
            mensaje += f"{idx}. *{row['titulo']}* - {row['artista']} ({row['tono']}) - {row['tempo']} BPM\n"
        
        st.text_area("Copiar para WhatsApp:", value=mensaje, height=160)