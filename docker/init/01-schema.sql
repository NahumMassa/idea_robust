CREATE TABLE IF NOT EXISTS artist (
    id SERIAL PRIMARY KEY,
    name VARCHAR(60) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS genre (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS songs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(60),
    artist_id INTEGER REFERENCES artist(id),
    genre_id INTEGER REFERENCES genre(id),
    tempo INTEGER CHECK (tempo > 0),
    tone VARCHAR(10),
    link_yt TEXT,
    UNIQUE (title, link_yt)
);

CREATE TABLE IF NOT EXISTS performance (
    id SERIAL PRIMARY KEY,
    song_id INTEGER REFERENCES songs(id),
    artist_id INTEGER REFERENCES artist(id),
    played_at DATE DEFAULT CURRENT_DATE,
    UNIQUE (played_at, song_id)
);
