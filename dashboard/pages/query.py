import streamlit as st



st.set_page_config(page_title="Consultas", page_icon="🔎")

st.header("Consulta de canciones")
st.write("Busca por artista o canción para ver información específica")

conn = st.connection("postgres", type="sql")

st.subheader("Busqueda por nombre")
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


st.title("🎵 Buscador de Repertorio")
st.subheader("Selecciona una banda para ver sus detalles:")

#2. user selects the artist
artist_name = st.selectbox(
    "Selecciona una banda:",
    options=artistas
)
st.markdown(f"### Mostrando resultados para: **{artist_name}**")

artist_songs = conn.query(
    """
    SELECT s.title as título, s.tone as tono, s.tempo, s.link_yt as link
    FROM songs s
    INNER JOIN artist a ON a.id = s.artist_id
    WHERE a.name = :artist_name
    """,
    params={"artist_name": artist_name},
)

if not artist_songs.empty:
    st.info(f"Buscando canciones de {artist_name}...")
    st.dataframe(artist_songs, hide_index=True)
else:
    st.warning(f"No se encontraron canciones de {artist_name}.")