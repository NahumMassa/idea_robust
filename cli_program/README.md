# Setlist Uploader

A local web app for formatting and uploading worship setlists to the PostgreSQL database for the **IDEA Mérida Ministerio de Alabanza** system.

This replaces the old terminal-based CLI. The uploader runs as a **Streamlit page on localhost** — paste your setlist, see a live preview, pick the date, and upload with one click.

---

## Features

- **Live Preview**: Instantly see songs, artists, and links in a formatted table as you type.
- **Date Picker**: Defaults to the next upcoming Sunday automatically; override with any date.
- **Validation**: Upload button is locked until songs / artists / links counts match.
- **Database Safety**: Uses SQLAlchemy models — `get_or_create` for artists, deduplication for songs and performances.
- **One-click Upload**: Artists → Songs → Performances inserted in the correct dependency order, with full rollback on error.

---

## Setup & Prerequisites

Make sure your `.env` file at the project root has the DB credentials:

```env
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

---

## Running

### With Docker (recommended)

The `uploader` service is defined in `docker/docker-compose.yml` and runs on port **8502**.

```bash
# Start only the uploader (and its DB dependency)
docker compose -f docker/docker-compose.yml up uploader

# Or start everything
docker compose -f docker/docker-compose.yml up
```

Then open **http://localhost:8502** in your browser.

### Locally (without Docker)

```bash
# From the project root
venv/bin/streamlit run cli_program/upload_app.py
```

Then open **http://localhost:8501** in your browser.

---

## Setlist Format

Paste your setlist into the text area using this format — three sections separated by `---`:

```
Song title 1
Song title 2
Song title 3
---
Artist 1
Artist 2
Artist 3
---
https://youtu.be/...
https://youtu.be/...
https://youtu.be/...
```

> **Important:** Each section must have the **same number of lines** — one song, one artist, and one link per row, in the same order.

### Supported link formats

| Format | Example |
|---|---|
| Short YouTube | `https://youtu.be/abc123` |
| Full YouTube | `https://www.youtube.com/watch?v=abc123` |

---

## File Structure

```
cli_program/
├── upload_app.py       # Streamlit upload UI (entry point)
├── upload.py           # DB logic: get_or_create, rollback, session management
├── format_setlist.py   # Pure text parser (no DB imports)
└── README.md
```

---

## Architecture

| File | Responsibility |
|---|---|
| `upload_app.py` | UI only — collects input, renders preview, triggers upload |
| `upload.py` | DB only — artists → songs → performances, handles duplicates and rollback |
| `format_setlist.py` | Text parsing only — no DB imports, no side effects |
| `models/` | SQLAlchemy models with `@validates` sanitization and `exists()` helpers |
