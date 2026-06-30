import streamlit as st
from sqlalchemy import text

conn = st.connection("postgres", type="sql")


def add_song_to_db(title, artist, genre, tempo, tone, link):
    try:
        with conn.session as session:
            # Insert artist if not already in the db
            session.execute(
                text("INSERT INTO artist (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
                {"name": artist}
            )
            # Insert song, resolving artist_id and genre_id by name via subqueries
            session.execute(
                text("""
                    INSERT INTO songs (title, artist_id, genre_id, tempo, tone, link_yt)
                    VALUES (
                        :title,
                        (SELECT id FROM artist WHERE name = :artist LIMIT 1),
                        (SELECT id FROM genre  WHERE name = :genre  LIMIT 1),
                        :tempo,
                        :tone,
                        :link
                    )
                    ON CONFLICT (title, link_yt) DO NOTHING
                """),
                {"title": title, "artist": artist, "genre": genre,
                 "tempo": tempo, "tone": tone, "link": link}
            )
        st.success("✅ Canción agregada correctamente")

    except Exception as e:
        st.error(f"❌ Error al agregar la canción: {e}")


def add_performance_to_db(song_title, played_at):
    try:
        with conn.session as session:
            session.execute(
                text("""
                    INSERT INTO performance (song_id, played_at)
                    VALUES (
                        (SELECT id FROM songs WHERE title = :title LIMIT 1),
                        :played_at
                    )
                    ON CONFLICT (played_at, song_id) DO NOTHING
                """),
                {"title": song_title, "played_at": played_at}
            )
        st.success("✅ Performance agregada correctamente")

    except Exception as e:
        st.error(f"❌ Error al agregar la performance: {e}")

if __name__ == "__main__":
    add_song_to_db("title", "artist", "genre", "tempo", "tone", "link")
