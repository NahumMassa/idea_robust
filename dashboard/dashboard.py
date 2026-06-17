import streamlit as st

st.set_page_config(
    page_title="IDEA",
    page_icon="✝️",
)
conn = st.connection("postgres", type="sql")

st.subheader("Setlist Dashboard de la Iglesia Dios es Amor Mérida")
st.sidebar.success("Selecciona una página para navegar")


#query returns a pandas dataframe 
kpis = conn.query("""
    SELECT
        (SELECT COUNT(*) FROM songs) AS total_songs,
        (SELECT COUNT(*) FROM artist) AS total_artists,
        (SELECT COUNT(distinct(tone)) from songs) as total_tones,
        (SELECT COUNT(*) FROM performance) AS total_performances
""").iloc[0]


col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Canciones", int(kpis["total_songs"]))

with col2:
    st.metric("Artistas", int(kpis["total_artists"]))

with col3:
    st.metric("Tonos", int(kpis["total_tones"]))



query = """
SELECT 
    COUNT(*) AS total_canciones, 
    a.name AS artista
FROM songs s 
INNER JOIN artist a ON s.artist_id = a.id 
GROUP BY a.name 
ORDER BY total_canciones DESC 
LIMIT 5;
"""

query_top_tones = """
SELECT 
    COUNT(*) AS total_canciones, 
    s.tone AS tono
FROM songs s 
GROUP BY s.tone
ORDER BY total_canciones DESC
LIMIT 5;
"""

query_songs_genre = """
    SELECT 
        COUNT(*) AS total_canciones,
        g.name AS genre
    FROM songs s
    JOIN genre g ON s.genre_id = g.id
    GROUP BY g.name
    ORDER BY total_canciones DESC
    LIMIT 5;
"""

most_songs_per_artist = conn.query(query)
query_top_tones = conn.query(query_top_tones)
query_songs_genre = conn.query(query_songs_genre)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Top 5 artistas con más canciones")
    st.bar_chart(most_songs_per_artist, y="total_canciones", x="artista")
    
with col2:
    st.subheader("Top 5 Tonos más tocadas")
    st.bar_chart(query_top_tones, y="total_canciones", x="tono")
    
with col3:
    st.subheader("Canciones por género")
    st.bar_chart(query_songs_genre, y="total_canciones", x="genre")

    