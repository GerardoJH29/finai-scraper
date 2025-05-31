"""tests/test_integration.py – prueba de integración offline
==========================================================="""
from __future__ import annotations
import os
import pathlib
import vcr
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import weekly_scraper  # importa modelos y helpers del script principal

# ───────────────────── Configuración de VCR ─────────────────────
CASSETTE_DIR = pathlib.Path(__file__).parent / "cassettes"
my_vcr = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
    filter_headers=["authorization"],
    decode_compressed_response=True,
)

# ─────────────── Fixture de DB en memoria ───────────────────────
@pytest.fixture(scope="function")
def in_memory_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:", future=True)
    weekly_scraper.Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    monkeypatch.setattr(weekly_scraper, "engine", engine, raising=False)
    monkeypatch.setattr(weekly_scraper, "SessionLocal", TestSession, raising=False)
    yield TestSession

# ─────────────────────── Test de integración ────────────────────
@my_vcr.use_cassette("bbva.yml")
def test_crawl_bbva(tmp_path, monkeypatch, in_memory_db):
    monkeypatch.setenv("SCRAPER_DATA_DIR", str(tmp_path))
    weekly_scraper.crawl_institution("bbva-mx", weekly_scraper.INSTITUTIONS["bbva-mx"])
    with in_memory_db() as db:
        assert db.query(weekly_scraper.Product).count() > 0
        assert db.query(weekly_scraper.Document).count() > 0
