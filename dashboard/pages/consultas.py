import streamlit as st
from datetime import datetime, timedelta
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models import TONALIDADES
from models.utils import show_normalized_df, get_next_sunday_date, TIME_FORMAT


st.set_page_config(page_title="Consultas", page_icon="🔎")

#CONNECTION
conn = st.connection("postgres", type="sql")

st.title("Consulta de canciones")


def options(sql: str) -> list:
    """Opciones para un filtro: primera columna de la consulta."""
    return conn.query(sql, ttl=0).iloc[:, 0].tolist()


#--------------------------------
# FILTROS
# Cada filtro activo agrega una condición al WHERE y sus valores a params.
# Los valores del usuario SIEMPRE van en params (:nombre), nunca dentro del
# texto del SQL, para evitar inyección SQL.
#--------------------------------

FILTROS = ["Título", "Artista", "Género", "Tono", "Tempo", "Etiquetas", "Sin tocar"]

activos = st.pills(
    "Agregar filtros", FILTROS, selection_mode="multi", key="filtros",
    help="Las canciones deben cumplir todos los filtros activos",
)

conditions = []
params = {}
cols = st.columns(2)

for i, filtro in enumerate(activos):
    with cols[i % 2]:
        if filtro == "Título":
            title = st.text_input("Título contiene").strip()
            if title:
                conditions.append("s.title ILIKE :title")
                params["title"] = f"%{title}%"

        elif filtro == "Artista":
            artists = st.multiselect("Artista", options("SELECT name FROM artist ORDER BY name"))
            if artists:
                conditions.append("a.name = ANY(:artists)")
                params["artists"] = artists

        elif filtro == "Género":
            genres = st.multiselect("Género", options("SELECT name FROM genre ORDER BY name"))
            if genres:
                conditions.append("g.name = ANY(:genres)")
                params["genres"] = genres

        elif filtro == "Tono":
            tones_in_db = options("SELECT DISTINCT tone FROM songs WHERE tone IS NOT NULL")
            tones = st.multiselect("Tono", [t for t in TONALIDADES if t in tones_in_db])
            if tones:
                conditions.append("s.tone = ANY(:tones)")
                params["tones"] = tones

        elif filtro == "Tempo":
            tempo_min, tempo_max = st.slider("Tempo (BPM)", 40, 250, (40, 250))
            conditions.append("s.tempo BETWEEN :tempo_min AND :tempo_max")
            params["tempo_min"] = tempo_min
            params["tempo_max"] = tempo_max

        elif filtro == "Etiquetas":
            tags = st.multiselect(
                "Etiquetas", options("SELECT name FROM tags ORDER BY name"),
                help="Canciones que tengan todas las etiquetas elegidas",
            )
            if tags:
                conditions.append("""s.id IN (
                    SELECT st.song_id
                    FROM song_tags st
                    JOIN tags t ON t.id = st.tag_id
                    WHERE t.name = ANY(:tags)
                    GROUP BY st.song_id
                    HAVING COUNT(DISTINCT t.id) = :n_tags
                )""")
                params["tags"] = tags
                params["n_tags"] = len(tags)

        elif filtro == "Sin tocar":
            weeks = st.number_input("Sin tocar en las últimas N semanas", min_value=1, value=12)
            next_sunday = datetime.strptime(get_next_sunday_date(), TIME_FORMAT)
            # incluye las canciones que nunca se han tocado
            conditions.append("""NOT EXISTS (
                SELECT 1
                FROM performance_elements pe
                JOIN performances p ON p.id = pe.performance_id
                WHERE pe.song_id = s.id AND p.played_at >= :since
            )""")
            params["since"] = (next_sunday - timedelta(weeks=weeks)).date()

where = ("WHERE " + "\n  AND ".join(conditions)) if conditions else ""

# TTL 0 para que las canciones nuevas aparezcan sin esperar al caché
songs = conn.query(f"""
    SELECT
        s.title,
        a.name AS artist,
        g.name AS genre,
        s.tone,
        s.tempo,
        (SELECT string_agg(t.name, ', ' ORDER BY t.name)
         FROM song_tags st JOIN tags t ON t.id = st.tag_id
         WHERE st.song_id = s.id) AS tags,
        (SELECT MAX(p.played_at)
         FROM performance_elements pe JOIN performances p ON p.id = pe.performance_id
         WHERE pe.song_id = s.id) AS last_played,
        s.link_yt
    FROM songs s
    LEFT JOIN artist a ON a.id = s.artist_id
    LEFT JOIN genre g ON g.id = s.genre_id
    {where}
    ORDER BY s.title
""", params=params, ttl=0)

#--------------------------------
# RESULTADOS
#--------------------------------

col1, col2, col3 = st.columns(3)
col1.metric("Canciones", len(songs))
col2.metric("Artistas", songs["artist"].nunique())
col3.metric("Tonos", songs["tone"].nunique())

if songs.empty:
    st.warning("Ninguna canción cumple con todos los filtros.")
else:
    show_normalized_df(songs, extra_config={
        "title": "Canción",
        "artist": "Artista",
        "genre": "Género",
        "tone": "Tono",
        "tags": "Etiquetas",
        "last_played": st.column_config.DateColumn("Última vez tocada", format="YYYY-MM-DD"),
    })
