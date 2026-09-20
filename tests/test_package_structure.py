"""Package-structure tests.

Guards against the packaging regression where ``core/`` and ``api/routes/``
lacked ``__init__.py``: with setuptools' ``find_packages`` that silently
dropped those subpackages from a non-editable build.
"""

from __future__ import annotations

from pathlib import Path

import oe_infrastructure

PACKAGE_ROOT = Path(oe_infrastructure.__file__).resolve().parent


def test_all_package_dirs_have_init() -> None:
    missing = [
        str(path.relative_to(PACKAGE_ROOT.parent))
        for path in PACKAGE_ROOT.rglob("*")
        if path.is_dir()
        and "__pycache__" not in path.parts
        and not any(child.suffix == ".py" for child in path.iterdir())
        and not (path / "__init__.py").is_file()
    ]
    assert missing == [], f"directories with .py files but no __init__.py: {missing}"


def test_core_and_routes_are_importable_packages() -> None:
    import oe_infrastructure.api.routes  # noqa: F401
    import oe_infrastructure.core  # noqa: F401
    import oe_infrastructure.core.security  # noqa: F401


def test_core_does_not_duplicate_role_enum() -> None:
    from oe_infrastructure.core.security import Role
    from oe_infrastructure.modules import enums

    assert not hasattr(enums, "Role"), "Role must live only in core.security"
    assert Role.PLATFORM_ADMIN.value == "platform_admin"
