from app.engine.schemes import match_government_schemes


def test_bakery_matches_pmfme_and_pmegp():
    matches = match_government_schemes(
        category_key="bakery",
        archetype="takeaway",
        startup_cost=800_000,
        is_new=True,
        settlement_type="urban",
    )
    scheme_ids = [m["id"] for m in matches]
    assert "pmfme" in scheme_ids
    assert "pmegp" in scheme_ids
    assert "mudra" in scheme_ids


def test_tea_stall_micro_matches_svanidhi():
    matches = match_government_schemes(
        category_key="tea_stall",
        archetype="dine_in",
        startup_cost=50_000,
        is_new=True,
        settlement_type="urban",
    )
    scheme_ids = [m["id"] for m in matches]
    assert "pm_svanidhi" in scheme_ids


def test_rural_pmegp_subsidy_rate():
    matches = match_government_schemes(
        category_key="gym",
        archetype="membership",
        startup_cost=1_500_000,
        is_new=True,
        settlement_type="rural",
    )
    pmegp = next(m for m in matches if m["id"] == "pmegp")
    assert "25% to 35%" in pmegp["benefit"]
    assert "Rural" in pmegp["match_reason"]


def test_cgtmse_and_standup_for_large_capital():
    matches = match_government_schemes(
        category_key="gym",
        archetype="membership",
        startup_cost=3_500_000,
        is_new=True,
        settlement_type="urban",
    )
    scheme_ids = [m["id"] for m in matches]
    assert "cgtmse" in scheme_ids
    assert "standup_india" in scheme_ids
