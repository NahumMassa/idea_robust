import sys
import streamlit as st
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models import get_next_sunday_date, get_sunday_setlist, render_song_card, show_footer

st.set_page_config(page_title="Setlist Domingo", page_icon="🎼")


#----------------
# SONGS FOR THIS SUNDAY
#----------------

#get sunday date
sunday_date = get_next_sunday_date()


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

show_footer()
