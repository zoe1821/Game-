from app.domain.products.catalog import (
    InventoryItem,
    Product,
    SurfactantStrength,
)
from app.domain.products.ingredients import (
    Function,
    analyse,
    classify,
    function_profile,
    parse_inci,
)
from app.domain.products.matching import MatchOutcome, compare, match_for_step
from app.domain.products.routine_analysis import analyse_routine
from app.domain.routine.amounts import ProductCategory as C


def test_soluble_and_insoluble_silicones_are_not_the_same_thing() -> None:
    """El mito «silicona = malo» agrupa moléculas con comportamiento opuesto."""
    assert classify("PEG-12 Dimethicone") == (Function.SILICONE_SOLUBLE,)
    assert classify("Dimethicone") == (Function.SILICONE_INSOLUBLE,)
    assert classify("Dimethicone Copolyol") == (Function.SILICONE_SOLUBLE,)


def test_fatty_and_drying_alcohols_are_not_the_same_thing() -> None:
    assert Function.ALCOHOL_FATTY in classify("Cetearyl Alcohol")
    assert classify("Alcohol Denat") == (Function.ALCOHOL_DRYING,)


def test_unknown_ingredients_are_declared_not_guessed() -> None:
    assert classify("Xylotrophic Unobtainium Extract") == (Function.OTHER,)


def test_inci_position_changes_the_weight() -> None:
    """Proteína en segunda posición no es lo mismo que proteína al final."""
    early = function_profile(parse_inci("Aqua, Hydrolyzed Wheat Protein, Glycerin, Parfum"))
    late = function_profile(parse_inci("Aqua, Glycerin, Parfum, Hydrolyzed Wheat Protein"))
    assert early.weight(Function.HYDROLYSED_PROTEIN) > late.weight(Function.HYDROLYSED_PROTEIN)


def test_analysis_is_contextual_not_a_verdict() -> None:
    ingredients = parse_inci("Aqua, Dimethicone, Glycerin, Phenoxyethanol")
    with_gentle = {f.key for f in analyse(ingredients, uses_only_gentle_cleansing=True)}
    with_capable = {f.key for f in analyse(ingredients, uses_only_gentle_cleansing=False)}
    assert "finding.insoluble_silicone_without_matching_cleanser" in with_gentle
    assert "finding.insoluble_silicone_without_matching_cleanser" not in with_capable


def test_attributes_are_derived_from_the_formulation() -> None:
    strong = Product.from_inci(
        inci="Aqua, Sodium Lauryl Sulfate, Cocamidopropyl Betaine, Tetrasodium EDTA",
        id="s", brand="b", name="n", category=C.CLARIFYING_SHAMPOO,
    )
    assert strong.surfactant_strength is SurfactantStrength.STRONG
    assert strong.chelating

    gentle = Product.from_inci(
        inci="Aqua, Cocamidopropyl Betaine, Decyl Glucoside, Glycerin",
        id="g", brand="b", name="n", category=C.SHAMPOO,
    )
    assert gentle.surfactant_strength is SurfactantStrength.MILD


def test_inventory_comes_first_and_blocks_purchase_suggestions() -> None:
    """A15: si ya lo tienes y sirve, no se recomienda comprar nada."""
    owned = Product.from_inci(
        inci="Aqua, VP/VA Copolymer, PVP, Glycerin", id="own", brand="", name="mi gel", category=C.GEL
    )
    catalog = [
        Product.from_inci(
            inci="Aqua, Acrylates Copolymer, PVP, Glycerin", id="shop", brand="X", name="gel", category=C.GEL
        )
    ]
    result = match_for_step(
        category=C.GEL,
        wanted_attributes={"film_forming": True, "hold_level": ["medium", "strong"]},
        inventory=[InventoryItem(id="i1", product=owned)],
        catalog=catalog,
    )
    assert result.outcome is MatchOutcome.ALREADY_OWNED
    assert result.suggestions == ()


def test_partial_inventory_match_states_exactly_what_is_missing() -> None:
    weak = Product.from_inci(
        inci="Aqua, Glycerin, Phenoxyethanol", id="own", brand="", name="agua con glicerina", category=C.GEL
    )
    result = match_for_step(
        category=C.GEL,
        wanted_attributes={"film_forming": True},
        inventory=[InventoryItem(id="i1", product=weak)],
        catalog=[],
    )
    assert result.outcome is MatchOutcome.OWNED_PARTIAL
    assert "film_forming" in result.unmet_attributes


def test_disliked_or_empty_inventory_items_are_skipped() -> None:
    product = Product.from_inci(
        inci="Aqua, PVP, Glycerin", id="own", brand="", name="gel", category=C.GEL
    )
    for item in (
        InventoryItem(id="i1", product=product, disliked=True),
        InventoryItem(id="i2", product=product, amount_left_ratio=0.0),
    ):
        result = match_for_step(
            category=C.GEL, wanted_attributes={"film_forming": True}, inventory=[item], catalog=[]
        )
        assert result.outcome is not MatchOutcome.ALREADY_OWNED


def test_match_reports_unknown_attributes_instead_of_assuming() -> None:
    product = Product.from_inci(inci="Aqua, PVP", id="p", brand="", name="", category=C.GEL)
    result = match_for_step(
        category=C.GEL,
        wanted_attributes={"nonexistent_attribute": True},
        inventory=[InventoryItem(id="i", product=product)],
        catalog=[],
    )
    unknown = result.from_inventory[0].unknown if result.from_inventory else ()
    assert result.outcome in {MatchOutcome.OWNED_PARTIAL, MatchOutcome.UNVERIFIABLE} or unknown


def test_no_single_percentage_score_is_exposed() -> None:
    """A11: nada de «97 % de compatibilidad». Esa cifra no existiría de verdad."""
    from app.domain.products.matching import ProductMatch

    assert not hasattr(ProductMatch, "score")
    assert not hasattr(ProductMatch, "compatibility")


def test_routine_analysis_flags_the_silicone_cowash_trap() -> None:
    products = [
        Product.from_inci(
            inci="Aqua, Cetearyl Alcohol, Behentrimonium Chloride", id="cw", brand="", name="", category=C.CO_WASH
        ),
        Product.from_inci(
            inci="Aqua, Dimethicone, Glycerin", id="li", brand="", name="", category=C.LEAVE_IN
        ),
    ]
    keys = {f.key for f in analyse_routine(products).findings}
    assert "routine.insoluble_silicone_without_capable_cleanser" in keys


def test_routine_analysis_detects_stacked_protein() -> None:
    products = [
        Product.from_inci(
            inci=f"Aqua, Hydrolyzed {p} Protein, Glycerin", id=f"p{i}", brand="", name="", category=cat
        )
        for i, (p, cat) in enumerate(
            [("Wheat", C.LEAVE_IN), ("Silk", C.CREAM), ("Rice", C.GEL)]
        )
    ]
    findings = analyse_routine(products).findings
    protein = next(f for f in findings if f.key == "routine.protein_stacked_across_layers")
    assert protein.params["layers_with_protein"] == 3
    assert protein.suggestion_key


def test_comparison_is_limited_and_highlights_real_differences() -> None:
    import pytest

    a = Product.from_inci(inci="Aqua, PVP", id="a", brand="", name="", category=C.GEL)
    b = Product.from_inci(inci="Aqua, Glycerin", id="b", brand="", name="", category=C.GEL)
    rows = compare([a, b])
    assert any(r.differs for r in rows)
    with pytest.raises(ValueError):
        compare([a, b, a, b, a])
