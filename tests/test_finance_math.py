import math

import pytest

from vt_valuation_agent.valuation.finance_math import cagr, discount_factor, irr, npv


def test_discount_factor():
    assert discount_factor(0.10, 1) == pytest.approx(1 / 1.1)
    assert discount_factor(0.10, 0.5) == pytest.approx(1 / math.sqrt(1.1))


def test_npv_end_of_year_and_mid_year():
    flows = [100.0, 100.0]
    assert npv(0.10, flows) == pytest.approx(100 / 1.1 + 100 / 1.21)
    assert npv(0.10, flows, mid_year=True) == pytest.approx(100 / 1.1**0.5 + 100 / 1.1**1.5)


def test_irr_recovers_known_rate():
    # -100 today, 121 in two years is exactly 10%
    assert irr([-100.0, 0.0, 121.0]) == pytest.approx(0.10, abs=1e-8)


def test_irr_requires_sign_change():
    with pytest.raises(ValueError):
        irr([100.0, 50.0])


def test_cagr():
    assert cagr(100.0, 121.0, 2) == pytest.approx(0.10)
    with pytest.raises(ValueError):
        cagr(0.0, 1.0, 1)
