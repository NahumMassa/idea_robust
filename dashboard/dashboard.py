import streamlit as st
import matplotlib.pyplot as plt

st.subheader("Setlist Dashboard de la Iglesia Dios es Amor Mérida")

conn = st.connection("postgres", type="sql") 

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



