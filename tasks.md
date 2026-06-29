Viewed add_data.py
Viewed setlist_domingo.py:1-104
Listed directory init
Viewed 01-schema.sql:1-29

The best and most secure approach to solve this is to implement **Database Role Separation** coupled with **Streamlit connection gating** and **Admin Authentication**. 

Here is the architectural overview of how to set this up:

---

### Step 1: Database Level (PostgreSQL Role Separation)
In your database, you create two distinct users:
1. **`postgres` (or `db_user` from `.env`)**: The superuser/owner with full Write (CRUD) privileges. Only the admin/upload scripts use this.
2. **`viewer_user`**: A read-only user that can only perform `SELECT` statements.

You can configure this in your database initialization SQL script (`docker/init/01-schema.sql`):
```sql
-- Create read-only user
CREATE USER viewer_user WITH PASSWORD 'viewer_password';

-- Grant read privileges
GRANT CONNECT ON DATABASE postgres TO viewer_user;
GRANT USAGE ON SCHEMA public TO viewer_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO viewer_user;

-- Ensure future tables are also read-only
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO viewer_user;
```

---

### Step 2: Connection Level (`secrets.toml` Configuration)
In Streamlit, you define **two separate database connections** in your `.streamlit/secrets.toml`.

Your `entrypoint.py` script (which generates this file dynamically) can be configured to write both connections:
```toml
# Default public connection (Read-Only)
[connections.postgres_read]
dialect = "postgresql"
host = "db"
port = 5432
database = "postgres"
username = "viewer_user"
password = "viewer_password"

# Admin connection (Read/Write)
[connections.postgres_write]
dialect = "postgresql"
host = "db"
port = 5432
database = "postgres"
username = "postgres"  # or DB_USER from .env
password = "idea_robust_password_123"  # or DB_PASSWORD from .env
```

---

### Step 3: Application Level (Streamlit Gating)

Since the Streamlit server runs in the cloud or container and has access to *both* keys, you must prevent public visitors from accessing the write connection.

1. **Public Pages** (like `dashboard.py` and standard views):
   Use the read-only connection:
   ```python
   conn = st.connection("postgres_read", type="sql")
   ```

2. **Admin/Write Pages** (like `pages/add_data.py`):
   Gate the page with a simple password field (read from environment/secrets) before letting anyone see the form or execute updates using the write connection:

   ```python
   import streamlit as st

   st.title("Agregar Nueva Canción")

   # Simple admin password gate
   admin_password = st.text_input("Contraseña de Administrador", type="password")

   if admin_password == st.secrets.get("ADMIN_PASSWORD", "admin123"):
       st.success("Acceso concedido.")
       
       # Use the write connection
       conn = st.connection("postgres_write", type="sql")
       
       # ... Draw form here ...
       if st.button("Subir canción"):
           conn.execute("INSERT INTO ...")
           st.success("Guardado con éxito!")
   else:
       st.warning("Introduce la contraseña de administrador para añadir datos.")
   ```

---

### Would you like me to implement this?
If you'd like, I can:
1. Update `docker/init/01-schema.sql` to create the read-only database user automatically.
2. Update `entrypoint.py` to write both `postgres_read` and `postgres_write` configurations to `secrets.toml`.
3. Set up the template logic for your `pages/add_data.py` page.