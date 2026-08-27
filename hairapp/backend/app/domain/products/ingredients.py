"""Análisis de ingredientes por función, no por listas de "bueno/malo" (A11).

El error que este módulo existe para no cometer: juzgar un ingrediente aislado.
"Silicona = malo" es falso porque agrupa moléculas con comportamientos opuestos
(unas se enjuagan con un champú suave, otras no). Lo que importa es la función,
la posición en el INCI y la coherencia con el resto de la rutina.
"""

from __future__ import annotations

import enum
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field


class Function(enum.Enum):
    """Qué hace un ingrediente en la formulación."""

    ANIONIC_SURFACTANT = "anionic_surfactant"
    AMPHOTERIC_SURFACTANT = "amphoteric_surfactant"
    NONIONIC_SURFACTANT = "nonionic_surfactant"
    CATIONIC_CONDITIONER = "cationic_conditioner"
    EMOLLIENT = "emollient"
    OCCLUSIVE = "occlusive"
    HUMECTANT = "humectant"
    FILM_FORMER = "film_former"
    HYDROLYSED_PROTEIN = "hydrolysed_protein"
    SILICONE_SOLUBLE = "silicone_soluble"
    SILICONE_INSOLUBLE = "silicone_insoluble"
    CHELATOR = "chelator"
    PRESERVATIVE = "preservative"
    SOLVENT = "solvent"
    ALCOHOL_DRYING = "alcohol_drying"
    ALCOHOL_FATTY = "alcohol_fatty"
    OIL_PENETRATING = "oil_penetrating"
    OIL_SEALING = "oil_sealing"
    UV_FILTER = "uv_filter"
    PH_ADJUSTER = "ph_adjuster"
    FRAGRANCE = "fragrance"
    COLOURANT = "colourant"
    THICKENER = "thickener"
    OTHER = "other"

    @property
    def label_key(self) -> str:
        return f"ingredient.function.{self.value}"


@dataclass(frozen=True)
class Ingredient:
    inci_name: str
    functions: tuple[Function, ...]
    notes_key: str | None = None
    common_name_key: str | None = None

    @property
    def is_silicone(self) -> bool:
        return bool(
            {Function.SILICONE_SOLUBLE, Function.SILICONE_INSOLUBLE} & set(self.functions)
        )


#: Reglas de clasificación por patrón de nombre INCI. Se aplican en orden; la
#: primera que casa decide. Las excepciones van antes que la regla general.
_PATTERNS: tuple[tuple[str, tuple[Function, ...]], ...] = (
    # Siliconas solubles: los prefijos PEG-/PPG- y los copolioles llevan
    # cadenas de óxido de etileno que las hacen dispersables en agua.
    (r"^(peg|ppg)-\d+.*(dimethicone|methicone|silox)", (Function.SILICONE_SOLUBLE,)),
    (r"dimethicone copolyol", (Function.SILICONE_SOLUBLE,)),
    (r"(dimethicone|amodimethicone|cyclopentasiloxane|cyclomethicone|trimethicone|"
     r"phenyl trimethicone|silox|silicone)", (Function.SILICONE_INSOLUBLE,)),
    # Tensioactivos
    (r"(sodium|ammonium) (lauryl|laureth|myreth|coco) sulfate", (Function.ANIONIC_SURFACTANT,)),
    (r"(olefin sulfonate|sulfosuccinate|isethionate|taurate|sarcosinate)",
     (Function.ANIONIC_SURFACTANT,)),
    (r"(cocamidopropyl betaine|sultaine|hydroxysultaine|amphoacetate|amphodiacetate)",
     (Function.AMPHOTERIC_SURFACTANT,)),
    (r"(decyl|lauryl|coco) glucoside", (Function.NONIONIC_SURFACTANT,)),
    # Acondicionadores catiónicos
    (r"(behentrimonium|cetrimonium|steartrimonium|dicetyldimonium|quaternium|polyquaternium|"
     r"guar hydroxypropyltrimonium)", (Function.CATIONIC_CONDITIONER,)),
    # Alcoholes: la distinción que más confusión causa
    (r"(cetyl|cetearyl|stearyl|behenyl|myristyl) alcohol", (Function.ALCOHOL_FATTY, Function.EMOLLIENT)),
    (r"^(alcohol denat|sd alcohol|isopropyl alcohol|ethanol|alcohol)$", (Function.ALCOHOL_DRYING,)),
    # Humectantes
    (r"(glycerin|propanediol|propylene glycol|butylene glycol|sorbitol|panthenol|"
     r"sodium pca|hyaluronate|honey|urea)", (Function.HUMECTANT,)),
    # Proteínas hidrolizadas
    (r"hydrolyzed (wheat|soy|rice|keratin|silk|corn|oat|quinoa|collagen)",
     (Function.HYDROLYSED_PROTEIN,)),
    (r"(keratin amino acids|amino acids)", (Function.HYDROLYSED_PROTEIN,)),
    # Aceites: penetrantes vs. selladores. La diferencia es real y accionable.
    (r"(cocos nucifera|coconut oil)", (Function.OIL_PENETRATING, Function.EMOLLIENT)),
    (r"(olea europaea|olive oil|persea gratissima|avocado oil|babassu)",
     (Function.OIL_PENETRATING, Function.EMOLLIENT)),
    (r"(simmondsia chinensis|jojoba|ricinus communis|castor oil|argania|argan|"
     r"helianthus|sunflower|grape seed|vitis vinifera)", (Function.OIL_SEALING, Function.EMOLLIENT)),
    (r"(butyrospermum|shea butter|theobroma|cocoa butter|mangifera)",
     (Function.OCCLUSIVE, Function.EMOLLIENT)),
    (r"(petrolatum|mineral oil|paraffinum liquidum|lanolin)", (Function.OCCLUSIVE,)),
    # Formadores de película / fijación
    (r"(vp/va copolymer|pvp|acrylates copolymer|vinyl|polyurethane|"
     r"hydroxyethylcellulose|carbomer)", (Function.FILM_FORMER,)),
    (r"(linum usitatissimum|flaxseed|aloe barbadensis)", (Function.FILM_FORMER, Function.HUMECTANT)),
    # Quelantes
    (r"(edta|etidronic|phytic acid|sodium gluconate|citric acid)", (Function.CHELATOR,)),
    # Filtros UV
    (r"(benzophenone|ethylhexyl methoxycinnamate|octocrylene|polysilicone-15)",
     (Function.UV_FILTER,)),
    # Conservantes, fragancia y resto
    (r"(phenoxyethanol|benzyl alcohol|sodium benzoate|potassium sorbate|"
     r"methylisothiazolinone|dmdm hydantoin)", (Function.PRESERVATIVE,)),
    (r"^(parfum|fragrance|aroma|limonene|linalool|citral|geraniol)", (Function.FRAGRANCE,)),
    (r"^(aqua|water|eau)$", (Function.SOLVENT,)),
    (r"(xanthan gum|cellulose|hectorite|silica)$", (Function.THICKENER,)),
    (r"(ci \d{5}|hc (blue|yellow|red))", (Function.COLOURANT,)),
)

_COMPILED = tuple((re.compile(pattern), functions) for pattern, functions in _PATTERNS)


def classify(inci_name: str) -> tuple[Function, ...]:
    """Clasifica un ingrediente por su nombre INCI.

    Devuelve `(Function.OTHER,)` cuando no reconoce el ingrediente. No adivina:
    un ingrediente desconocido se declara desconocido y no cuenta ni a favor ni
    en contra en el análisis.
    """
    name = inci_name.strip().lower()
    for pattern, functions in _COMPILED:
        if pattern.search(name):
            return functions
    return (Function.OTHER,)


def parse_inci(raw: str) -> list[Ingredient]:
    """Parsea una lista INCI tal como aparece en el envase.

    El orden importa: en una lista INCI los ingredientes van por concentración
    decreciente hasta el 1%, y eso es lo que permite distinguir "lleva proteína"
    de "lleva una pizca de proteína al final para poder ponerlo en la etiqueta".
    """
    parts = [p.strip() for p in re.split(r"[,\n;]+", raw) if p.strip()]
    ingredients = []
    for part in parts:
        cleaned = re.sub(r"\s*\(.*?\)\s*", " ", part).strip().strip(".")
        cleaned = re.sub(r"\s+", " ", cleaned)
        if not cleaned:
            continue
        ingredients.append(Ingredient(inci_name=cleaned, functions=classify(cleaned)))
    return ingredients


@dataclass(frozen=True)
class FunctionProfile:
    """Resumen funcional de una formulación, ponderado por posición."""

    weights: dict[Function, float] = field(default_factory=dict)
    unknown_count: int = 0
    total_count: int = 0

    def weight(self, function: Function) -> float:
        return self.weights.get(function, 0.0)

    def has(self, function: Function, *, threshold: float = 0.02) -> bool:
        return self.weight(function) >= threshold

    @property
    def unknown_ratio(self) -> float:
        return self.unknown_count / self.total_count if self.total_count else 0.0

    def as_dict(self) -> dict[str, float]:
        return {f.value: round(w, 4) for f, w in sorted(self.weights.items(), key=lambda kv: -kv[1])}


def function_profile(ingredients: Sequence[Ingredient]) -> FunctionProfile:
    """Peso relativo de cada función según la posición en el INCI.

    El peso decae con la posición porque la concentración también lo hace. No
    es una medida de concentración real — no la tenemos — sino un ordenamiento
    honesto: lo que va primero pesa más que lo que va al final.
    """
    if not ingredients:
        return FunctionProfile()

    weights: dict[Function, float] = {}
    total_weight = 0.0
    unknown = 0

    for index, ingredient in enumerate(ingredients):
        positional = 1.0 / (index + 1) ** 0.7
        total_weight += positional
        if ingredient.functions == (Function.OTHER,):
            unknown += 1
        for function in ingredient.functions:
            weights[function] = weights.get(function, 0.0) + positional

    normalised = {f: w / total_weight for f, w in weights.items()}
    return FunctionProfile(weights=normalised, unknown_count=unknown, total_count=len(ingredients))


@dataclass(frozen=True)
class IngredientFinding:
    """Un hallazgo del análisis. Nunca un veredicto de "bueno/malo"."""

    key: str
    function: Function | None
    severity: str  # "info" | "attention" | "conflict"
    params: dict[str, object] = field(default_factory=dict)


def analyse(
    ingredients: Sequence[Ingredient],
    *,
    porosity: str | None = None,
    uses_only_gentle_cleansing: bool = False,
) -> list[IngredientFinding]:
    """Analiza una formulación **en su contexto**, no ingrediente a ingrediente.

    Los hallazgos son condicionales por diseño: una silicona no soluble solo es
    un problema si la rutina no incluye nada capaz de retirarla.
    """
    profile = function_profile(ingredients)
    findings: list[IngredientFinding] = []

    if profile.has(Function.SILICONE_INSOLUBLE, threshold=0.03):
        if uses_only_gentle_cleansing:
            findings.append(
                IngredientFinding(
                    key="finding.insoluble_silicone_without_matching_cleanser",
                    function=Function.SILICONE_INSOLUBLE,
                    severity="conflict",
                    params={"weight": round(profile.weight(Function.SILICONE_INSOLUBLE), 3)},
                )
            )
        else:
            findings.append(
                IngredientFinding(
                    key="finding.insoluble_silicone_needs_matching_cleanser",
                    function=Function.SILICONE_INSOLUBLE,
                    severity="info",
                )
            )

    if profile.has(Function.HYDROLYSED_PROTEIN, threshold=0.05):
        findings.append(
            IngredientFinding(
                key="finding.notable_protein_content",
                function=Function.HYDROLYSED_PROTEIN,
                severity="attention",
                params={"weight": round(profile.weight(Function.HYDROLYSED_PROTEIN), 3)},
            )
        )

    if profile.has(Function.ALCOHOL_DRYING, threshold=0.06):
        findings.append(
            IngredientFinding(
                key="finding.drying_alcohol_high_position",
                function=Function.ALCOHOL_DRYING,
                severity="attention",
            )
        )

    if profile.has(Function.ALCOHOL_FATTY) and profile.has(Function.ALCOHOL_DRYING):
        findings.append(
            IngredientFinding(
                key="finding.both_alcohol_types_present",
                function=None,
                severity="info",
            )
        )

    if porosity == "low" and profile.weight(Function.OCCLUSIVE) > 0.08:
        findings.append(
            IngredientFinding(
                key="finding.heavy_occlusives_on_low_porosity",
                function=Function.OCCLUSIVE,
                severity="attention",
            )
        )

    if porosity == "high" and profile.weight(Function.HUMECTANT) > 0.12:
        findings.append(
            IngredientFinding(
                key="finding.high_humectant_context_dependent",
                function=Function.HUMECTANT,
                severity="info",
            )
        )

    if profile.unknown_ratio > 0.4:
        findings.append(
            IngredientFinding(
                key="finding.many_unrecognised_ingredients",
                function=None,
                severity="info",
                params={"unknown_ratio": round(profile.unknown_ratio, 2)},
            )
        )

    return findings


def summarise_functions(ingredients: Iterable[Ingredient]) -> dict[str, list[str]]:
    """Agrupa los ingredientes por función, para mostrarlos explicados."""
    grouped: dict[str, list[str]] = {}
    for ingredient in ingredients:
        for function in ingredient.functions:
            grouped.setdefault(function.value, []).append(ingredient.inci_name)
    return grouped
