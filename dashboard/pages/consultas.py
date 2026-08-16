import streamlit as st
from datetime import timedelta
from datetime import datetime

conn = st.connection("postgres", type="sql")

st.set_page_config(page_title="Consultas", page_icon="🔎")
st.title("Consulta de canciones")

#----------------
# BUSQUEDA POR ARTISTA
#------------------

#1. Fetch all the artists
artistas = conn.query("select name from artist")

st.header("Buscar por artista")
st.write("Selecciona un nombre para ver sus detalles:")

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
#KPI 1: Total de canciones del artista
total_songs_artist = conn.query(
    """
    SELECT COUNT(*) AS total_songs
    FROM songs s
    INNER JOIN artist a ON a.id = s.artist_id
    WHERE a.name = :artist_name
    """,
    params={"artist_name": artist_name},
).iloc[0]

#KPI 2: Total de tonos del artista
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
    with st.expander("canciones del artista"):
        st.dataframe(artist_songs, hide_index=True)


#--------------------------------
#BUSQUEDA POR ATRIBUTOS
#--------------------------------

#--------- POR GENERO ---------
generos = ["Alabanza", "Adoración"]
st.header("Buscador de atributos")

with st.expander("buscar por género"):
    genero = st.selectbox("Buscar por género:", options=generos)
    if genero:
        query_songs_by_genre = conn.query(
        """select s.title as "Canción", 
            a.name as "Artista",
            s.tempo,
            s.tone,
            s.link_yt as link
        from songs s
        left join artist a on a.id = s.artist_id
        where genre_id  = (select id from genre where name = :genero);""",
        params={"genero": genero},
        )
        if not query_songs_by_genre.empty:
            st.dataframe(query_songs_by_genre, hide_index=True)
        else:
            st.warning("No se encontraron canciones con ese género.")


#---------------- BUSQUEDA POR TÍTULO

with st.expander("buscar por título"):
    song_title= st.text_input("ingresa el nombre de la canción").title()


    if song_title:

        query_song_by_title = conn.query(
            "SELECT * FROM songs WHERE title LIKE :title",
            params={"title": f"%{song_title}%"},
        )
        if not query_song_by_title.empty:
            st.dataframe(query_song_by_title, hide_index=True)
        else:
            st.warning("No se encontró ninguna canción con ese título.")

#------------------ Por Tempo ---------
with st.expander("buscar por tempo"):
    rango_tempo = st.slider("Selecciona el rango de tempo:", min_value=0, max_value=200, value=(0, 200), step=1)
    tempo_min, tempo_max = rango_tempo
    query_songs_by_tempo = conn.query(
        """select s.title, 
        a.name,
        s.tempo,
        s.tone,
        s.link_yt 
        from songs s
        left join artist a on a.id = s.artist_id
        where tempo between :tempo_min and :tempo_max;
        """,
        params={"tempo_min": tempo_min, "tempo_max": tempo_max},
    )
    if not query_songs_by_tempo.empty:
        st.dataframe(query_songs_by_tempo, hide_index=True)
    else:
        st.warning("No se encontraron canciones con ese rango de tempo.")


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
    st.write(f"Ok, gracias por tu sugerencia, pero todavía no sirve  JAJAJAJAJ: {sugerencia}")