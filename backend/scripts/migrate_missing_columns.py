"""
Auto-migration: add columns that exist in SQLAlchemy models but are missing
from the local SQLite database.

This is a development helper. It does not handle column type changes,
constraint changes, or data migration beyond adding nullable columns.
"""

import asyncio
import sqlite3
from pathlib import Path

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.dialects.sqlite import dialect as sqlite_dialect

from app.database import engine
from app.config import get_settings
from app.auth.models import *  # noqa: F401,F403 - register all models with Base
from app.database import Base


async def migrate_missing_columns() -> None:
    settings = get_settings()
    db_url = settings.DATABASE_URL

    if not db_url.startswith("sqlite"):
        print("[migrate] Non-SQLite database; skipping.")
        return

    db_path = db_url.split(":///", 1)[-1]
    if db_path.startswith("./"):
        db_path = db_path[2:]
    db_file = Path(__file__).resolve().parent.parent / db_path

    if not db_file.exists():
        print(f"[migrate] Database file not found at {db_file}; skipping.")
        return

    # Reflect existing tables from the database
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: sa_inspect(sync_conn).get_table_names())

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        added_any = False

        for table_name, table in Base.metadata.tables.items():
            if table_name not in tables:
                # Table does not exist; Base.metadata.create_all should create it.
                continue

            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}

            for column in table.columns:
                if column.name in existing_columns:
                    continue

                # Build SQLite ALTER TABLE ADD COLUMN clause
                col_type = column.type.compile(dialect=sqlite_dialect())
                nullable = "NULL" if column.nullable else "NOT NULL"
                default_clause = ""
                if column.default is not None and hasattr(column.default, "arg"):
                    default_val = column.default.arg
                    if isinstance(default_val, str):
                        default_clause = f" DEFAULT '{default_val}'"
                    else:
                        default_clause = f" DEFAULT {default_val}"
                elif not column.nullable:
                    # SQLite requires a default for NOT NULL columns added to existing tables.
                    # Use type-appropriate fallback.
                    if "INT" in col_type.upper() or "BOOL" in col_type.upper():
                        default_clause = " DEFAULT 0"
                    elif "FLOAT" in col_type.upper() or "DOUBLE" in col_type.upper():
                        default_clause = " DEFAULT 0.0"
                    elif "JSON" in col_type.upper():
                        default_clause = " DEFAULT '[]'"
                    else:
                        default_clause = " DEFAULT ''"

                sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable}{default_clause}"
                try:
                    cursor.execute(sql)
                    print(f"[migrate] {table_name}.{column.name}: added")
                    added_any = True
                except sqlite3.OperationalError as exc:
                    print(f"[migrate] {table_name}.{column.name}: skipped ({exc})")

        if added_any:
            conn.commit()
            print("[migrate] Migration complete.")
        else:
            print("[migrate] No missing columns found.")
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_missing_columns())
