"""
Regression tests for CORS middleware ordering (Issue #92).

CorsMiddleware must be positioned BEFORE CommonMiddleware in the MIDDLEWARE
list to ensure preflight (OPTIONS) requests receive proper CORS headers.
These tests guard against accidental reordering.

These tests inspect the settings module directly (pure Python, no Django
app-registry boot required) so they run fast and without external deps.
"""

import importlib
import os
import sys
import types
from typing import List

import pytest


CORS_MIDDLEWARE = "corsheaders.middleware.CorsMiddleware"
COMMON_MIDDLEWARE = "django.middleware.common.CommonMiddleware"


@pytest.fixture(scope="module")
def middleware_list() -> List[str]:
    """Load the MIDDLEWARE list from assessment_service.settings.

    We set the required env-var so the module can be imported without
    raising ``RuntimeError``, then import it as a plain Python module
    (no ``django.setup()``) to read the ``MIDDLEWARE`` constant.
    """
    os.environ.setdefault("ASSIGNMENT_SERVICE_SECRET_KEY", "test-secret-key")

    # Stub out heavy optional deps that settings.py may transitively import
    # but are irrelevant for reading the MIDDLEWARE list.
    stubs_needed = []
    for mod_name in ("dotenv",):
        if mod_name not in sys.modules:
            stub = types.ModuleType(mod_name)
            stub.load_dotenv = lambda *a, **kw: None  # type: ignore[attr-defined]
            sys.modules[mod_name] = stub
            stubs_needed.append(mod_name)

    settings_mod = importlib.import_module("assessment_service.settings")
    middleware: List[str] = list(settings_mod.MIDDLEWARE)  # type: ignore[attr-defined]

    # Clean up stubs
    for mod_name in stubs_needed:
        sys.modules.pop(mod_name, None)

    return middleware


class TestCorsMiddlewareOrder:
    """Ensure CorsMiddleware is correctly positioned in MIDDLEWARE."""

    def test_cors_middleware_is_present(self, middleware_list: List[str]) -> None:
        """CorsMiddleware must be included in the MIDDLEWARE list."""
        assert CORS_MIDDLEWARE in middleware_list, (
            f"{CORS_MIDDLEWARE} is missing from MIDDLEWARE"
        )

    def test_common_middleware_is_present(self, middleware_list: List[str]) -> None:
        """CommonMiddleware must be included in the MIDDLEWARE list (sanity check)."""
        assert COMMON_MIDDLEWARE in middleware_list, (
            f"{COMMON_MIDDLEWARE} is missing from MIDDLEWARE"
        )

    def test_cors_middleware_before_common_middleware(
        self, middleware_list: List[str]
    ) -> None:
        """CorsMiddleware must appear before CommonMiddleware."""
        cors_index = middleware_list.index(CORS_MIDDLEWARE)
        common_index = middleware_list.index(COMMON_MIDDLEWARE)
        assert cors_index < common_index, (
            f"CorsMiddleware (index {cors_index}) must come before "
            f"CommonMiddleware (index {common_index})"
        )

    def test_cors_middleware_is_first_or_second(
        self, middleware_list: List[str]
    ) -> None:
        """CorsMiddleware should be at position 0 or 1 (best practice)."""
        cors_index = middleware_list.index(CORS_MIDDLEWARE)
        assert cors_index <= 1, (
            f"CorsMiddleware is at position {cors_index}; "
            f"it should be at position 0 or 1 for correct CORS handling"
        )
