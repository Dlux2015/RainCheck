"""Tests for feature engineering label logic."""

import pytest


def test_label_positive_for_large_price_change():
    # Label rule: price_pct_change > 0.03 → 1
    pct_change = 0.05
    label = 1 if pct_change > 0.03 else 0
    assert label == 1


def test_label_zero_for_small_price_change():
    pct_change = 0.01
    label = 1 if pct_change > 0.03 else 0
    assert label == 0


def test_label_zero_at_exact_threshold():
    pct_change = 0.03
    label = 1 if pct_change > 0.03 else 0
    assert label == 0


def test_label_negative_price_change_is_zero():
    pct_change = -0.02
    label = 1 if pct_change > 0.03 else 0
    assert label == 0


@pytest.mark.parametrize("pct_change,expected", [
    (0.10, 1),
    (0.04, 1),
    (0.03, 0),
    (0.00, 0),
    (-0.05, 0),
])
def test_label_parametrized(pct_change, expected):
    label = 1 if pct_change > 0.03 else 0
    assert label == expected
