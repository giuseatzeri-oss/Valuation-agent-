import pytest

from vt_valuation_agent.valuation.comps import Comparable, TargetMetrics, multiple_stats, relative_valuation


def test_multiple_stats_quartiles():
    st = multiple_stats("ev_ebitda", [8, 9, 10, 11, 12])
    assert st.median == 10
    assert st.first_quartile == 9
    assert st.third_quartile == 11
    assert st.mean == 10
    assert st.n == 5


def test_relative_valuation_bridges_ev_and_equity():
    peers = [Comparable(name=f"P{i}", ev_ebitda=m, pe=p) for i, (m, p) in enumerate([(8, 14), (10, 16), (12, 18)])]
    target = TargetMetrics(ebitda=100, net_income=50)
    res = relative_valuation(peers, target, net_debt=200, shares_outstanding=10)
    by = {i.multiple: i for i in res.implied}
    assert by["ev_ebitda"].mid["enterprise_value"] == pytest.approx(1000)
    assert by["ev_ebitda"].mid["equity_value"] == pytest.approx(800)
    assert by["ev_ebitda"].mid["value_per_share"] == pytest.approx(80)
    # P/E gives equity directly; EV adds net debt back
    assert by["pe"].mid["equity_value"] == pytest.approx(800)
    assert by["pe"].mid["enterprise_value"] == pytest.approx(1000)


def test_negative_multiples_excluded_and_missing_metric_noted():
    peers = [Comparable(name="A", ev_ebitda=-5), Comparable(name="B", ev_ebitda=9), Comparable(name="C", ev_revenue=2)]
    res = relative_valuation(peers, TargetMetrics(ebitda=10), kind="precedent_transactions")
    assert any("excluded" in e for e in res.excluded)
    assert any("revenue not provided" in n for n in res.notes)
    assert any("control premium" in n for n in res.notes)


def test_requires_usable_multiples():
    with pytest.raises(ValueError):
        relative_valuation([Comparable(name="A")], TargetMetrics(ebitda=1))
