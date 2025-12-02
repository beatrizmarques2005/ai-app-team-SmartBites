"""Workspace sanity check script.

Runs import checks for all modules under `src`, reports import errors,
verifies presence of common environment variables, and smoke-tests
Streamlit demo imports. Exit code 0 if all checks pass, 2 if issues
were detected.
"""
import sys
from pathlib import Path
import importlib
import os
import traceback

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'

sys.path.insert(0, str(ROOT))

failures = []

print(f"Scanning Python modules under: {SRC}")

for path in SRC.rglob('*.py'):
    # skip tests, __pycache__, and entrypoints
    if any(part.startswith('__') for part in path.parts):
        continue
    # compute module path
    rel = path.relative_to(ROOT)
    parts = list(rel.with_suffix('').parts)
    # skip scripts or top-level CLI files
    if parts[0] in ('tests', 'scripts'):
        continue
    mod_name = '.'.join(parts)
    try:
        importlib.import_module(mod_name)
        print(f"OK: {mod_name}")
    except Exception as e:
        print(f"FAIL: {mod_name} -> {e.__class__.__name__}: {e}")
        traceback.print_exc()
        failures.append((mod_name, str(e)))

print('\nEnvironment variable checks:')
vars_to_check = [
    'DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_ANON_KEY',
    'OPENAI_API_KEY', 'GOOGLE_API_KEY'
]
for v in vars_to_check:
    print(f"- {v}: {'SET' if os.environ.get(v) else 'MISSING'}")

print('\nStreamlit import smoke test:')
try:
    import importlib
    st = importlib.import_module('streamlit')
    # If the installed streamlit is a stub or very old/modified, it may
    # lack the familiar UI functions. In that case skip importing the demo
    # modules (they are optional) and report a warning instead of failing.
    if not hasattr(st, 'title') or not hasattr(st, 'set_page_config'):
        print('Streamlit is present but does not expose standard UI APIs; skipping demo import (warning).')
    else:
        # try importing the demo app modules
        importlib.import_module('streamlit_bea.App')
        importlib.import_module('streamlit_bea._common')
        print('Streamlit and demo modules imported OK')
except Exception as e:
    print(f'Streamlit/demo import failed: {e.__class__.__name__}: {e}')
    traceback.print_exc()
    failures.append(('streamlit_import', str(e)))

if failures:
    print(f"\nCompleted with {len(failures)} failures.")
    sys.exit(2)
else:
    print('\nAll import checks passed.')
    sys.exit(0)
