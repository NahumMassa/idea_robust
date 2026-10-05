
from sqlalchemy import exc
import streamlit as st
import pandas as pd

from datetime import datetime, timedelta

from .chords import parse_chart, to_plain, transpose_sections, parse_tone
from .structure import parse_structure
from .models import TONALIDADES



TIME_FORMAT = "%Y-%m-%d"

# versión de la app (SemVer); se cambia aquí y al crear el tag de git vX.Y.Z
APP_VERSION = "1.0.0"

# Configuraciones globales predeterminadas de tu app
DEFAULT_COLUMN_CONFIG = {
    "link_yt": st.column_config.LinkColumn(
        label="YouTube",
        display_text="Ver video",
        help="Abrir video en YouTube"
    ),
    "tempo": st.column_config.NumberColumn(
        label="Tempo",
        format="%d BPM"
    )
}

def show_normalized_df(df: pd.DataFrame, extra_config: dict = None, **kwargs):
    """
    Renderiza un dataframe en Streamlit aplicando automáticamente
    las configuraciones de enlaces, formatos y estilos base.
    """
    config_final = DEFAULT_COLUMN_CONFIG.copy()
    if extra_config:
        config_final.update(extra_config)
        
    # Parámetros por defecto para todas las tablas del dashboard
    defaults = {
        "width": "stretch",
        "hide_index": True,
        "column_config": config_final
    }
    defaults.update(kwargs)
    
    return st.dataframe(df, **defaults)


def get_next_sunday_date(date:str=None)->str:
    """
    Calculates the next sunday for a given date
    date in format YYYY/MM/DD

    default = today
    """
    if date:
        today_obj = datetime.strptime(date, TIME_FORMAT)

    else:
        today_obj = datetime.now()


    sunday_num = 7 #7th day of the week is sundar
    today_weekday = today_obj.isoweekday() #in ISO, monday is 1 NOT 0

    days_diff = sunday_num - today_weekday 
    next_sunday_date = today_obj + timedelta(days=days_diff)
    return next_sunday_date.strftime(TIME_FORMAT)

#---------------------
# TARJETA DE CANCIÓN (setlist del domingo y consultas)

def chords_for_report(chords: str, tone: str | None, key: str | None) -> str:
    """Acordes sin corchetes; transpuestos si se ven en otro tono."""
    try:
        sections = parse_chart(chords)
        if tone and key and key != tone:
            sections = transpose_sections(sections, tone, key)
        return to_plain(sections)
    except ValueError:
        # formato anterior o tonos de distinto modo: se muestra tal cual
        return chords


def has_value(value) -> bool:
    return pd.notna(value) and value != ""


def structure_markdown(structure: str) -> str:
    """'IN - V1 - C' -> `IN` → `V1` → `C`"""
    try:
        parts = parse_structure(structure)
    except ValueError:
        return structure  # formato anterior: se muestra tal cual
    return " → ".join(f"`{p}`" for p in parts)


def transpose_selector(container, key: str, original_tone: str | None, tone: str | None) -> str | None:
    """
    Selector para ver los acordes en otro tono (solo vista, no se guarda).
    Ofrece los tonos del mismo modo que el original y arranca en el tono del servicio.
    """
    try:
        original_index, minor = parse_tone(original_tone)
    except (ValueError, AttributeError):
        return tone  # sin tono original válido no hay desde dónde transponer

    options = [t for t in TONALIDADES if t.endswith("-") == minor]
    # se compara por semitono para tolerar specific_key con otra ortografía (C# vs Db)
    try:
        target = parse_tone(tone)[0]
    except (ValueError, AttributeError):
        target = original_index
    default = next((k for k, t in enumerate(options) if parse_tone(t)[0] == target), 0)

    return container.selectbox("Transponer a", options, index=default, key=f"transpose_{key}")


def render_song_card(row, key: str, number: int | None = None) -> None:
    """
    Tarjeta de una canción: título, artista, tono/tempo/compás, estructura y acordes.
    row necesita title, artist, tempo, tone, link_yt, time_signature, structure y chords;
    specific_key (tono de ese servicio) es opcional. key debe ser único en la página.
    """
    original_tone = row.tone if has_value(row.tone) else None
    specific_key = getattr(row, "specific_key", None)
    tone = specific_key if has_value(specific_key) else original_tone

    with st.container(border=True):
        col_title, col_link = st.columns([4, 1], vertical_alignment="center")
        col_title.markdown(f"### {number} · {row.title}" if number else f"### {row.title}")
        if has_value(row.artist):
            col_title.caption(row.artist)
        if has_value(row.link_yt):
            col_link.link_button("▶️ YouTube", row.link_yt, width="stretch")

        badges = []
        if tone:
            note = f" (original {original_tone})" if original_tone and tone != original_tone else ""
            badges.append(f":orange-badge[🎵 Tono {tone}{note}]")
        if has_value(row.tempo):
            badges.append(f":blue-badge[⏱️ {int(row.tempo)} BPM]")
        if has_value(row.time_signature):
            badges.append(f":green-badge[🥁 {row.time_signature}]")
        if badges:
            st.markdown(" ".join(badges))

        st.markdown("**Estructura**")
        if has_value(row.structure):
            st.markdown(structure_markdown(row.structure))
        else:
            st.caption("Sin estructura registrada")

        col_label, col_tone = st.columns([3, 1], vertical_alignment="bottom")
        col_label.markdown("**Acordes**")
        if has_value(row.chords):
            view_tone = transpose_selector(col_tone, key, original_tone, tone)
            st.code(chords_for_report(row.chords, original_tone, view_tone), language=None)
        else:
            st.caption("Sin acordes registrados")


def show_footer() -> None:
    """Pie de página con la versión; se llama al final de cada página."""
    st.divider()
    st.markdown(
        f"<p style='text-align: center; opacity: 0.6; font-size: 0.8rem;'>"
        f"IDEA Mérida · Ministerio de Alabanza · v{APP_VERSION}</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    print(get_next_sunday_date())
    print(get_next_sunday_date("2026-04-24"))