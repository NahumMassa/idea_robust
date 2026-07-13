"""
Uploads setlist data to the DB using SQLAlchemy models.
Called by setlistcli.py with --mode upload.
"""

import sys
import os
from datetime import datetime

# Add project root so `models` package is importable
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from format_setlist import get_data_from_text, get_timestamp_for_Sunday
from models.models import session, Artist, Songs, Performance


def _get_or_create_artist(sess, name: str):
    """
    Returns the Artist row (existing or newly created).
    """
    instance = sess.query(Artist).filter_by(name=name.strip().title()).first()
    if instance:
        return instance
    instance = Artist(name=name)
    sess.add(instance)
    sess.flush()  # write to DB to get the generated id, without committing yet
    return instance


def _get_or_create_song(sess, title: str, artist_id: int, link_yt: str):
    """
    Returns the Songs row (existing or newly created).
    Matched by title + link_yt. tempo/tone/genre_id are optional at upload time.
    """
    instance = sess.query(Songs).filter(
        Songs.title == title.strip().title(),
        Songs.link_yt == link_yt.strip()
    ).first()
    if instance:
        return instance
    instance = Songs(
        title=title,
        artist_id=artist_id,
        link_yt=link_yt,
        genre_id=None,
        tempo=None,
        tone=None,
    )
    sess.add(instance)
    sess.flush()
    return instance


def upload_data_to_db(data: tuple[list[str], list[str], list[str]], date: str):
    """
    Upload all setlist data to the DB (artist → songs → performance order).
    Rolls back the entire transaction on any error.
    """
    titles, artists_list, links = data

    if date is None:
        date = get_timestamp_for_Sunday()

    played_at = datetime.strptime(date, "%Y-%m-%d")

    try:
        # ── 1. ARTISTS ────────────────────────────────────────────────────────
        print("ARTIST UPLOAD --------------------->")
        artist_objects = {}
        for name in artists_list:
            a = _get_or_create_artist(session, name)
            artist_objects[name.strip().title()] = a
            print(f"  {'created' if not a.id else 'found'}: {a.name} (id={a.id})")

        # ── 2. SONGS ──────────────────────────────────────────────────────────
        print("SONGS UPLOAD --------------------->")
        song_objects = {}
        for title, artist_name, link in zip(titles, artists_list, links):
            a = artist_objects[artist_name.strip().title()]
            s = _get_or_create_song(session, title, a.id, link)
            song_objects[title.strip().title()] = s
            print(f"  {'created' if not s.id else 'found'}: {s.title} (id={s.id})")

        # ── 3. PERFORMANCE ────────────────────────────────────────────────────
        print("PERFORMANCE UPLOAD --------------------->")
        for title in titles:
            s = song_objects[title.strip().title()]
            existing = session.query(Performance).filter_by(
                song_id=s.id, played_at=played_at
            ).first()
            if existing:
                print(f"  skipped (already exists): {s.title} on {date}")
                continue
            perf = Performance(song_id=s.id, played_at=played_at)
            session.add(perf)
            print(f"  added: {s.title} on {date}")

        session.commit()
        print("ALL DATA UPLOADED SUCCESSFULLY!!")

    except Exception as e:
        session.rollback()
        print(f"Error during upload, rolled back: {e}")
        raise


if __name__ == "__main__":
    text3 = """
    Eres Señor Vencedor
    Abba Padre
    Él es más grande
    El poderoso de Israel
    Grande y fuerte (Proezas)
    ---
    Juan Carlos Alvarado
    Marco Barrientos
    Avivamiento
    Juan Carlos Alvarado
    Miel San Marcos
    ---
    https://youtu.be/YgzL38Uh3z0?si=RwJbv-TRYr0CArYO
    https://youtu.be/TzC42TFbB2Y?si=R4uiW-9e4d96t1XZ
    https://www.youtube.com/watch?v=c_7xEmW8RxM
    https://youtu.be/2cbVxPKaik4?si=fjG4yF0niQUsG_TO
    https://youtu.be/WZC9RAk7dOI?si=ma74qgy1Kc5PNkRy
    """
    data = get_data_from_text(text3)
    upload_data_to_db(data, "2026-01-01")
