import sys
from pathlib import Path
import pandas as pd
import streamlit as st

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models import Artist, Genre, Songs, Performance, PerformanceElement, session, TONALIDADES, get_next_sunday_date

conn = st.connection("postgres", type="sql")

# token from streamlit secrets
ADMIN_SECRET = st.secrets["ADMIN_TOKEN"]


def _admin_token_from_url() -> str | None:
    """Read admin token from URL query params (handles list/str variants)."""
    admin = st.query_params.get("admin")
    if isinstance(admin, list):
        admin = admin[0] if admin else None
    if admin is None:
        values = st.query_params.get_all("admin")
        admin = values[0] if values else None
    return admin.strip() if admin else None


url_token = _admin_token_from_url()
if url_token == ADMIN_SECRET:
    st.session_state["admin_authenticated"] = True

if not st.session_state.get("admin_authenticated"):
    st.error("❌ Acceso denegado: Acceso solo para Administradores")
    st.caption(
        "Token no es el mismo"
    )
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

    # 1. Simulación de datos (o tu df_all_songs obtenido de PostgreSQL)
    df_all_songs = pd.DataFrame(conn.query("""select s.title,
                                                s.id,
                                                a.name as artist,
                                                s.link_yt,
                                                s.tempo
                                            from songs s
                                            left join artist a on artist_id = a.id;""", ttl=0))
                                            #TTL 0, PARA QUE AL AGREGAR CANCIONES APAREZCAN y no se use el caché

    # Creamos una columna auxiliar descriptiva para identificar cada opción
    df_all_songs["etiqueta"] = df_all_songs["title"] + " - " + df_all_songs["artist"] + " - " + df_all_songs["tempo"].astype(str)
    #el tempo solo es para que al elegirs, sepa ponerla de más lenta a rápida
    seleccion = st.multiselect(
        label="Busca y elige las 5-6 canciones:",
        options=df_all_songs["etiqueta"].tolist(),
        max_selections=6
    )

    if seleccion:
        df_setlist = df_all_songs[df_all_songs["etiqueta"].isin(seleccion)]
        
        mensaje = "*🎶 SETLIST DEL SERVICIO 🎶*\n\n"
        mensaje = f"{'*CANCIÓN*'} | {'*ARTISTA*'} | {'*LINK*'}\n"
        for idx, (_, row) in enumerate(df_setlist.iterrows(), 1):
            mensaje += f"> *{row['title']}* | {row['artist']} | {row['link_yt']} \n"
        
        st.text_area("Copiar para WhatsApp:", value=mensaje, height=160)

### FALTA LÓGICA PARA SUBIR A LA TABLA PERFORMANCE CON FECHA DE HOY U OTR
with st.expander("subir performance"):
    check = st.checkbox("Fecha personalizada?")
    date_str = get_next_sunday_date()
    
    if check:
        st.write(f" fecha natural: {date_str}")
        date_str = st.text_input("ponga la fecha con formato YYYY-MM-DD")
        try:
            get_next_sunday_date(date_str)  
            st.write("Fecha válida")
        except ValueError as e:
            st.error(f"Error: {e}")


    #NOTAS 
    notes_for_performance = st.text_input("Notas para el performance")

    if st.button("Upload"):
        try:
            performance = Performance(played_at=date_str,
                service_type="Domingo",
                notes=notes_for_performance
                )
            
            session.add(performance)
            #tengo que hacer un flush porque al hacer append directamente a la lista de elementos, 
            # no se le asigna un id hasta que se hace flush o commit
            session.flush()
            #st.write(performance.id)
            for i, (_, row) in enumerate(df_setlist.iterrows(), 1):
                performance_element = PerformanceElement(
                    performance_id=performance.id,
                    song_id=row["id"],
                    song_order=i
                )

                session.add(performance_element)
            session.add(performance)
            session.commit()
                
            st.success("Performance subida exitosamente")
        except Exception as e:
            session.rollback()
            st.error(f"Error al subir performance: {e}")
        