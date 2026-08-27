"""El dominio es Python puro (docs/01-ARCHITECTURE.md §1).

Sin esta garantía, el motor acabaría atado a FastAPI y a la base de datos, y
dejaría de poder ejecutarse en el dispositivo o probarse sin infraestructura.
"""

from __future__ import annotations

import ast
from pathlib import Path

DOMAIN_ROOT = Path(__file__).resolve().parents[1] / "app" / "domain"

FORBIDDEN_PREFIXES = (
    "fastapi",
    "sqlalchemy",
    "alembic",
    "starlette",
    "requests",
    "httpx",
    "boto3",
    "redis",
    "psycopg",
    "app.models",
    "app.services",
    "app.api",
    "app.db",
)


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.append(node.module)
    return found


def test_domain_has_no_infrastructure_imports() -> None:
    offenders: list[str] = []
    for path in DOMAIN_ROOT.rglob("*.py"):
        for module in _imports(path):
            if module.startswith(FORBIDDEN_PREFIXES):
                offenders.append(f"{path.relative_to(DOMAIN_ROOT)} importa {module}")
    assert not offenders, "\n".join(offenders)


def test_domain_is_importable_without_any_service_running() -> None:
    """Se importa entero sin base de datos, sin red y sin variables de entorno."""
    import importlib

    for path in DOMAIN_ROOT.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        relative = path.relative_to(DOMAIN_ROOT.parents[1])
        module = str(relative.with_suffix("")).replace("/", ".")
        importlib.import_module(module)
