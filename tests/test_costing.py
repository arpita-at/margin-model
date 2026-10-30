import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from marginmodel.costing import (OverheadPool, Product, AbsorptionInputs,
                                 plantwide_rate, activity_rates, margins,
                                 absorption_variance, flips)
from marginmodel.sample import PRODUCTS, POOL, ABSORPTION


def test_both_methods_absorb_the_whole_pool():
    """Neither method may create or destroy overhead. This is the invariant
    that makes the comparison honest."""
    for method in ("plantwide", "activity"):
        total = sum(m.overhead for m in margins(PRODUCTS, POOL, method))
        assert abs(total - POOL.total) < 0.01, (method, total, POOL.total)


def test_revenue_and_direct_cost_do_not_move_between_methods():
    a = {m.code: m for m in margins(PRODUCTS, POOL, "plantwide")}
    b = {m.code: m for m in margins(PRODUCTS, POOL, "activity")}
    for code in a:
        assert abs(a[code].revenue - b[code].revenue) < 0.01
        assert abs(a[code].direct - b[code].direct) < 0.01


def test_the_two_variances_sum_to_total_over_under_absorption():
    v = absorption_variance(ABSORPTION)
    assert abs((v["expenditure_variance"] + v["volume_variance"])
               - v["total_over_under"]) < 0.01


def test_under_absorbed_when_hours_fall_short_of_budget():
    v = absorption_variance(ABSORPTION)
    assert ABSORPTION.actual_hours < ABSORPTION.budgeted_hours
    assert v["volume_variance"] < 0


def test_at_least_one_product_flips_sign_between_methods():
    assert flips(PRODUCTS, POOL), "sample data no longer demonstrates the point"


def test_plantwide_rate_rejects_zero_hours():
    try:
        plantwide_rate([Product("X", "x", "P", 10, 1, 0, 0, 0.0, 1, 1)],
                       OverheadPool(1, 1, 1))
    except ValueError:
        return
    raise AssertionError("expected ValueError on zero machine hours")


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    bad = 0
    for f in fns:
        try:
            f(); print(f"PASS {f.__name__}")
        except Exception:
            bad += 1; print(f"FAIL {f.__name__}"); traceback.print_exc()
    print(f"\n{len(fns)-bad}/{len(fns)} passed")
    raise SystemExit(1 if bad else 0)
