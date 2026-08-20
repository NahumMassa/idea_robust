import sys
import streamlit as st
from datetime import timedelta
from datetime import datetime
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import select 
from models import Songs, Artist, Performance, PerformanceElement, get_next_sunday_date, session, show_normalized_df

conn = st.connection("postgres", type="sql")

st.set_page_config(page_title="Setlist Domingo", page_icon="🎼")


#----------------
# SONGS FOR THIS SUNDAY
#----------------

#get sunday date
sunday_date = get_next_sunday_date()

st.header("Setlist del Domingo")


@st.cache_data(ttl="5d")
def get_sunday_setlist(sunday_date: str):
    """
    Retorna el setlist dado una fecha de domingo.
    """
    query = (
        select(
            Songs.title,
            Artist.name.label("artist"),
            Songs.tempo,
            Songs.tone,
            Songs.link_yt,
        )
        .select_from(PerformanceElement)
        .join(Performance, PerformanceElement.performance_id == Performance.id)
        .outerjoin(Songs, PerformanceElement.song_id == Songs.id)
        .outerjoin(Artist, Songs.artist_id == Artist.id)
        .where(Performance.played_at == sunday_date)
    )
    return pd.read_sql(query, session.bind)

#renderizar en Streamlit
st.subheader(f"Canciones para el ({sunday_date})")

df = get_sunday_setlist(sunday_date)
show_normalized_df(df)
conn = st.connection("postgres", type="sql")


#------------------
# SUGERENCIAS
#-----------------

st.header("¿Sugerencias de canciones?")
st.write("Esta sección está en construcción... Pero aquí podrás poner tus sugerencias de canciones!")
sugerencia = st.text_input("Sugerencia")

if st.button("Enviar sugerencia"):
    st.write(f"Gracias por tu sugerencia, pero esta sección sigue en construcción (es un reto evadir los bots): {sugerencia}")
