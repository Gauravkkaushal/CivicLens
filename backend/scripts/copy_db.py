"""Copy every CivicLens table from one Postgres to another (same Alembic revision on both), e.g. to move regions.

Reads DATABASE_URL (source) and NEW_DATABASE_URL (target) from the environment / backend/.env; never prints them.
The target tables must exist and be empty. With --swap, the .env holding DATABASE_URL is rewritten afterwards so DATABASE_URL points
at the target and the old value is kept as OLD_DATABASE_URL.

Usage: python scripts/copy_db.py [--swap]
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import geoalchemy2  # noqa: F401  (registers the geography type for reflection)
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, func, select, text

ROOT = Path(__file__).resolve().parent.parent
# the app reads backend/.env, then the repo-root .env; rewrite whichever one holds DATABASE_URL
ENV = next((p for p in (ROOT / ".env", ROOT.parent / ".env") if p.exists() and "DATABASE_URL=" in p.read_text(encoding="utf-8")),
           ROOT / ".env")
# parents before children (foreign keys)
TABLES = ["users", "projects", "candidate_locations", "market_snapshots", "competitors", "scenarios", "simulation_runs",
          "actual_outcomes", "reports", "provider_cache", "field_requests", "field_records"]


def _url(name: str) -> str:
    url = os.getenv(name) or sys.exit(f"{name} is not set (add it to backend/.env)")
    for p in ("postgres://", "postgresql://"):
        if url.startswith(p):
            return "postgresql+psycopg://" + url[len(p):]
    return url


def main() -> None:
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT.parent / ".env")
    src = create_engine(_url("DATABASE_URL"), connect_args={"connect_timeout": 30})
    dst = create_engine(_url("NEW_DATABASE_URL"), connect_args={"connect_timeout": 30})
    with src.connect() as s, dst.connect() as d:
        rev_s = s.execute(text("select version_num from alembic_version")).scalar()
        rev_d = d.execute(text("select version_num from alembic_version")).scalar()
        if rev_s != rev_d:
            sys.exit(f"schema mismatch: source at {rev_s}, target at {rev_d}")
    meta = MetaData()
    meta.reflect(dst, only=TABLES)
    with dst.begin() as d:
        for name in TABLES:
            if d.execute(select(func.count()).select_from(meta.tables[name])).scalar():
                sys.exit(f"target table {name} is not empty; refusing to copy")
    with src.connect() as s, dst.begin() as d:  # one transaction: all or nothing
        for name in TABLES:
            t = meta.tables[name]
            n = 0
            rows = s.execution_options(stream_results=True).execute(select(t)).mappings()
            while batch := rows.fetchmany(50):
                d.execute(t.insert(), [dict(r) for r in batch])
                n += len(batch)
            print(f"{name:<22} {n} rows")
    if "--swap" in sys.argv:
        env = ENV.read_text(encoding="utf-8")
        old = re.search(r"^DATABASE_URL=(.*)$", env, re.M).group(1)
        new = re.search(r"^NEW_DATABASE_URL=(.*)$", env, re.M).group(1)
        env = re.sub(r"^NEW_DATABASE_URL=.*\n?", "", env, flags=re.M)
        env = re.sub(r"^DATABASE_URL=.*$", lambda _: f"DATABASE_URL={new}\nOLD_DATABASE_URL={old}", env, count=1, flags=re.M)
        ENV.write_text(env, encoding="utf-8")
        print(f"{ENV.name} now points DATABASE_URL at the new database (old one kept as OLD_DATABASE_URL)")


if __name__ == "__main__":
    main()
