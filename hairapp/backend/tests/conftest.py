from __future__ import annotations

import pytest

from app.domain.evidence.language import ControlledLanguage
from app.domain.rules.engine import RuleEngine
from app.domain.rules.loader import load_all


@pytest.fixture(scope="session")
def language() -> ControlledLanguage:
    return ControlledLanguage.load()


@pytest.fixture(scope="session")
def rules(language: ControlledLanguage):
    return load_all(language=language)


@pytest.fixture(scope="session")
def engine(rules) -> RuleEngine:
    return RuleEngine(rules)
