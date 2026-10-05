import sys
from datetime import datetime
from pathlib import Path
import streamlit as st

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models import *

conn = st.connection("postgres", type="sql")

# token from streamlit secrets
ADMIN_SECRET = st.secrets["ADMIN_TOKEN"]


def _admin_token_from_url() -> str | None:
    """Read admin token from URL query params (handles list/str variants)."""
    admin = st.query_params.get("admin")
    if isinstance(admin, list):
        admin = admin[0] if admin else None
    if admin is None:
        values = st.query_params.get_all("admin")
        admin = values[0] if values else None
    return admin.strip() if admin else None


url_token = _admin_token_from_url()
if url_token == ADMIN_SECRET:
    st.session_state["admin_authenticated"] = True

if not st.session_state.get("admin_authenticated"):
    st.error("❌ Acceso denegado: Acceso solo para Administradores")
    st.caption(
        "Token no es el mismo"
    )
    st.stop()

st.header("Panel de administrador")

#---------------------
# FUNCIONES

def get_or_create_artist(name: str) -> Artist:
    normalized = name.strip().title()
    artist = session.query(Artist).filter_by(name=normalized).first()
    if artist:
        return artist
    artist = Artist(name=normalized)
    session.add(artist)
    session.flush()
    return artist


def get_genre_id(name: str) -> int:
    genre = session.query(Genre).filter_by(name=name).first()
    if not genre:
        raise ValueError(f"Género no encontrado: {name}")
    return genre.id


def get_or_create_tags(names: list[str]) -> list[Tag]:
    """
    Devuelve los Tag para cada nombre. Los que ya existen en la tabla tags se
    reutilizan y los que no, se crean. Ignora vacíos y duplicados.
    """
    # misma normalización que Tag.sanitize_name, para comparar contra la db
    normalized = list(dict.fromkeys(n.strip().title() for n in names if n and n.strip()))
    if not normalized:
        return []

    existing = {tag.name: tag for tag in session.query(Tag).filter(Tag.name.in_(normalized))}
    tags = []
    for name in normalized:
        tag = existing.get(name)
        if tag is None:
            tag = Tag(name=name)
            session.add(tag)
        tags.append(tag)
    session.flush()
    return tags

def chords_for_editing(chords: str) -> str:
    """Acordes guardados sin corchetes; si vienen de un formato anterior, tal cual."""
    try:
        return to_plain(parse_chart(chords))
    except ValueError:
        return chords

#---------------------
# DATOS COMPARTIDOS
# TTL 0, PARA QUE AL AGREGAR CANCIONES APAREZCAN y no se use el caché

df_all_songs = conn.query("""select s.id,
                                s.title,
                                a.name as artist,
                                s.link_yt,
                                s.tempo
                            from songs s
                            left join artist a on artist_id = a.id
                            order by s.title;""", ttl=0)
# el tempo solo es para que al elegirla, sepa ponerla de más lenta a rápida
song_labels = {
    int(row.id): f"{row.title} - {row.artist} - {row.tempo}"
    for row in df_all_songs.itertuples()
}
song_ids = list(song_labels)

tag_names = conn.query("SELECT name FROM tags ORDER BY name", ttl=0)["name"].tolist()

tab_song, tab_tags, tab_setlist, tab_chart = st.tabs(
    ["🎵 Nueva canción", "🏷️ Etiquetas", "📋 Setlist", "🎸 Chart"]
)

#--------------------------
# AGREGAR CANCIÓN

with tab_song:
    artist_names = conn.query("SELECT name FROM artist ORDER BY name", ttl=0)["name"].tolist()
    genre_names = conn.query("SELECT name FROM genre")["name"].tolist()

    with st.form("new_song", clear_on_submit=True):
        title = st.text_input("Título")
        # permite elegir un artista existente o escribir uno nuevo
        artist = st.selectbox(
            "Artista", artist_names, index=None,
            placeholder="Elige o escribe un artista nuevo",
            accept_new_options=True,
        )
        link = st.text_input("Link de YouTube")

        col1, col2 = st.columns(2)
        genre = col1.selectbox("Género", genre_names)
        tone_selected = col2.selectbox("Tono", TONALIDADES)
        tempo = st.slider("Tempo", 40, 250)

        new_song_tags = st.multiselect(
            "Etiquetas", tag_names,
            placeholder="Elige o escribe etiquetas nuevas",
            accept_new_options=True,
        )

        submitted = st.form_submit_button("Subir canción", type="primary")

    if submitted:
        try:
            if not artist:
                raise ValueError("Falta el artista")
            title = title.strip().title()
            link = link.strip()
            if Songs.exists(session, title, link):
                st.warning("Esta canción ya existe en la base de datos")
            else:
                song = Songs(
                    title=title,
                    artist_id=get_or_create_artist(artist).id,
                    genre_id=get_genre_id(genre),
                    tempo=tempo,
                    tone=tone_selected,
                    link_yt=link,
                )
                song.tags = get_or_create_tags(new_song_tags)
                session.add(song)
                session.commit()
                st.success(f"✅ Canción agregada: {song.title} ({tone_selected} con link {song.link_yt})")
        except Exception as e:
            session.rollback()
            st.error(f"❌ Error al agregar la canción: {e}")

#--------------------------
# ETIQUETAS DE UNA CANCIÓN

with tab_tags:
    tag_song_id = st.selectbox(
        "Canción", song_ids, index=None,
        format_func=song_labels.get, placeholder="Busca una canción",
        key="tag_song",
    )

    if tag_song_id is not None:
        song = session.get(Songs, tag_song_id)
        # key por canción para que el default se recargue al cambiar de canción
        selected_tags = st.multiselect(
            "Etiquetas", tag_names,
            default=[tag.name for tag in song.tags],
            placeholder="Elige o escribe etiquetas nuevas",
            accept_new_options=True,
            key=f"tags_{tag_song_id}",
        )

        if st.button("Guardar etiquetas", type="primary"):
            try:
                # la lista elegida reemplaza a la anterior: quitar una etiqueta la desasigna
                song.tags = get_or_create_tags(selected_tags)
                session.commit()
                st.success(f"✅ Etiquetas guardadas para {song.title}")
            except Exception as e:
                session.rollback()
                st.error(f"❌ Error al guardar etiquetas: {e}")

#-------------------------
# CREAR SETLIST Y SUBIR PERFORMANCE

with tab_setlist:
    setlist_ids = st.multiselect(
        "Busca y elige las 5-6 canciones:",
        song_ids,
        format_func=song_labels.get,
        max_selections=6,
    )

    if setlist_ids:
        df_setlist = df_all_songs.set_index("id").loc[setlist_ids]

        mensaje = "*🎶 SETLIST DEL SERVICIO 🎶*\n\n"
        mensaje += "*CANCIÓN* | *ARTISTA* | *LINK*\n"
        for row in df_setlist.itertuples():
            mensaje += f"> *{row.title}* | {row.artist} | {row.link_yt} \n"

        st.text_area("Copiar para WhatsApp:", value=mensaje, height=160)

    st.divider()

    col1, col2 = st.columns([1, 2])
    played_at = col1.date_input(
        "Fecha del servicio",
        value=datetime.strptime(get_next_sunday_date(), "%Y-%m-%d").date(),
    )
    notes_for_performance = col2.text_input("Notas para el performance")

    if st.button("Registrar performance", type="primary", disabled=not setlist_ids):
        try:
            performance = Performance(played_at=played_at,
                service_type="Domingo",
                notes=notes_for_performance
                )
            for i, song_id in enumerate(setlist_ids, 1):
                performance.elements.append(
                    PerformanceElement(song_id=song_id, song_order=i)
                )
            session.add(performance)
            session.commit()

            st.success("Performance subida exitosamente")
        except Exception as e:
            session.rollback()
            st.error(f"Error al subir performance: {e}")

#-------------------------
# AGREGAR ESTRUCTURAS Y ACORDES

with tab_chart:
    chart_song_id = st.selectbox(
        "Canción", song_ids, index=None,
        format_func=song_labels.get, placeholder="Busca una canción",
        key="chart_song",
    )

    if chart_song_id is not None:
        # si la canción ya tiene chart, se edita en lugar de crear otro (song_id es único)
        chart = session.query(SongChart).filter_by(song_id=chart_song_id).first()
        song = session.get(Songs, chart_song_id)

        if song.link_yt:
            st.link_button("▶️ Ver en YouTube", song.link_yt)

        with st.form(f"chart_{chart_song_id}"):
            col1, col2 = st.columns(2)
            song_tone = col1.selectbox(
                "Tono", TONALIDADES,
                index=TONALIDADES.index(song.tone) if song.tone in TONALIDADES else None,
            )
            song_tempo = col2.number_input("Tempo (BPM)", min_value=1, max_value=300, value=song.tempo)
            song_link = st.text_input("Link de YouTube", value=song.link_yt or "")
            structure_input = st.text_input(
                "Estructura:",
                value=chart.structure if chart else "",
                placeholder="IN - V1 - PC - PC - C - V - PC'[2] - C2(2) - BR(4) - C - C - OUT",
                help="Partes separadas por '-', con o sin espacios. Se guardan en mayúsculas.",
            )
            chords_input = st.text_area(
                "Acordes / Progresión:",
                # se edita sin corchetes; al guardar se normaliza a ChordPro
                value=chords_for_editing(chart.chords) if chart and chart.chords else "",
                height=200,
                placeholder="VERSO\n| G | C G | E- D | C |\n\nPRE-CORO\n| C | D | E- E-, D | C |\n| A |",
                help="Cifrado americano por compás. Corchetes opcionales; menores con '-' o 'm'.",
            )
            time_signature_selected = st.selectbox(
                "Compás", COMPASES,
                index=COMPASES.index(chart.time_signature) if chart and chart.time_signature in COMPASES else 0,
            )
            submitted_chart = st.form_submit_button("Guardar chart", type="primary")

        if submitted_chart:
            try:
                if chart is None:
                    chart = SongChart(song_id=chart_song_id)
                    session.add(chart)
                chart.structure = structure_input
                chart.chords = chords_input
                chart.time_signature = time_signature_selected
                # los acordes no se transponen al cambiar el tono: se guardan tal como se escribieron
                song.tone = song_tone
                song.tempo = song_tempo
                song.link_yt = song_link
                session.commit()
                st.success("Canción, estructura y acordes guardados exitosamente")
            except Exception as e:
                session.rollback()
                st.error(f"Error al guardar la canción, estructura y acordes: {e}")

        # vista previa transpuesta, solo entre tonos del mismo modo que el original
        if chart and chart.chords and song.tone:
            same_mode = [t for t in TONALIDADES if t.endswith("-") == song.tone.endswith("-")]
            view_tone = st.selectbox(
                "Ver en tono", same_mode, index=same_mode.index(song.tone),
                key=f"view_tone_{chart_song_id}",
            )
            try:
                sections = transpose_sections(parse_chart(chart.chords), song.tone, view_tone)
                st.code(to_plain(sections), language=None)
            except ValueError as e:
                st.warning(f"No se pueden transponer los acordes guardados: {e}")
