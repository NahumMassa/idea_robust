# CLI Setlist Manager




A command-line tool designed to format setlists and upload them directly to the PostgreSQL database for the **IDEA Mérida Ministerio de Alabanza** system.

This program provides an interactive, terminal-based editor (`nano`) to safely input, preview, and persist performance data, ensuring database normalization constraints and unique key indices are respected.

---

## Features
- **Format Mode**: Preview formatted lists of songs, artists, and links in a clean terminal table before saving.
- **Upload Mode**: Automatically batch-inserts artists, songs, and performance details.
- **Database Safety**: Resolves foreign keys using optimized subqueries and handles unique constraints safely (i.e. `ON CONFLICT DO NOTHING`).
- **Flexible Dates**: Defaults to the next upcoming Sunday date automatically, with support for custom manual dates.

---

## Setup & Prerequisites
Make sure you have your environment variables set up in your `.env` file at the root of the repository:

```env
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

Ensure your python virtual environment is active and psycopg2 dependencies are installed.

---

## Usage

Run the program from the repository root:
```bash
docker compose -f docker/docker-compose.yml run --rm cli --mode upload

python cli_program/setlistcli.py [OPTIONS]
```

### Running with Docker

Since the program is integrated into your `docker/docker-compose.yml`, you can run it inside a Docker container without setting up a local Python environment.

Run the service using `docker compose run` (pointing to the compose file, which will mount your workspace so scripts update dynamically, keep stdin open, and allocate a tty so `nano` works):

```bash
docker compose -f docker/docker-compose.yml run --rm cli [OPTIONS]
```

#### Examples:
* **Format only:** `docker compose -f docker/docker-compose.yml run --rm cli --mode format`
* **Upload for Sunday:** `docker compose -f docker/docker-compose.yml run --rm cli --mode upload`
* **Upload for a manual date:** `docker compose -f docker/docker-compose.yml run --rm cli --mode upload --date 2026-01-01`

### CLI Options

| Argument | Choices / Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--mode` | `format`, `upload` | `format` | Operation mode. `format` displays a preview; `upload` persists data to the database. |
| `--date` | `YYYY-MM-DD` | `None` | Optional manual date. If omitted, defaults to the upcoming Sunday. |
| `-h, --help` | | | Show the help message and exit. |

---

## Detailed Guide

### Step 1: Executing the Command
To parse and upload a setlist for the upcoming Sunday, run:
```bash
python cli_program/setlistcli.py --mode upload
```

### Step 2: Filling out the Template
The CLI will automatically launch a temporary instance of the `nano` editor in your terminal displaying a blueprint:

```text
#title
----
#artist
----
#link
----
```

Write down the songs, artists, and YouTube links underneath each header in the **exact same order** (separated by lines).

#### Example:
```text
Por el poder de tu amor
Cantos de Júbilo
----
Ingrid Rosario
Jaime Murrel
----
https://youtu.be/Tssk5UWxvuw
https://youtu.be/wchrgDmxzXw
```

* **Save & Exit**: Press `Ctrl + O`, then press `Enter` to confirm, and finally press `Ctrl + X` to exit.

---

## Example Usage Commands

### 1. Previewing a Setlist (Format Only)
Validates and prints the formatted setlist in a table without uploading to the database.
```bash
python cli_program/setlistcli.py --mode format
```
**Output Example:**
```text
*CANCIÓN* | *ARTISTA* | *LINK*
--------------------
> Por el poder de tu amor | Ingrid Rosario | https://youtu.be/Tssk5UWxvuw
> Cantos de Júbilo | Jaime Murrel | https://youtu.be/wchrgDmxzXw
```

### 2. Uploading for Next Sunday (Default)
Loads the setlist and calculates the upcoming Sunday automatically for the `played_at` date.
```bash
python cli_program/setlistcli.py --mode upload
```

### 3. Uploading with a Manual Date
Overrides the default Sunday calculation and logs the performance on a specific date (e.g. `2026-01-01`).
```bash
python cli_program/setlistcli.py --mode upload --date 2026-01-01
```
