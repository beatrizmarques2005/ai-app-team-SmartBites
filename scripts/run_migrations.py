"""Safe migration helper for SmartBites.

This script DOES NOT run SQL automatically by default. It lists SQL migrations
found in `src/db/migrations/` and writes a combined SQL file that you can run
manually in the Supabase SQL editor. If you really want to attempt an automatic
run, you must provide `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in your
environment and have the `supabase` Python client installed; even then the
script will prompt for confirmation.

Usage (PowerShell):
  .\project-env\Scripts\Activate.ps1
  python .\scripts\run_migrations.py

The script is intentionally conservative to avoid accidental schema changes.
"""
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = Path(ROOT / "src" / "db" / "migrations")
OUT = Path(__file__).resolve().parent / "combined_migrations.sql"


def list_migrations():
    if not MIGRATIONS.exists():
        return []
    return sorted([p for p in MIGRATIONS.iterdir() if p.suffix == '.sql'])


def combine_sql(paths):
    parts = []
    for p in paths:
        parts.append(f"-- Migration: {p.name}\n")
        parts.append(p.read_text(encoding='utf-8'))
        parts.append('\n\n')
    return '\n'.join(parts)


def main():
    migs = list_migrations()
    if not migs:
        print('No migrations found under src/db/migrations')
        return

    print('Found migrations:')
    for m in migs:
        print('-', m.name)

    combined = combine_sql(migs)
    print('\nWriting combined SQL to', OUT)
    OUT.write_text(combined, encoding='utf-8')

    print('\nYou can now open this file and run it in the Supabase SQL editor:')
    print(OUT)

    # Optional: attempt to run using supabase client
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print('\nSUPABASE_URL or SUPABASE_SERVICE_KEY not found in environment.')
        print('To attempt an automated run set these env vars and re-run the script.')
        return

    try:
        from supabase import create_client
    except Exception as e:
        print(f'Unable to import supabase client: {e}')
        print('Install the supabase package to attempt an automated apply.')
        return

    confirm = input('\nAttempt to run combined SQL against Supabase now? (yes/no): ').strip().lower()
    if confirm not in ('y', 'yes'):
        print('Aborting automatic run.')
        return

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print('Running SQL via Supabase...')
    # Supabase Python client doesn't expose a direct "run SQL" method in every version.
    # For safety we use the REST SQL API via the project's SQL editor endpoint is not
    # directly available. Therefore we fallback to attempting a simple insert test to
    # check connectivity and then instruct the user to run the combined SQL in the
    # SQL editor if automatic execution is not possible.
    try:
        # test connectivity by calling the project's REST endpoint (simple table listing)
        resp = client.table('users').select('*').limit(1).execute()
        print('Connectivity test OK. Please run the SQL in the Supabase SQL editor:')
        print(OUT)
    except Exception as e:
        print('Connectivity test failed:', e)
        print('Automatic SQL execution is not supported by this safe runner. Run the SQL manually in the Supabase SQL editor.')


if __name__ == '__main__':
    main()
