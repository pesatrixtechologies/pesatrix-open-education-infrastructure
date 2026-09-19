"""PESATRIX Open Education Infrastructure.

Reusable, secure, interoperable digital infrastructure for structured
educational events and information in low-resource environments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = [
    "create_app",
    "__version__",
    "__title__",
]

__title__ = "pesatrix-open-education-infrastructure"
__version__ = "0.1.0"

if TYPE_CHECKING:
    from oe_infrastructure.main import create_app


def __getattr__(name: str) -> object:
    """Lazily expose ``create_app`` without importing the app at package load.

    Importing eagerly would create a circular import (``main`` imports ``api``,
    which imports the route modules). PEP 562 lazy attributes keep
    ``from oe_infrastructure import create_app`` working on demand.
    """
    if name == "create_app":
        from oe_infrastructure.main import create_app

        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
