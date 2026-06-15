from datetime import datetime, timedelta
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="IDEA",
    page_icon="✝️",
)
conn = st.connection("postgres", type="sql")

st.subheader("Setlist Dashboard de la Iglesia Dios es Amor Mérida")
st.sidebar.success("Selecciona una página para navegar")

def get_upcoming_sunday() -> str:
    today = datetime.now()
    remaining_days = 6 - today.weekday()
    return (today + timedelta(days=remaining_days)).strftime("%Y-%m-%d")

sunday = get_upcoming_sunday()

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

#----------------
# SONGS FOR THIS SUNDAY
#----------------


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

st.subheader(f"Setlist del domingo ({sunday})")
st.dataframe(songs_for_sunday, width="stretch", hide_index=True)

