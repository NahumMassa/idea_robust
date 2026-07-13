
from datetime import datetime


from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base 
from sqlalchemy import create_engine

from os import getenv
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
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


class songs(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    artist_id = Column(Integer)
    genre_id = Column(Integer)
    tempo = Column(Integer)
    tone = Column(String)
    link_yt = Column(String)

    __str__ = lambda self: f'title {self.title}, artist_id {self.artist_id}, genre_id {self.genre_id}, tempo {self.tempo}, tone {self.tone}, link_yt {self.link_yt}'

class artist(Base):
    __tablename__ = "artist"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    __str__ = lambda self: f'name {self.name}, id {self.id}'

class genre(Base):
    __tablename__ = "genre"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    __str__ = lambda self: f'name {self.name}, id {self.id}'

class performance(Base):
    __tablename__ = "performance"
    id = Column(Integer, primary_key=True)
    song_id = Column(Integer)
    played_at = Column(DateTime)

    __str__ = lambda self: f'song_id {self.song_id}, played_at {self.played_at}'


if __name__ == '__main__':
    print('TEST, QUERY SONGS-------------------')
    print(session.query(songs).first())
    song = songs(
        title="Dummy song for test",
        artist_id=1,
        genre_id=1,
        tempo=125,
        tone="C",
        link_yt="https://youtu.be/ZS7st5oNSWU?si=cBTdmBE8dB-LBaGS",
    )
    print(session.add(song))
    session.commit()
    print('TEST, ARTIST SONG -------------------')
    print(session.query(artist).first())
    print('TEST, GENRE SONG -------------------')
    print(session.query(genre).first())
    print('TEST, PERFORMANCE SONG --------------------')
    print(session.query(performance).first())
