import os
from pathlib import Path

# Extract environment variables with fallback defaults
db_user = os.environ.get("DB_USER") or "postgres"
db_password = os.environ.get("DB_PASSWORD") or "idea_robust_password_123"
db_host = os.environ.get("DB_HOST") or "db"
db_port = os.environ.get("DB_PORT") or "5432"
db_name = os.environ.get("DB_NAME") or "postgres"

# Generate the connection URL
url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Ensure .streamlit directory exists in root folder and write secrets
secrets_dir = Path(".streamlit")
secrets_dir.mkdir(parents=True, exist_ok=True)
secrets_file = secrets_dir / "secrets.toml"

# Write the secrets.toml configuration file
content = f"""[postgres]
DB_NAME = "{db_name}"
DB_USER = "{db_user}"
DB_PASSWORD = "{db_password}"
DB_HOST = "{db_host}"
DB_PORT = {db_port}

[connections.postgres]
dialect = "postgresql"
host = "{db_host}"
port = {db_port}
database = "{db_name}"
username = "{db_user}"
password = "{db_password}"
"""

secrets_file.write_text(content)

# Ensure .streamlit directory exists in dashboard folder and write secrets
dashboard_secrets_dir = Path("dashboard/.streamlit")
dashboard_secrets_dir.mkdir(parents=True, exist_ok=True)
dashboard_secrets_file = dashboard_secrets_dir / "secrets.toml"
dashboard_secrets_file.write_text(content)

print(f"entrypoint.py: Generated secrets.toml in root and dashboard pointing to {db_host}:{db_port}")

