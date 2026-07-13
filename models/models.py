

from datetime import datetime


from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base, validates
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
        if value not in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]:
            raise ValueError("Tone is not valid")
        return value

    @validates("link_yt")
    def sanitize_link_yt(self,key,value):
        if value is None:
            raise ValueError("Link yt cannot be None")
        value = value.strip()
        if not value.startswith("https://youtu.be/") and not value.startswith("https://www.youtube.com/watch?v="):
            raise ValueError("Link yt is not valid")
        return value
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
    __tablename__ = "performance"
    id = Column(Integer, primary_key=True)
    song_id = Column(Integer)
    played_at = Column(DateTime)

    __str__ = lambda self: f'song_id {self.song_id}, played_at {self.played_at}'


if __name__ == '__main__':
    print('TEST, QUERY SONGS-------------------')
    print(session.query(Songs).first())
    song = Songs(
        title="Dummy song for test",
        artist_id=1,
        genre_id=1,
        tempo=125,
        tone="C",
        link_yt="https://youtu.be/ZS7st5oNSWU?si=cBTdmBE8dsB-LBaGS",
    )
    print(session.add(song))
    session.commit()
    print('TEST, ARTIST SONG -------------------')
    print(session.query(Artist).first())
    print('TEST, GENRE SONG -------------------')
    print(session.query(Genre).first())
    print('TEST, PERFORMANCE SONG --------------------')
    print(session.query(Performance).first())
