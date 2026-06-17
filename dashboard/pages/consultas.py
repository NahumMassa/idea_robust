import streamlit as st
from datetime import timedelta
from datetime import datetime



st.set_page_config(page_title="Consultas", page_icon="🔎")

st.title("Consulta de canciones")
st.write("Busca por artista o canción para ver información específica")

conn = st.connection("postgres", type="sql")

st.header("Busqueda por nombre")
song_title= st.text_input("ingresa el nombre de la canción").title()

#----------------
# BUSQUEDA POR TÍTULO
#------------------


if song_title:

    query_song_by_title = conn.query(
        "SELECT * FROM songs WHERE title = :title",
        params={"title": song_title},
    )
    if not query_song_by_title.empty:
        st.dataframe(query_song_by_title, hide_index=True)
    else:
        st.warning("No se encontró ninguna canción con ese título.")

#----------------
# BUSQUEDA POR ARTISTA
#------------------

#1. Fetch all the artists
artistas = conn.query("select name from artist")

st.header("Buscador de Repertorio")
st.write("Selecciona una banda para ver sus detalles:")

#2. user selects the artist
artist_name = st.selectbox(
    "Selecciona una banda:",
    options=artistas
)
st.markdown(f"### **{artist_name}**")

artist_songs = conn.query(
    """
    SELECT s.title as título, s.tone as tono, s.tempo, s.link_yt as link
    FROM songs s
    INNER JOIN artist a ON a.id = s.artist_id
    WHERE a.name = :artist_name
    """,
    params={"artist_name": artist_name},
)

total_songs_artist = conn.query(
    """
    SELECT COUNT(*) AS total_songs
    FROM songs s
    INNER JOIN artist a ON a.id = s.artist_id
    WHERE a.name = :artist_name
    """,
    params={"artist_name": artist_name},
).iloc[0]

total_tones_artist = conn.query(
    """
    SELECT COUNT(DISTINCT s.tone) AS total_tones
    FROM songs s
    INNER JOIN artist a ON a.id = s.artist_id
    WHERE a.name = :artist_name
    """,
    params={"artist_name": artist_name},
).iloc[0]

col1, col2 = st.columns(2)

with col1:
    st.metric("Canciones", int(total_songs_artist["total_songs"]))

with col2:
    st.metric("Tonos", int(total_tones_artist["total_tones"]))

if not artist_songs.empty:
    st.dataframe(artist_songs, hide_index=True)
else:
    st.warning(f"No se encontraron canciones de {artist_name}.")

#-------------------------
#BUSCAR CANCIONES NO TOCADAS HACE MÁS DE 3 MESES
#-------------------------
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


def not_played_songs_due_a_date(time_span_in_weeks: int):
    """
    fetch not played songs given a time span in weeks
    """
    date_format = "%Y-%m-%d"
    sunday_str = get_timestamp_for_Sunday()
    sunday_datetime = datetime.strptime(sunday_str, date_format)
    deltasunday = timedelta(weeks=time_span_in_weeks)

    time_span = sunday_datetime - deltasunday

    songs_not_played = conn.query("""
    SELECT 
        s.title AS "Canción",
        a.name AS "Artista",
        MAX(p.played_at) AS "Última Vez Tocada"
    FROM performance p
    INNER JOIN songs s ON s.id = p.song_id
    INNER JOIN artist a ON a.id = p.artist_id
    GROUP BY s.title, a.name
    HAVING MAX(p.played_at) < :time_span;

    """, params={"time_span": time_span})
    
    return songs_not_played

st.header("Canciones no tocadas hace más de # semanas tiempo")
st.write("Buscar canciones que no se han tocado a partir de un número de semanas")
time_span= st.text_input("ingresa el número de semanas:").title()
if time_span:
    time_span = int(time_span)
    if time_span > 0:
        songs_not_played = not_played_songs_due_a_date(time_span)
        st.dataframe(songs_not_played, hide_index=True)

#-----------------
#SUGERENCIA DE CANCIONES
#-----------------

st.header("¿Sugerencias de canciones?")
st.write("Esta sección está en construcción... Pero aquí podrás poner tus sugerencias de canciones!")
sugerencia = st.text_input("Sugerencia")

if st.button("Enviar sugerencia"):
    st.write(f"Ok, gracias por tu sugerencia, pero todavía sirve  JAJAJAJAJ: {sugerencia}")