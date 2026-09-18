from pathlib import Path
import mysql.connector
from config import DB_CONFIG


SCHEMA_FILE = Path(__file__).resolve().parent / "database" / "database.sql"


def initialize_database():
    """Create the database and all tables required by the application."""
    config = DB_CONFIG.copy()
    database_name = config.pop("database")

    # First connect without selecting a database so a fresh installation works.
    server = mysql.connector.connect(**config)
    cursor = server.cursor()
    try:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        server.commit()
    finally:
        cursor.close()
        server.close()

    # Execute each CREATE statement separately because mysql.connector does not
    # need multi-statement mode for this schema.
    db_config = config.copy()
    db_config["database"] = database_name
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    try:
        sql = SCHEMA_FILE.read_text(encoding="utf-8")
        statements = []
        current = []
        for line in sql.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("--"):
                continue
            current.append(line)
            if stripped.endswith(";"):
                statements.append("\n".join(current).strip()[:-1])
                current = []

        for statement in statements:
            if statement.upper().startswith("CREATE DATABASE") or statement.upper().startswith("USE "):
                continue
            cur.execute(statement)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    initialize_database()
    print("DATABASE INITIALIZATION SUCCESS")
