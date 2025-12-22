"""
Supabase Client Module
----------------------

This module exposes a `supabase` symbol for use across `src`.

Behaviour:
- If the `supabase` Python package is available and `SUPABASE_URL`/`SUPABASE_KEY`
  are set, a real client will be created.
- Otherwise a lightweight placeholder is exported so imports do not fail during
  unit tests or in environments without the dependency. Code that actually
  performs DB operations should handle the placeholder case gracefully.

"""
import os
from types import SimpleNamespace
try:
    from supabase import create_client  # type: ignore
except Exception:
    create_client = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

if not supabase:
    supabase = SimpleNamespace() # placeholder so modules can import without the real client.

__all__ = ["supabase"]
