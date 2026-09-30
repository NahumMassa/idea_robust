-- Normaliza los tonos a la notación de models.TONALIDADES:
--   * sin espacios alrededor          (' G'  -> 'G',   'B- ' -> 'B-')
--   * bemoles en lugar de sostenidos  ('C#-' -> 'Db-', 'G#-' -> 'Ab-')
--   * menores con '-'
--
-- Se puede correr más de una vez (idempotente). Si al final queda algún tono
-- fuera de la notación, la transacción se revierte y no se aplica nada.
--
-- Uso (respaldar antes):
--   docker exec idea_robust_db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup_$(date +%F).sql
--   docker exec -i idea_robust_db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < docker/migrations/001_fix_tone_notation.sql

BEGIN;

-- 1. Espacios. Un tono vacío queda como NULL (el validador lo permite).
UPDATE songs
SET tone = NULLIF(btrim(tone), '')
WHERE tone <> btrim(tone) OR btrim(tone) = '';

UPDATE performance_elements
SET specific_key = NULLIF(btrim(specific_key), '')
WHERE specific_key <> btrim(specific_key) OR btrim(specific_key) = '';

-- 2. Sostenidos -> bemoles (conserva el '-' de los menores)
UPDATE songs s
SET tone = m.flat || substr(s.tone, 3)
FROM (VALUES ('C#', 'Db'), ('D#', 'Eb'), ('F#', 'Gb'), ('G#', 'Ab'), ('A#', 'Bb')) AS m(sharp, flat)
WHERE left(s.tone, 2) = m.sharp;

UPDATE performance_elements pe
SET specific_key = m.flat || substr(pe.specific_key, 3)
FROM (VALUES ('C#', 'Db'), ('D#', 'Eb'), ('F#', 'Gb'), ('G#', 'Ab'), ('A#', 'Bb')) AS m(sharp, flat)
WHERE left(pe.specific_key, 2) = m.sharp;

-- 3. Verificación: todo tono debe estar en TONALIDADES
DO $$
DECLARE
    valid_tones TEXT[] := ARRAY[
        'C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B',
        'C-', 'Db-', 'D-', 'Eb-', 'E-', 'F-', 'Gb-', 'G-', 'Ab-', 'A-', 'Bb-', 'B-'
    ];
    invalid TEXT;
BEGIN
    SELECT string_agg(DISTINCT quote_literal(t), ', ') INTO invalid
    FROM (
        SELECT tone AS t FROM songs WHERE tone IS NOT NULL
        UNION ALL
        SELECT specific_key FROM performance_elements WHERE specific_key IS NOT NULL
    ) all_tones
    WHERE t <> ALL(valid_tones);

    IF invalid IS NOT NULL THEN
        RAISE EXCEPTION 'Tonos fuera de la notación, revisar a mano: %', invalid;
    END IF;
END $$;

COMMIT;
