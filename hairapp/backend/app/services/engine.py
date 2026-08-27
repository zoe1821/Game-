"""Instancias compartidas del motor de dominio.

Se cargan una vez al arrancar: los packs de reglas se validan en ese momento,
así que un pack inválido **impide arrancar** en vez de fallar en la primera
petición de un usuario.
"""

from __future__ import annotations

from functools import lru_cache

from ..domain.evidence.language import ControlledLanguage
from ..domain.routine.generator import RoutineGenerator
from ..domain.rules.engine import RuleEngine
from ..domain.rules.loader import load_all
from ..domain.scan.pipeline import ScanPipeline


@lru_cache
def get_language() -> ControlledLanguage:
    return ControlledLanguage.load()


@lru_cache
def get_rule_engine() -> RuleEngine:
    return RuleEngine(load_all(language=get_language()))


@lru_cache
def get_routine_generator() -> RoutineGenerator:
    return RoutineGenerator(get_rule_engine())


@lru_cache
def get_scan_pipeline() -> ScanPipeline:
    return ScanPipeline()
