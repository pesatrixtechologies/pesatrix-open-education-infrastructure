"""PESATRIX Open Education Infrastructure.

Reusable, secure, interoperable digital infrastructure for structured
educational events and information in low-resource environments.
"""

__all__ = [
    "create_app",
    "__version__",
    "__title__",
]

__title__ = "pesatrix-open-education-infrastructure"
__version__ = "0.1.0"

from oe_infrastructure.main import create_app