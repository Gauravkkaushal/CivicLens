"""Government Schemes & Financial Incentives matcher for Indian small businesses & startups.

Matches verified Central & State MSME schemes based on:
- Category (e.g. food processing, retail, services, tech)
- Economic Archetype (e.g. dine_in, takeaway, membership, appointment)
- Startup Capital / Setup Cost
- Objective (start_new vs improve_existing)
- Location State & Settlement Type (urban vs rural)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GovtScheme:
    id: str
    name: str
    ministry: str
    type: str  # "Capital Subsidy", "Collateral-free Loan", "Interest Subsidy", "Startup Grant"
    benefit: str
    portal_url: str
    eligibility_summary: str
    documents_needed: tuple[str, ...]


SCHEMES: dict[str, GovtScheme] = {
    "pmegp": GovtScheme(
        id="pmegp",
        name="Prime Minister's Employment Generation Programme (PMEGP)",
        ministry="Ministry of MSME / KVIC",
        type="Capital Subsidy & Term Loan",
        benefit="15% to 35% margin money subsidy (Up to ₹20L for services, ₹50L for manufacturing).",
        portal_url="https://www.jansamarth.in",
        eligibility_summary="Applicable for new micro-enterprises. Higher subsidy (25%-35%) in rural areas & for women/SC/ST/OBC promoters.",
        documents_needed=(
            "Aadhaar card & PAN",
            "Detailed Project Report (DPR)",
            "EDP (Entrepreneurship Development) Training Certificate",
            "Educational Qualification Certificate (for projects > ₹5L/₹10L)",
        ),
    ),
    "pmfme": GovtScheme(
        id="pmfme",
        name="PM Formalisation of Micro food processing Enterprises (PMFME)",
        ministry="Ministry of Food Processing Industries (MoFPI)",
        type="Credit-Linked Capital Subsidy",
        benefit="35% subsidy on eligible project cost, capped at ₹10 Lakh per unit.",
        portal_url="https://pmfme.mofpi.gov.in",
        eligibility_summary="Exclusively for food processing, commercial bakeries, packaged snacks, beverages, and cloud kitchens.",
        documents_needed=(
            "FSSAI Food License / Registration",
            "Udyam MSME Registration Certificate",
            "Equipment & Machinery quotations",
            "Rent Agreement or Property Ownership proof",
        ),
    ),
    "mudra": GovtScheme(
        id="mudra",
        name="Pradhan Mantri MUDRA Yojana (PMMY)",
        ministry="Department of Financial Services, Ministry of Finance",
        type="Collateral-free Business Loan",
        benefit="Collateral-free loan up to ₹10-20 Lakh across Shishu (<₹50k), Kishore (₹50k-₹5L), Tarun (₹5L-₹10L), and Tarun Plus tiers.",
        portal_url="https://www.mudra.org.in",
        eligibility_summary="For non-corporate, non-farm small and micro enterprises in retail, services, and trading requiring debt or working capital.",
        documents_needed=(
            "Udyam Registration Certificate",
            "Identity & Business Address Proof",
            "Quotation for machinery / inventory / setup",
            "Bank account statements for last 6 months",
        ),
    ),
    "pm_svanidhi": GovtScheme(
        id="pm_svanidhi",
        name="PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
        ministry="Ministry of Housing and Urban Affairs",
        type="Micro Working Capital Loan",
        benefit="₹10,000 to ₹50,000 working capital loan with 7% interest subsidy & cashback on digital UPI transactions.",
        portal_url="https://pmsvanidhi.mohua.gov.in",
        eligibility_summary="For urban street vendors, tea stalls, and small roadside snack stalls.",
        documents_needed=(
            "Certificate of Vending or Local Urban Body recommendation letter",
            "Aadhaar-linked Bank Account",
        ),
    ),
    "cgtmse": GovtScheme(
        id="cgtmse",
        name="Credit Guarantee Fund Trust for Micro & Small Enterprises (CGTMSE)",
        ministry="Ministry of MSME & SIDBI",
        type="Credit Guarantee Coverage",
        benefit="Third-party collateral-free bank loans up to ₹5 Crore with 75% to 85% credit guarantee cover.",
        portal_url="https://www.cgtmse.in",
        eligibility_summary="For new and existing MSMEs requiring medium-to-large business loans without mortgaging private land or property.",
        documents_needed=(
            "Udyam MSME Registration",
            "Audited / Projected Financials & Cash Flow Projections",
            "Business Plan / Feasibility Report",
            "ITR and Bank Statements",
        ),
    ),
    "startup_india": GovtScheme(
        id="startup_india",
        name="Startup India Seed Fund Scheme (SISFS) & DPIIT Recognition",
        ministry="DPIIT, Ministry of Commerce & Industry",
        type="Seed Grant & Tax Holiday",
        benefit="Grants up to ₹20 Lakh for proof-of-concept/prototype, up to ₹50 Lakh debt, and 3-year income tax exemption (Sec 80-IAC).",
        portal_url="https://www.startupindia.gov.in",
        eligibility_summary="For incorporated entities with innovative, tech-enabled, or scalable products/services recognized by DPIIT.",
        documents_needed=(
            "DPIIT Startup Recognition Certificate",
            "Certificate of Incorporation / MCA",
            "Product Pitch Deck & Demonstration / Prototype",
        ),
    ),
    "standup_india": GovtScheme(
        id="standup_india",
        name="Stand-Up India Scheme",
        ministry="Department of Financial Services, Ministry of Finance",
        type="Composite Bank Loan",
        benefit="Composite loan (term loan + working capital) between ₹10 Lakh and ₹1 Crore at concessional interest rates.",
        portal_url="https://www.standupmitra.in",
        eligibility_summary="For greenfield enterprises in manufacturing, services, or trading led by at least one Woman or SC/ST entrepreneur (>=51% stake).",
        documents_needed=(
            "Identity Proof & Category Certificate (for SC/ST) / Gender Proof",
            "Project Report / Feasibility Study",
            "Proof of Business Premise",
            "PAN Card & Partnership / Incorporation Deed",
        ),
    ),
}

# Food categories that directly qualify for MoFPI PMFME
FOOD_PROCESSING_CATEGORIES = {
    "bakery",
    "bakery_cafe",
    "cloud_kitchen",
    "ice_cream",
    "juice_bar",
    "food_processing",
    "confectionery",
}

# Street kiosk / micro cart categories eligible for PM SVANidhi
STREET_MICRO_CATEGORIES = {
    "tea_stall",
    "fast_food",
}

# Tech/innovation oriented categories
TECH_INNOVATION_CATEGORIES = {
    "coworking",
    "tech_startup",
    "edtech",
}


def match_government_schemes(
    category_key: str,
    archetype: str,
    startup_cost: float = 0.0,
    is_new: bool = True,
    state: str | None = None,
    settlement_type: str | None = None,
) -> list[dict[str, Any]]:
    """Match applicable central and state government schemes for a business."""
    matches: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    is_rural = (settlement_type or "").lower() == "rural"

    def add_match(scheme_id: str, reason: str, custom_benefit: str | None = None) -> None:
        if scheme_id in seen_ids or scheme_id not in SCHEMES:
            return
        seen_ids.add(scheme_id)
        sc = SCHEMES[scheme_id]
        matches.append({
            "id": sc.id,
            "name": sc.name,
            "ministry": sc.ministry,
            "type": sc.type,
            "benefit": custom_benefit or sc.benefit,
            "portal_url": sc.portal_url,
            "match_reason": reason,
            "eligibility_summary": sc.eligibility_summary,
            "documents_needed": list(sc.documents_needed),
        })

    # 1. PMFME (Food Processing & Kitchens)
    if category_key in FOOD_PROCESSING_CATEGORIES or "bakery" in category_key or "food" in category_key:
        add_match(
            "pmfme",
            "Eligible under Ministry of Food Processing Industries (MoFPI) micro food processing and commercial kitchen support.",
        )

    # 2. PM SVANidhi (Micro food stalls / Tea stalls in urban areas)
    if category_key in STREET_MICRO_CATEGORIES and startup_cost <= 150_000 and not is_rural:
        add_match(
            "pm_svanidhi",
            "Applicable for micro food kiosks, tea stalls, and street-side operations seeking subsidized working capital.",
        )

    # 3. PMEGP (New Ventures under ₹20L/₹50L)
    if is_new and startup_cost <= 5_000_000:
        subsidy_rate = "25% to 35%" if is_rural else "15% to 25%"
        area_str = "Rural" if is_rural else "Urban"
        add_match(
            "pmegp",
            f"Greenfield business with an estimated setup capital of ₹{int(startup_cost):,}. Grounded in {area_str} area ({subsidy_rate} subsidy).",
            custom_benefit=f"{subsidy_rate} margin money capital subsidy via KVIC/JanSamarth based on {area_str} location.",
        )

    # 4. Pradhan Mantri MUDRA Yojana (PMMY)
    # Tier mapping based on startup cost
    if startup_cost <= 2_000_000 and "pm_svanidhi" not in seen_ids:
        if startup_cost <= 50_000:
            tier = "Shishu (up to ₹50,000)"
        elif startup_cost <= 500_000:
            tier = "Kishore (₹50,000 to ₹5 Lakh)"
        elif startup_cost <= 1_000_000:
            tier = "Tarun (₹5 Lakh to ₹10 Lakh)"
        else:
            tier = "Tarun Plus (₹10 Lakh to ₹20 Lakh)"
        add_match(
            "mudra",
            f"Standard collateral-free bank financing suited for setup costs under {tier}.",
        )

    # 5. Stand-Up India (Greenfield capital >= ₹10 Lakh)
    if is_new and startup_cost >= 1_000_000:
        add_match(
            "standup_india",
            "Applicable if enterprise is promoted by Women or SC/ST entrepreneurs requiring ₹10L - ₹1Cr financing.",
        )

    # 6. CGTMSE (Collateral-free credit for larger capital requirements)
    if startup_cost > 1_000_000:
        add_match(
            "cgtmse",
            f"Enables collateral-free credit guarantee for larger setup capital requirements (estimated ₹{int(startup_cost):,}).",
        )

    # 7. Startup India (Tech / Coworking / Scalable)
    if category_key in TECH_INNOVATION_CATEGORIES or archetype in ("membership", "software"):
        add_match(
            "startup_india",
            "Relevant for tech-enabled models, co-working platforms, or innovative startups eligible for DPIIT seed funds.",
        )

    return matches
