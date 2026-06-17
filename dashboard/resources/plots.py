import os
import streamlit as st
import matplotlib.pyplot as plt
from pathlib import Path

# Cambiar al directorio 'dashboard' para que streamlit encuentre la carpeta .streamlit y sus secretos
dashboard_dir = Path(__file__).resolve().parent.parent
os.chdir(dashboard_dir)



conn = st.connection("postgres", type="sql")


query = """
SELECT 
    COUNT(*) AS total_canciones, 
    a.name AS artista
FROM songs s 
INNER JOIN artist a ON s.artist_id = a.id -- El JOIN va PRIMERO
GROUP BY a.name -- Agrupamos por lo que queremos mostrar
ORDER BY total_canciones DESC -- Para que tenga sentido el "Top 5"
LIMIT 5;
"""
most_songs_per_artist = conn.query(query)

plt.figure(figsize=(10, 5))
plt.barh(most_songs_per_artist["artista"], most_songs_per_artist["total_canciones"])
plt.title("Top 5 artistas con más canciones")
st.pyplot(plt)