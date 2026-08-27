"""Motor experimental personal (A25).

El tercer pilar del producto: la app no pretende saber la respuesta, ayuda a
averiguarla. La persona define un experimento (crema+gel vs. solo gel), la app
estructura las repeticiones, comprueba que las variables que se dijeron fijas
lo estén de verdad, y lee el resultado con honestidad estadística.

La parte difícil no es comparar medias: es **negarse a concluir** cuando la
muestra no da o cuando el propio experimento se ejecutó mal.
"""

from __future__ import annotations

import enum
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from ..common import Explanation, clamp
from ..learning.journal import JournalEntry


class ExperimentStatus(enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    READY_TO_READ = "ready_to_read"
    CONCLUDED = "concluded"
    INVALID = "invalid"
    """El experimento no se ejecutó como se definió: no se lee, se dice por qué."""


@dataclass(frozen=True)
class ExperimentArm:
    """Una condición del experimento."""

    id: str
    label_key: str
    product_ids: tuple[str, ...] = ()
    technique_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Experiment:
    id: str
    question_key: str
    arms: tuple[ExperimentArm, ...]
    controlled_variables: tuple[str, ...] = ()
    """Lo que la persona se compromete a mantener igual: `dew_point`,
    `wash_frequency`, `other_products`, `techniques`..."""
    target_repetitions_per_arm: int = 4
    status: ExperimentStatus = ExperimentStatus.DRAFT

    def __post_init__(self) -> None:
        if len(self.arms) < 2:
            raise ValueError("un experimento necesita al menos dos condiciones que comparar")


@dataclass(frozen=True)
class ArmResult:
    arm_id: str
    label_key: str
    n: int
    mean_rating: float
    std_dev: float
    mean_longevity_days: float


@dataclass(frozen=True)
class ProtocolIssue:
    """Algo que se salió del protocolo. Se reporta, no se ignora."""

    key: str
    arm_id: str | None
    params: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ExperimentReading:
    """La lectura del experimento. Puede perfectamente ser «no concluyente»."""

    experiment_id: str
    status: ExperimentStatus
    arms: tuple[ArmResult, ...]
    winner_arm_id: str | None
    difference: float
    effect_size: float
    is_distinguishable_from_noise: bool
    protocol_issues: tuple[ProtocolIssue, ...]
    explanation: Explanation

    @property
    def is_conclusive(self) -> bool:
        return (
            self.status is ExperimentStatus.CONCLUDED
            and self.winner_arm_id is not None
            and self.is_distinguishable_from_noise
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "experiment_id": self.experiment_id,
            "status": self.status.value,
            "arms": [
                {
                    "arm_id": a.arm_id,
                    "label_key": a.label_key,
                    "n": a.n,
                    "mean_rating": round(a.mean_rating, 2),
                    "std_dev": round(a.std_dev, 2),
                    "mean_longevity_days": round(a.mean_longevity_days, 1),
                }
                for a in self.arms
            ],
            "winner_arm_id": self.winner_arm_id,
            "difference": round(self.difference, 2),
            "effect_size": round(self.effect_size, 2),
            "is_distinguishable_from_noise": self.is_distinguishable_from_noise,
            "is_conclusive": self.is_conclusive,
            "protocol_issues": [
                {"key": i.key, "arm_id": i.arm_id, "params": dict(i.params)}
                for i in self.protocol_issues
            ],
            "explanation": self.explanation.as_dict(),
        }


#: Mínimo de repeticiones por condición para leer el resultado. Por debajo, la
#: app dice cuántas faltan en vez de dar un ganador provisional.
MIN_REPETITIONS = 3

#: Diferencia de punto de rocío que rompe el control de la variable clima.
DEW_POINT_TOLERANCE_C = 5.0


def read_experiment(
    experiment: Experiment,
    entries: Sequence[JournalEntry],
) -> ExperimentReading:
    by_arm: dict[str, list[JournalEntry]] = {arm.id: [] for arm in experiment.arms}
    for entry in entries:
        if entry.experiment_arm_id in by_arm:
            by_arm[entry.experiment_arm_id].append(entry)

    issues = _protocol_issues(experiment, by_arm)

    insufficient = [
        arm.id for arm in experiment.arms if len(by_arm[arm.id]) < MIN_REPETITIONS
    ]
    if insufficient:
        return _incomplete(experiment, by_arm, issues, insufficient)

    results = tuple(
        _summarise(arm, by_arm[arm.id]) for arm in experiment.arms
    )
    ranked = sorted(results, key=lambda r: r.mean_rating, reverse=True)
    best, runner_up = ranked[0], ranked[1]

    best_values = _ratings(by_arm[best.arm_id])
    runner_values = _ratings(by_arm[runner_up.arm_id])
    effect = _cohens_d(best_values, runner_values)
    difference = best.mean_rating - runner_up.mean_rating

    # "Distinguible del ruido" en lugar de "significativo": no hacemos un
    # contraste de hipótesis formal con n=4, y decir "p<0.05" sería falso.
    # El criterio es que la diferencia supere la dispersión interna.
    pooled_spread = (best.std_dev + runner_up.std_dev) / 2
    distinguishable = abs(effect) >= 0.8 and abs(difference) > max(pooled_spread * 0.5, 0.25)

    blocking = [i for i in issues if i.key in _BLOCKING_ISSUES]
    if blocking:
        status = ExperimentStatus.INVALID
        winner = None
        distinguishable = False
    else:
        status = ExperimentStatus.CONCLUDED
        winner = best.arm_id if distinguishable else None

    uncertainty: list[str] = ["uncertainty.small_sample_experiment"]
    if not distinguishable:
        uncertainty.append("uncertainty.difference_within_noise")
    uncertainty += [f"uncertainty.protocol.{i.key}" for i in issues]
    missing_controls = set(_ALL_CONTROLS) - set(experiment.controlled_variables)
    uncertainty += [f"uncertainty.uncontrolled.{v}" for v in sorted(missing_controls)]

    explanation = Explanation(
        summary_key=(
            "experiment.reading.conclusive"
            if winner
            else "experiment.reading.inconclusive"
            if status is ExperimentStatus.CONCLUDED
            else "experiment.reading.invalid"
        ),
        inputs_used=("input.experiment_entries",),
        observations=tuple(f"{r.arm_id}: n={r.n}, media={r.mean_rating:.2f}" for r in results),
        evidence_level="extended_anecdote",
        evidence_confidence=0.45,
        personal_confidence=_personal_confidence(results, effect, bool(blocking)),
        sample_size=sum(r.n for r in results),
        uncertainty_keys=tuple(dict.fromkeys(uncertainty)),
        alternatives=("experiment.alternative.more_repetitions",) if not winner else (),
        params={
            "controlled_variables": list(experiment.controlled_variables),
            "uncontrolled_variables": sorted(missing_controls),
        },
    )

    return ExperimentReading(
        experiment_id=experiment.id,
        status=status,
        arms=results,
        winner_arm_id=winner,
        difference=difference,
        effect_size=effect,
        is_distinguishable_from_noise=distinguishable,
        protocol_issues=tuple(issues),
        explanation=explanation,
    )


_ALL_CONTROLS = ("dew_point", "other_products", "techniques", "wash_frequency")

#: Problemas que invalidan la lectura en vez de solo restarle confianza.
_BLOCKING_ISSUES = frozenset({"arms_share_no_common_baseline", "declared_control_broken"})


def _protocol_issues(
    experiment: Experiment, by_arm: Mapping[str, Sequence[JournalEntry]]
) -> list[ProtocolIssue]:
    issues: list[ProtocolIssue] = []

    if "dew_point" in experiment.controlled_variables:
        means: dict[str, float] = {}
        for arm_id, entries in by_arm.items():
            values = [e.dew_point_c for e in entries if e.dew_point_c is not None]
            if values:
                means[arm_id] = sum(values) / len(values)
        if len(means) >= 2 and (max(means.values()) - min(means.values())) > DEW_POINT_TOLERANCE_C:
            issues.append(
                ProtocolIssue(
                    key="declared_control_broken",
                    arm_id=None,
                    params={
                        "variable": "dew_point",
                        "spread_c": round(max(means.values()) - min(means.values()), 1),
                    },
                )
            )

    if "other_products" in experiment.controlled_variables:
        arm_products = {
            arm.id: {p for e in by_arm[arm.id] for p in e.product_ids}
            for arm in experiment.arms
        }
        declared = {arm.id: set(arm.product_ids) for arm in experiment.arms}
        for arm_id, observed in arm_products.items():
            unexpected = observed - declared[arm_id] - _shared(declared)
            if unexpected:
                issues.append(
                    ProtocolIssue(
                        key="unexpected_products_used",
                        arm_id=arm_id,
                        params={"products": sorted(unexpected)},
                    )
                )

    for arm in experiment.arms:
        entries = by_arm[arm.id]
        if entries and len(entries) < experiment.target_repetitions_per_arm:
            issues.append(
                ProtocolIssue(
                    key="fewer_repetitions_than_planned",
                    arm_id=arm.id,
                    params={"done": len(entries), "planned": experiment.target_repetitions_per_arm},
                )
            )

    return issues


def _shared(declared: Mapping[str, set[str]]) -> set[str]:
    sets = list(declared.values())
    if not sets:
        return set()
    common = set(sets[0])
    for other in sets[1:]:
        common &= other
    return common


def _incomplete(
    experiment: Experiment,
    by_arm: Mapping[str, Sequence[JournalEntry]],
    issues: Sequence[ProtocolIssue],
    insufficient: Sequence[str],
) -> ExperimentReading:
    results = tuple(_summarise(arm, by_arm[arm.id]) for arm in experiment.arms)
    missing = {
        arm_id: MIN_REPETITIONS - len(by_arm[arm_id])
        for arm_id in insufficient
    }
    explanation = Explanation(
        summary_key="experiment.reading.not_enough_yet",
        inputs_used=("input.experiment_entries",),
        observations=tuple(f"{r.arm_id}: n={r.n}" for r in results),
        evidence_level="extended_anecdote",
        evidence_confidence=0.45,
        personal_confidence=0.0,
        sample_size=sum(r.n for r in results),
        uncertainty_keys=("uncertainty.experiment_incomplete",),
        alternatives=("experiment.alternative.more_repetitions",),
        params={"missing_repetitions": missing},
    )
    return ExperimentReading(
        experiment_id=experiment.id,
        status=ExperimentStatus.RUNNING,
        arms=results,
        winner_arm_id=None,
        difference=0.0,
        effect_size=0.0,
        is_distinguishable_from_noise=False,
        protocol_issues=tuple(issues),
        explanation=explanation,
    )


def _summarise(arm: ExperimentArm, entries: Sequence[JournalEntry]) -> ArmResult:
    values = _ratings(entries)
    longevity = [float(e.longevity_days) for e in entries]
    return ArmResult(
        arm_id=arm.id,
        label_key=arm.label_key,
        n=len(entries),
        mean_rating=_mean(values),
        std_dev=_std_dev(values),
        mean_longevity_days=_mean(longevity),
    )


def _ratings(entries: Sequence[JournalEntry]) -> list[float]:
    return [e.mean_rating for e in entries if e.mean_rating is not None]


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std_dev(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))


def _cohens_d(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) < 2 or len(b) < 2:
        return 0.0
    mean_a, mean_b = _mean(a), _mean(b)
    var_a = sum((x - mean_a) ** 2 for x in a) / (len(a) - 1)
    var_b = sum((x - mean_b) ** 2 for x in b) / (len(b) - 1)
    pooled = math.sqrt(((len(a) - 1) * var_a + (len(b) - 1) * var_b) / (len(a) + len(b) - 2))
    if pooled == 0:
        difference = mean_a - mean_b
        return 0.0 if difference == 0 else math.copysign(3.0, difference)
    return clamp((mean_a - mean_b) / pooled, low=-3.0, high=3.0)


def _personal_confidence(
    results: Sequence[ArmResult], effect: float, invalid: bool
) -> float:
    if invalid:
        return 0.0
    total = sum(r.n for r in results)
    size_factor = 1.0 - math.exp(-total / 10.0)
    effect_factor = clamp(abs(effect) / 1.2)
    # Un experimento controlado vale más que la misma cantidad de observación
    # suelta, pero sigue siendo n pequeño: el techo es deliberadamente bajo.
    return clamp(size_factor * effect_factor * 1.15, high=0.85)
