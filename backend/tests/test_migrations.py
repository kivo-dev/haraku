"""The Alembic migration must create exactly what app/models.py describes."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {"categories", "places", "place_images", "opportunities"}


@pytest.fixture
def migrated_url(tmp_path, monkeypatch):
    pytest.importorskip("alembic")
    from alembic import command
    from alembic.config import Config

    from app.config import get_settings

    url = f"sqlite:///{tmp_path}/mig.db"
    monkeypatch.setattr(get_settings(), "database_url", url)  # migrations/env.py reads it from settings
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(cfg, "head")
    yield url, cfg, command


def test_upgrade_creates_all_tables_and_matches_models(migrated_url):
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy import create_engine, inspect

    from app.models import Base

    url, _, _ = migrated_url
    eng = create_engine(url)
    assert EXPECTED <= set(inspect(eng).get_table_names())
    with eng.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn, opts={"compare_type": False}), Base.metadata)
    assert diff == [], diff


def test_downgrade_removes_everything(migrated_url):
    from sqlalchemy import create_engine, inspect

    url, cfg, command = migrated_url
    command.downgrade(cfg, "base")
    assert EXPECTED.isdisjoint(set(inspect(create_engine(url)).get_table_names()))
