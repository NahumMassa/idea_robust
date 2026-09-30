"""
Tests for models/models.py

Uses an in-memory SQLite database so no real DB connection is required.
models.py is loaded directly by file path with importlib to avoid triggering
the Streamlit dashboard through the `dashboard` package __init__.

Run with:
    venv/bin/python -m pytest models/tests/test_models.py -v
"""

import sys
import importlib.util
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, configure_mappers


# ---------------------------------------------------------------------------
# Load models.py directly by path — bypasses any package __init__ entirely
# so Streamlit is never imported as a side effect.
# ---------------------------------------------------------------------------

_models_path = Path(__file__).resolve().parent.parent / "models.py"

with patch("sqlalchemy.create_engine", return_value=MagicMock()), \
     patch("sqlalchemy.orm.sessionmaker", return_value=MagicMock()):
    spec = importlib.util.spec_from_file_location("models_module", _models_path)
    _mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_mod)

Base = _mod.Base
Songs = _mod.Songs
Artist = _mod.Artist
Genre = _mod.Genre
Performance = _mod.Performance
Tag = _mod.Tag
song_tags = _mod.song_tags


# ---------------------------------------------------------------------------
# Fixtures — in-memory SQLite for real query tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sqlite_engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def session(sqlite_engine):
    """Fresh session per test, always rolled back to keep tests isolated."""
    Session = sessionmaker(bind=sqlite_engine)
    sess = Session()
    yield sess
    sess.rollback()
    sess.close()


# ---------------------------------------------------------------------------
# Songs — @validates
# ---------------------------------------------------------------------------

class TestSongValidators:

    def test_title_strips_and_titlecases(self):
        s = Songs(title="  awesome song  ", artist_id=1, genre_id=1,
                  tempo=120, tone="C", link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")
        assert s.title == "Awesome Song"

    def test_title_none_raises(self):
        with pytest.raises(ValueError, match="Title cannot be None"):
            Songs(title=None, artist_id=1, genre_id=1,
                  tempo=120, tone="C", link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")

    def test_tempo_valid(self):
        s = Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=140, tone="A", link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")
        assert s.tempo == 140

    def test_tempo_none_allowed(self):
        s = Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=None, tone="A", link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")
        assert s.tempo is None

    def test_tempo_negative_raises(self):
        with pytest.raises(ValueError, match="Tempo cannot be negative"):
            Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=-10, tone="A", link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")

    def test_tone_strips_whitespace(self):
        s = Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=120, tone=" Db ", link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")
        assert s.tone == "Db"

    def test_tone_minor_with_dash(self):
        s = Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=120, tone="Bb-", link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")
        assert s.tone == "Bb-"

    @pytest.mark.parametrize("tone", ["C#", "A#", "c", "Am", "Bbm"])
    def test_tone_old_notation_raises(self, tone):
        """Solo bemoles, mayúscula y '-' para menores (C# -> Db, Am -> A-)."""
        with pytest.raises(ValueError, match="Tone is not valid"):
            Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=120, tone=tone, link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")

    def test_tone_invalid_raises(self):
        with pytest.raises(ValueError, match="Tone is not valid"):
            Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=120, tone="Z", link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")

    def test_tone_none_allowed(self):
        s = Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=120, tone=None, link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")
        assert s.tone is None

    def test_link_yt_youtu_be_valid(self):
        s = Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=120, tone="C", link_yt="  https://youtu.be/NUo_aw33vC0  ")
        assert s.link_yt == "https://youtu.be/NUo_aw33vC0"

    def test_link_yt_youtube_watch_valid(self):
        s = Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=120, tone="C",
                  link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")
        assert s.link_yt == "https://www.youtube.com/watch?v=NUo_aw33vC0"

    def test_link_yt_invalid_raises(self):
        with pytest.raises(ValueError, match="Link yt is not valid"):
            Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=120, tone="C", link_yt="https://vimeo.com/123")

    def test_link_yt_short_id_raises(self):
        """Los IDs de YouTube tienen 11 caracteres."""
        with pytest.raises(ValueError, match="Link yt is not valid"):
            Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=120, tone="C", link_yt="https://youtu.be/abc123")

    def test_link_yt_none_raises(self):
        with pytest.raises(ValueError, match="Link yt cannot be None"):
            Songs(title="Test", artist_id=1, genre_id=1,
                  tempo=120, tone="C", link_yt=None)


# ---------------------------------------------------------------------------
# Songs — exists()
# ---------------------------------------------------------------------------

class TestSongExists:

    def _make_song(self, **kwargs):
        defaults = dict(title="Holy Song", artist_id=1, genre_id=1,
                        tempo=120, tone="C", link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")
        defaults.update(kwargs)
        return Songs(**defaults)

    def test_exists_returns_false_when_not_in_db(self, session):
        assert Songs.exists(session, "Holy Song", "https://www.youtube.com/watch?v=NUo_aw33vC0") is False

    def test_exists_returns_true_after_add(self, session):
        s = self._make_song()
        session.add(s)
        session.flush()
        assert Songs.exists(session, "Holy Song", "https://www.youtube.com/watch?v=NUo_aw33vC0") is True

    def test_exists_false_for_different_link(self, session):
        s = self._make_song()
        session.add(s)
        session.flush()
        assert Songs.exists(session, "Holy Song", "https://www.youtube.com/watch?v=dQw4w9WgXcQ") is False

    def test_no_duplicate_added_when_exists(self, session):
        s = self._make_song()
        session.add(s)
        session.flush()

        if not Songs.exists(session, "Holy Song", "https://www.youtube.com/watch?v=NUo_aw33vC0"):
            session.add(self._make_song())
            session.flush()

        count = session.query(Songs).filter_by(title="Holy Song").count()
        assert count == 1


# ---------------------------------------------------------------------------
# Artist — @validates and exists()
# ---------------------------------------------------------------------------

class TestArtist:

    def test_name_strips_and_titlecases(self):
        a = Artist(name="  hillsong united  ")
        assert a.name == "Hillsong United"

    def test_name_none_raises(self):
        with pytest.raises(ValueError, match="Name cannot be None"):
            Artist(name=None)

    def test_exists_false_when_not_in_db(self, session):
        assert Artist.exists(session, "Hillsong United") is False

    def test_exists_true_after_add(self, session):
        a = Artist(name="Hillsong United")
        session.add(a)
        session.flush()
        assert Artist.exists(session, "Hillsong United") is True

    def test_exists_case_sensitive(self, session):
        """Sanitization titlecases on creation; lowercase query should NOT match."""
        a = Artist(name="Elevation Worship")
        session.add(a)
        session.flush()
        assert Artist.exists(session, "elevation worship") is False


# ---------------------------------------------------------------------------
# Genre — @validates (whitelist enforcement)
# ---------------------------------------------------------------------------

class TestGenre:

    def test_valid_genre_alabanza(self):
        g = Genre(name=" alabanza ")
        assert g.name == "Alabanza"

    def test_valid_genre_adoracion(self):
        g = Genre(name="adoración")
        assert g.name == "Adoración"

    def test_invalid_genre_raises(self):
        with pytest.raises(ValueError, match="Genre .* not found"):
            Genre(name="Rock")

    def test_none_genre_raises(self):
        with pytest.raises(ValueError, match="Name cannot be None"):
            Genre(name=None)


# ---------------------------------------------------------------------------
# get_or_create pattern
# ---------------------------------------------------------------------------

def get_or_create_artist(session, name):
    """Helper: returns (Artist_obj, was_created)."""
    instance = session.query(Artist).filter_by(name=name).first()
    if instance:
        return instance, False
    instance = Artist(name=name)
    session.add(instance)
    session.flush()
    return instance, True


class TestGetOrCreate:

    def test_creates_when_not_exists(self, session):
        obj, created = get_or_create_artist(session, "Maverick City")
        assert created is True
        assert obj.name == "Maverick City"

    def test_returns_existing_without_duplicate(self, session):
        get_or_create_artist(session, "Maverick City")
        obj, created = get_or_create_artist(session, "Maverick City")
        assert created is False
        count = session.query(Artist).filter_by(name="Maverick City").count()
        assert count == 1


# ---------------------------------------------------------------------------
# Relaciones entre modelos
# ---------------------------------------------------------------------------

def test_mappers_configure():
    """Falla si un relationship/back_populates apunta a una propiedad que no existe."""
    configure_mappers()


# ---------------------------------------------------------------------------
# Tag — @validates, exists() y relación muchos a muchos con Songs
# ---------------------------------------------------------------------------

class TestTag:

    def _make_song(self):
        return Songs(title="Holy Song", artist_id=1, genre_id=1, tempo=120,
                     tone="C", link_yt="https://www.youtube.com/watch?v=NUo_aw33vC0")

    def test_name_strips_and_titlecases(self):
        assert Tag(name="  navidad  ").name == "Navidad"

    def test_name_none_raises(self):
        with pytest.raises(ValueError, match="Name cannot be None"):
            Tag(name=None)

    def test_name_empty_raises(self):
        with pytest.raises(ValueError, match="Name cannot be empty"):
            Tag(name="   ")

    def test_name_too_long_raises(self):
        with pytest.raises(ValueError, match="longer than 50"):
            Tag(name="a" * 51)

    def test_exists_normalizes_name(self, session):
        session.add(Tag(name="Rápida"))
        session.flush()
        assert Tag.exists(session, " rápida ") is True
        assert Tag.exists(session, "Lenta") is False

    def test_song_with_multiple_tags(self, session):
        song = self._make_song()
        song.tags = [Tag(name="navidad"), Tag(name="rápida")]
        session.add(song)
        session.flush()

        rows = session.execute(song_tags.select().where(song_tags.c.song_id == song.id)).fetchall()
        assert len(rows) == 2
        assert sorted(t.name for t in song.tags) == ["Navidad", "Rápida"]
        assert song.tags[0].songs == [song]

    def test_removing_tag_deletes_link_not_tag(self, session):
        navidad, rapida = Tag(name="navidad"), Tag(name="rápida")
        song = self._make_song()
        song.tags = [navidad, rapida]
        session.add(song)
        session.flush()

        song.tags = [rapida]
        session.flush()

        rows = session.execute(song_tags.select().where(song_tags.c.song_id == song.id)).fetchall()
        assert [r.tag_id for r in rows] == [rapida.id]
        assert Tag.exists(session, "Navidad") is True
