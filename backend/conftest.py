"""
Top-level conftest — runs before any test module is imported.
Sets the environment variables the app requires so tests work without a real
Supabase project or PostgreSQL instance.
"""
import os

# Use SQLite for the test suite — fast, zero-config, no external service needed.
# Must be set before database.py is imported (the guard fires at module level).
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test-nutriplan.db")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret-for-pytest-minimum-32-chars!!")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
