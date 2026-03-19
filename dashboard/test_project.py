"""Tests for Finance Dashboard CLI companion."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# Point DATA_FILE at a temp file during tests
import project

TEMP_FILE = Path(__file__).parent / "_test_data.json"


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    """Redirect all data I/O to a fresh temp file for each test."""
    monkeypatch.setattr(project, "DATA_FILE", tmp_path / "data.json")
    yield
    pass  # tmp_path is cleaned up automatically


# ── helpers ──────────────────────────────────────────────────────────────────

def make_tx(type_="income", amount=100.0, date="2025-03-01", category="Salary", desc="Test"):
    return {
        "id":       str(uuid.uuid4())[:8],
        "type":     type_,
        "desc":     desc,
        "amount":   amount,
        "category": category,
        "date":     date,
    }


# ── load / save ───────────────────────────────────────────────────────────────

def test_load_empty_when_no_file():
    assert project.load() == []


def test_save_and_load():
    tx = make_tx()
    project.save([tx])
    assert project.load() == [tx]


def test_save_multiple():
    txs = [make_tx(amount=i * 10) for i in range(1, 4)]
    project.save(txs)
    loaded = project.load()
    assert len(loaded) == 3
    assert loaded[1]["amount"] == 20.0


# ── fmt_money ─────────────────────────────────────────────────────────────────

def test_fmt_money_basic():
    assert project.fmt_money(1234.5) == "$1,234.50"


def test_fmt_money_zero():
    assert project.fmt_money(0) == "$0.00"


def test_fmt_money_large():
    assert project.fmt_money(9999999.99) == "$9,999,999.99"


# ── parse_month ───────────────────────────────────────────────────────────────

def test_parse_month_valid():
    assert project.parse_month("2025-03") == (2025, 3)


def test_parse_month_january():
    assert project.parse_month("2024-01") == (2024, 1)


def test_parse_month_invalid():
    with pytest.raises(ValueError):
        project.parse_month("not-a-month")


# ── filter_by_month ──────────────────────────────────────────────────────────

def test_filter_correct_month():
    txs = [
        make_tx(date="2025-03-10"),
        make_tx(date="2025-04-01"),
        make_tx(date="2025-03-25"),
    ]
    result = project.filter_by_month(txs, "2025-03")
    assert len(result) == 2


def test_filter_empty():
    txs = [make_tx(date="2025-01-01")]
    result = project.filter_by_month(txs, "2025-06")
    assert result == []


def test_filter_preserves_content():
    tx = make_tx(date="2025-07-15", amount=500.0)
    result = project.filter_by_month([tx], "2025-07")
    assert result[0]["amount"] == 500.0


# ── cmd_summary (via captured print) ─────────────────────────────────────────

def test_summary_empty_month(capsys):
    project.cmd_summary("2030-01")
    out = capsys.readouterr().out
    assert "Income" in out
    assert "$0.00" in out


def test_summary_with_data(capsys):
    project.save([
        make_tx(type_="income",  amount=4000.0, date="2025-05-01", category="Salary"),
        make_tx(type_="expense", amount=1000.0, date="2025-05-10", category="Housing"),
        make_tx(type_="expense", amount=200.0,  date="2025-05-15", category="Food"),
    ])
    project.cmd_summary("2025-05")
    out = capsys.readouterr().out
    assert "$4,000.00" in out
    assert "$1,200.00" in out   # total expenses
    assert "$2,800.00" in out   # balance
    assert "70.0%" in out       # savings rate


# ── cmd_delete ────────────────────────────────────────────────────────────────

def test_delete_existing():
    tx = make_tx()
    project.save([tx])
    project.cmd_delete(tx["id"])
    assert project.load() == []


def test_delete_nonexistent(capsys):
    project.save([make_tx()])
    project.cmd_delete("fakeid99")
    out = capsys.readouterr().out
    assert "No transaction" in out
    assert len(project.load()) == 1  # untouched


def test_delete_leaves_others():
    txs = [make_tx(amount=float(i)) for i in range(3)]
    project.save(txs)
    project.cmd_delete(txs[1]["id"])
    remaining = project.load()
    assert len(remaining) == 2
    ids = {t["id"] for t in remaining}
    assert txs[1]["id"] not in ids
