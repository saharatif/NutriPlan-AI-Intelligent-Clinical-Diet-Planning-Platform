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
os.environ["OPENAI_API_KEY"] = ""
os.environ["DIET_PLAN_GENERATION_PROVIDER"] = "deterministic"
os.environ["MISTRAL_API_KEY"] = ""

# Patch RecipeService.lookup_recipe_url so tests never hit the network.
# The patch is applied at import time before any test collects.
from unittest.mock import AsyncMock, patch as _patch  # noqa: E402

_patch(
    "services.recipe_service.RecipeService.lookup_recipe_url",
    new=AsyncMock(return_value="https://www.themealdb.com/meal/52772"),
).start()

# Prevent Celery from trying to connect to Redis during tests
from unittest.mock import MagicMock as _MagicMock  # noqa: E402
_patch("workers.task_medical_profile.build_medical_profile.delay", new=_MagicMock()).start()
