import sys
import streamlit as st
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import select
from models import (
    Songs, Artist, Performance, PerformanceElement, SongChart,
    get_next_sunday_date, session, render_song_card,
)

st.set_page_config(page_title="Setlist Domingo", page_icon="🎼")


#----------------
# SONGS FOR THIS SUNDAY
#----------------

#get sunday date
sunday_date = get_next_sunday_date()


# ttl corto para que los cambios de acordes/estructura del admin se vean pronto
@st.cache_data(ttl="10m")
def get_sunday_setlist(sunday_date: str):
    """
    Retorna el setlist dado una fecha de domingo, con su chart, en orden.
    """
    query = (
        select(
            Songs.title,
            Artist.name.label("artist"),
            Songs.tempo,
            Songs.tone,
            Songs.link_yt,
            PerformanceElement.specific_key,
            SongChart.time_signature,
            SongChart.structure,
            SongChart.chords,
        )
        .select_from(PerformanceElement)
        .join(Performance, PerformanceElement.performance_id == Performance.id)
        .outerjoin(Songs, PerformanceElement.song_id == Songs.id)
        .outerjoin(Artist, Songs.artist_id == Artist.id)
        .outerjoin(SongChart, SongChart.song_id == Songs.id)
        .where(Performance.played_at == sunday_date)
        .order_by(PerformanceElement.song_order)
    )
    return pd.read_sql(query, session.bind)


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(date: str) -> str:
    """'2026-10-11' -> 'Domingo 11 de octubre de 2026' (sin depender del locale)."""
    year, month, day = (int(x) for x in date.split("-"))
    return f"Domingo {day} de {MESES[month - 1]} de {year}"


#renderizar en Streamlit
df = get_sunday_setlist(sunday_date)

st.title("🎼 Setlist")
st.subheader(fecha_larga(sunday_date))
if df.empty:
    st.info("Todavía no hay setlist registrado para este domingo.")
else:
    st.caption(f"{len(df)} canciones")

for i, row in enumerate(df.itertuples(), 1):
    render_song_card(row, key=f"setlist_{i}", number=i)
