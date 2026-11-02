from app.api.decisions import _report_content
from app.db import get_engine
from app.models import CandidateLocation, Project, Scenario, User
from sqlalchemy.orm import Session


def test_report_content_includes_schemes(client):
    with Session(get_engine()) as db:
        user = User(email="schemes_test@example.com", password_hash="x", preferences={})
        db.add(user)
        db.flush()

        p = Project(
            owner_id=user.id,
            name="Test Bakery Project",
            objective="start_new",
            decision_goal="profit",
            category={"key": "bakery", "label": "Bakery", "archetype": "takeaway", "filters": []},
            profile={"description": "Artisan bakery", "setup_cost": 750000},
        )
        db.add(p)
        db.flush()

        loc = CandidateLocation(
            project_id=p.id,
            label="Location 1",
            address="123 High St, Indiranagar, Bengaluru, Karnataka",
            lat=12.9716,
            lng=77.5946,
            geog="SRID=4326;POINT(77.5946 12.9716)",
            catchment={"mode": "radius", "radius_km": 1.5},
        )
        db.add(loc)
        db.flush()

        scen = Scenario(
            project_id=p.id,
            location_id=loc.id,
            name="Baseline",
            is_baseline=True,
            inputs={"price": 250, "startup_cost": 750000},
        )
        db.add(scen)
        db.commit()

        content = _report_content(db, p)
        assert "government_schemes" in content
        schemes = content["government_schemes"]
        assert len(schemes) >= 2

        scheme_ids = [s["id"] for s in schemes]
        assert "pmfme" in scheme_ids
        assert "pmegp" in scheme_ids
        assert "mudra" in scheme_ids
