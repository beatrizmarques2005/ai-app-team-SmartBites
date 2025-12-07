"""Adapted Supabase configuration (copy of `calls/supabase_config.py`).

This module intentionally does NOT re-run the original initialization logic
found in `calls/supabase_config.py`. Instead it re-exports the centralized
client present in `src.db.client` and provides safe helpers that let devs
inspect migration SQL and run it manually in their Supabase dashboard.

Do NOT modify `calls/supabase_config.py` as requested; this file is a
workspace-local, safe adapter placed under `src/db` for library-style
imports.
"""
from pathlib import Path
from typing import Optional

try:
    # Re-export the canonical client created in `src.db.client`
    from src.db.client import supabase  # type: ignore
except Exception:
    # If the client cannot be imported (tests or missing deps), provide a placeholder
    from types import SimpleNamespace

    supabase = SimpleNamespace()


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def get_migration_sql(name: str = "001_init.sql") -> Optional[str]:
    """Return the SQL for the named migration, or None if not found."""
    p = MIGRATIONS_DIR / name
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def list_migrations() -> list:
    """List migration filenames available under `src/db/migrations/`."""
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted([p.name for p in MIGRATIONS_DIR.iterdir() if p.suffix == ".sql"])


__all__ = ["supabase", "get_migration_sql", "list_migrations"]
