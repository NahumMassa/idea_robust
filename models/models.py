

from datetime import datetime
import re 

from sqlalchemy import Column, Integer, String, Date, Float, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, validates, relationship
from sqlalchemy import create_engine

from os import getenv
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)


user = getenv("DB_USER")
password = getenv("DB_PASSWORD")
host = getenv("DB_HOST")
port = getenv("DB_PORT")
db_name = getenv("DB_NAME")


engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db_name}')


Base = declarative_base()
Session = sessionmaker(engine)
session = Session()

TONALIDADES = [
    # Mayores
    "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B",
    # Menores (con formato '-')
    "C-", "Db-", "D-", "Eb-", "E-", "F-", "Gb-", "G-", "Ab-", "A-", "Bb-", "B-"
]


class Songs(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    artist_id = Column(Integer)
    genre_id = Column(Integer)
    tempo = Column(Integer)
    tone = Column(String)
    link_yt = Column(String)

    @classmethod
    def exists(cls, session, title, link_yt):
        return session.query(Songs).filter(Songs.title == title, Songs.link_yt == link_yt).first() is not None

    @validates("title")
    def sanitize_title(self,key,value):
        if value is None:
            raise ValueError("Title cannot be None")
        return value.strip().title()

    @validates("tempo")
    def sanitize_tempo(self,key,value):
        if value is None:
            return None  # optional at upload time
        if value < 0:
            raise ValueError("Tempo cannot be negative")
        return value

    @validates("tone")
    def sanitize_tone(self,key,value):
        if value is None:
            return None  # optional at upload time
        value = value.strip().upper()
        if value not in TONALIDADES:
            raise ValueError("Tone is not valid")
        return value

    @validates("link_yt")
    def sanitize_link_yt(self, key, value):
        if value is None:
            raise ValueError("Link yt cannot be None")
        value = value.strip()
        yt_pattern = re.compile(
            r'(?:https?:\/\/)?'                           # Protocolo opcional
            r'(?:www\.|m\.)?'                             # Subdominios opcionales (www, m)
            r'(?:'
                r'youtu\.be\/'                            # Formato corto: youtu.be/<id>
                r'|youtube\.com\/(?:'
                    r'watch\?(?:.*&)?v='                  # Formato estándar: youtube.com/watch?v=<id>
                    r'|embed\/'                           # Formato embed: youtube.com/embed/<id>
                    r'|v\/'                               # Formato legacy: youtube.com/v/<id>
                    r'|shorts\/'                          # Formato Shorts: youtube.com/shorts/<id>
                    r'|live\/'                            # Formato Live: youtube.com/live/<id>
                r')'
            r')'
            r'([a-zA-Z0-9_-]{11})'                        # Grupo de captura: ID de 11 caracteres
            r'(?:[^\s]*)?',                               # Parámetros adicionales en la query string (&t=..., etc.)
            re.IGNORECASE
        )

        match = yt_pattern.search(value)
        if not match:
            raise ValueError("Link yt is not valid")
        return match.group(0)
    __str__ = lambda self: f'title {self.title}, artist_id {self.artist_id}, genre_id {self.genre_id}, tempo {self.tempo}, tone {self.tone}, link_yt {self.link_yt}'

class Artist(Base):
    __tablename__ = "artist"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    @classmethod
    def exists(cls, session, name):
        return session.query(Artist).filter(Artist.name == name).first() is not None

    @validates("name")
    def sanitize_name(self,key,value):
        if value is None:
            raise ValueError("Name cannot be None")
        return value.strip().title()
    

    __str__ = lambda self: f'name {self.name}, id {self.id}'

class Genre(Base):
    __tablename__ = "genre"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    @validates("name")
    def sanitize_name(self, key, value):
        if value is None:
            raise ValueError("Name cannot be None")
        value = value.strip().title()
        if value not in ["Alabanza", "Adoración"]:
            raise ValueError(f"Genre {value} not found")
        return value

    __str__ = lambda self: f'name {self.name}, id {self.id}'

class Performance(Base):
    __tablename__ = "performances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    played_at = Column(Date, default=datetime.utcnow, nullable=False)
    service_type = Column(String(50), default="Domingo")
    notes = Column(Text, nullable=True)

    # Relación uno a muchos con cascade para borrar elementos si se borra el performance
    elements = relationship(
        "PerformanceElement", 
        back_populates="performance", 
        cascade="all, delete-orphan",
        order_by="PerformanceElement.song_order"
    )

    @validates("played_at")
    def sanitize_played_at(self, key, value):
        if value is None:
            raise ValueError("Played at cannot be None")
        return value

class PerformanceElement(Base):
    __tablename__ = "performance_elements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    performance_id = Column(Integer, ForeignKey("performances.id", ondelete="CASCADE"), nullable=False)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    song_order = Column(Integer, nullable=False)
    specific_key = Column(String(10), nullable=True)

    # Relaciones para navegar entre objetosz
    performance = relationship("Performance", back_populates="elements")
    song = relationship("Songs")

    @validates("song_order")
    def sanitize_song_order(self, key, value):
        if value is None:
            raise ValueError("Song order cannot be None")
        if value < 0:
            raise ValueError("Song order cannot be negative")
        return value

if __name__ == '__main__':
    print('TEST, QUERY SONGS-------------------')
    print(session.query(Songs).first())
    song = Songs(
        title="Dummy song for test345",
        artist_id=1,
        genre_id=1,
        tempo=125,
        tone="C-",
        link_yt="https://youtu.be/xXh0JZvjQSY?si=uH7vfKTJw2KjBaDW"
    )
    print(session.add(song))
    session.commit()
    print('TEST, ARTIST SONG -------------------')
    print(session.query(Artist).first())
    print('TEST, GENRE SONG -------------------')
    print(session.query(Genre).first())
    print('TEST, PERFORMANCE SONG --------------------')
    print(session.query(Performance).first())
