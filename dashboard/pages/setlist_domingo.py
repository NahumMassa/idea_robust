import os
import streamlit as st
from datetime import timedelta
from datetime import datetime
from pathlib import Path

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




