
from sqlalchemy import exc
import streamlit as st
import pandas as pd

from datetime import datetime, timedelta

from sqlalchemy import select
from fpdf import FPDF

from .chords import parse_chart, to_plain, transpose_sections, parse_tone
from .structure import parse_structure
from .models import TONALIDADES, Songs, Artist, Performance, PerformanceElement, SongChart, session



TIME_FORMAT = "%Y-%m-%d"

# versión de la app (SemVer); se cambia aquí y al crear el tag de git vX.Y.Z
APP_VERSION = "1.2.1"

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
    # se compara por semitono para tolerar otra ortografía (C# vs Db)
    try:
        target = parse_tone(tone)[0]
    except (ValueError, AttributeError):
        target = original_index
    default = next((k for k, t in enumerate(options) if parse_tone(t)[0] == target), 0)

    return container.selectbox("Transponer a", options, index=default, key=f"transpose_{key}")


def render_song_card(row, key: str, number: int | None = None) -> None:
    """
    Tarjeta de una canción: título, artista, tono/tempo/compás, estructura y acordes.
    row necesita title, artist, tempo, tone, link_yt, time_signature, structure y chords.
    key debe ser único en la página.
    """
    tone = row.tone if has_value(row.tone) else None

    with st.container(border=True):
        col_title, col_link = st.columns([4, 1], vertical_alignment="center")
        col_title.markdown(f"### {number} · {row.title}" if number else f"### {row.title}")
        if has_value(row.artist):
            col_title.caption(row.artist)
        if has_value(row.link_yt):
            col_link.link_button("▶️ YouTube", row.link_yt, width="stretch")

        badges = []
        if tone:
            badges.append(f":orange-badge[🎵 Tono {tone}]")
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
            view_tone = transpose_selector(col_tone, key, tone, tone)
            st.code(chords_for_report(row.chords, tone, view_tone), language=None)
        else:
            st.caption("Sin acordes registrados")


#---------------------
# SETLIST DEL DOMINGO
# Vive aquí (y no en la página) para que el panel de administrador pueda
# limpiar su caché (y la del PDF) con clear_sunday_setlist_cache() sin esperar al ttl.

@st.cache_data(ttl="10m")
def get_sunday_setlist(sunday_date: str) -> pd.DataFrame:
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


def pdf_text(text) -> str:
    # shortcut: las fuentes base del PDF solo traen latin-1 (acentos y ñ sí);
    # lo demás (emojis, →) sale como '?'. Si estorba, cargar una fuente TTF.
    return str(text).encode("latin-1", "replace").decode("latin-1")


# colores (fondo, texto) parecidos a los badges de Streamlit en la tarjeta de canción
PDF_TEXT = (49, 51, 63)
PDF_MUTED = (128, 132, 149)
PDF_BORDER = (220, 222, 228)
PDF_CODE = ((240, 242, 246), PDF_TEXT)
PDF_ORANGE = ((255, 236, 217), (184, 92, 0))
PDF_BLUE = ((224, 236, 255), (28, 99, 214))
PDF_GREEN = ((223, 245, 229), (23, 128, 61))
CARD_PAD = 5


def pdf_badge(pdf: FPDF, text: str, colors, font=("Helvetica", "B", 9)) -> None:
    """Etiqueta con fondo redondeado; salta de renglón si no cabe."""
    bg, fg = colors
    pdf.set_font(*font)
    text = pdf_text(text)
    w, h = pdf.get_string_width(text) + 4, 5.5
    if pdf.get_x() + w > pdf.w - pdf.r_margin:
        pdf.ln(h + 1.5)
    pdf.set_fill_color(*bg)
    pdf.rect(pdf.get_x(), pdf.get_y(), w, h, style="F", round_corners=True, corner_radius=1.2)
    pdf.set_text_color(*fg)
    pdf.cell(w, h, text, align="C")
    pdf.set_x(pdf.get_x() + 1.5)


def pdf_label(pdf: FPDF, text: str) -> None:
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*PDF_TEXT)
    pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")


def pdf_empty(pdf: FPDF, text: str) -> None:
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*PDF_MUTED)
    pdf.cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")


def pdf_song(pdf: FPDF, row, number: int, with_chords: bool) -> None:
    """Contenido de la tarjeta, igual que render_song_card pero sin YouTube ni selector de tono."""
    tone = row.tone if has_value(row.tone) else None

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*PDF_TEXT)
    pdf.multi_cell(0, 7, pdf_text(f"{number} · {row.title}"), new_x="LMARGIN", new_y="NEXT")
    if has_value(row.artist):
        pdf_empty(pdf, pdf_text(row.artist))

    badges = []
    if tone:
        badges.append((f"Tono {tone}", PDF_ORANGE))
    if has_value(row.tempo):
        badges.append((f"{int(row.tempo)} BPM", PDF_BLUE))
    if has_value(row.time_signature):
        badges.append((row.time_signature, PDF_GREEN))
    if badges:
        pdf.ln(2)
        for text, colors in badges:
            pdf_badge(pdf, text, colors)
        pdf.ln(5.5)

    pdf_label(pdf, "Estructura")
    if has_value(row.structure):
        try:
            parts = parse_structure(row.structure)
        except ValueError:
            parts = [row.structure]  # formato anterior: se muestra tal cual
        for n, part in enumerate(parts):
            if n:
                pdf.set_text_color(*PDF_MUTED)
                pdf.cell(4, 5.5, "»", align="C")
                pdf.set_x(pdf.get_x() + 1.5)
            pdf_badge(pdf, part, PDF_CODE, font=("Courier", "", 9))
        pdf.ln(5.5)
    else:
        pdf_empty(pdf, "Sin estructura registrada")

    if with_chords:
        pdf_label(pdf, "Acordes")
        if has_value(row.chords):
            pdf.set_font("Courier", "", 9)  # monoespaciada para que los compases se alineen
            pdf.set_fill_color(*PDF_CODE[0])
            pdf.set_text_color(*PDF_TEXT)
            pdf.multi_cell(0, 4.5, pdf_text(chords_for_report(row.chords, tone, tone)),
                           fill=True, padding=3, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf_empty(pdf, "Sin acordes registrados")


def pdf_card(pdf: FPDF, draw) -> None:
    """Dibuja draw(pdf) dentro de un recuadro; si no cabe en lo que queda de hoja, pasa a la siguiente."""
    def inner(p):
        p.set_left_margin(p.l_margin + CARD_PAD)
        p.set_right_margin(p.r_margin + CARD_PAD)
        p.set_xy(p.l_margin, p.get_y() + CARD_PAD)
        draw(p)
        p.set_left_margin(p.l_margin - CARD_PAD)
        p.set_right_margin(p.r_margin - CARD_PAD)

    with pdf.offset_rendering() as test:
        inner(test)
    if test.page_break_triggered and pdf.get_y() > pdf.t_margin + 1:
        pdf.add_page()

    page, top = pdf.page, pdf.get_y()
    inner(pdf)
    if pdf.page == page:  # una canción más larga que una hoja se queda sin recuadro
        pdf.set_draw_color(*PDF_BORDER)
        pdf.rect(pdf.l_margin, top, pdf.epw, pdf.get_y() + CARD_PAD - top,
                 round_corners=True, corner_radius=3)
    pdf.set_xy(pdf.l_margin, pdf.get_y() + CARD_PAD + 5)


@st.cache_data(ttl="10m")
def get_sunday_setlist_pdf(sunday_date: str, title: str, with_chords: bool) -> bytes:
    """PDF del setlist con el mismo diseño de tarjetas que la página; acordes opcionales."""
    df = get_sunday_setlist(sunday_date)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*PDF_TEXT)
    pdf.multi_cell(0, 10, pdf_text(title), new_x="LMARGIN", new_y="NEXT")
    pdf_empty(pdf, f"{len(df)} canciones")
    pdf.ln(4)

    for i, row in enumerate(df.itertuples(), 1):
        pdf_card(pdf, lambda p, row=row, i=i: pdf_song(p, row, i, with_chords))

    return bytes(pdf.output())


def clear_sunday_setlist_cache() -> None:
    """Fuerza a que el setlist y su PDF se vuelvan a generar con los datos actuales."""
    get_sunday_setlist.clear()
    get_sunday_setlist_pdf.clear()


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