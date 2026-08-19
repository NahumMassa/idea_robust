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

-- 1. Tabla Maestra: El evento / servicio en sí
CREATE TABLE IF NOT EXISTS performances (
    id SERIAL PRIMARY KEY,
    played_at DATE NOT NULL DEFAULT CURRENT_DATE,
    service_type VARCHAR(50) DEFAULT 'Domingo', -- ej. General, Jóvenes, Ensayo
    notes TEXT

);

-- 2. Tabla Detalle: Las canciones que componen ese setlist
CREATE TABLE IF NOT EXISTS performance_elements (
    id SERIAL PRIMARY KEY,
    performance_id INT NOT NULL REFERENCES performances(id) ON DELETE CASCADE,
    song_id INT NOT NULL REFERENCES canciones(id),
    song_order SMALLINT NOT NULL,              -- 1, 2, 3, 4, 5...
    specific_key VARCHAR(10),                  -- Opcional: si ese día la tocaron en un tono distinto al original
    CONSTRAINT uq_performance_song_order UNIQUE (performance_id, song_order)
);

-- Índices recomendados para búsquedas rápidas
CREATE INDEX idx_performances_played_at ON performances(played_at);
CREATE INDEX idx_performance_elements_perf_id ON performance_elements(performance_id);
CREATE INDEX idx_performance_elements_song_id ON performance_elements(song_id);