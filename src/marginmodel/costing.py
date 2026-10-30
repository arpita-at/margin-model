"""Overhead absorption and product/customer profitability.

Two allocation methods over the same cost pool, so the same product can be
profitable under one and loss-making under the other. That difference is the
whole point of the model.

Nothing here is specific to any employer. All inputs are synthetic.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Product:
    code: str
    name: str
    plant: str
    units: int                 # actual units produced and sold
    price: float               # per unit
    direct_material: float     # per unit
    direct_labour: float       # per unit
    machine_hours: float       # per unit
    setups: int                # production runs in the period
    order_lines: int           # customer order lines touched

    @property
    def direct_cost(self) -> float:
        return self.direct_material + self.direct_labour

    @property
    def revenue(self) -> float:
        return self.units * self.price


@dataclass(frozen=True)
class OverheadPool:
    """One period's overhead, split by what actually drives it."""
    machining: float           # driven by machine hours
    setup: float               # driven by number of setups
    order_handling: float      # driven by order lines

    @property
    def total(self) -> float:
        return self.machining + self.setup + self.order_handling


# ----------------------------------------------------------------- allocation

def plantwide_rate(products: list[Product], pool: OverheadPool) -> float:
    """Single blanket rate: total overhead / total machine hours.

    This is what most plants actually run. It is simple and it is wrong for any
    product whose setup or order-handling intensity differs from the average.
    """
    total_hours = sum(p.units * p.machine_hours for p in products)
    if total_hours == 0:
        raise ValueError("no machine hours: cannot compute a plantwide rate")
    return pool.total / total_hours


def plantwide_overhead(p: Product, rate: float) -> float:
    return p.units * p.machine_hours * rate


def activity_rates(products: list[Product], pool: OverheadPool) -> dict[str, float]:
    """One rate per driver. Each pool is absorbed by its own cause."""
    hours = sum(p.units * p.machine_hours for p in products)
    setups = sum(p.setups for p in products)
    lines = sum(p.order_lines for p in products)
    for name, denom in (("machine hours", hours), ("setups", setups), ("order lines", lines)):
        if denom == 0:
            raise ValueError(f"no {name}: cannot compute an activity rate")
    return {
        "machining_per_hour": pool.machining / hours,
        "setup_per_setup": pool.setup / setups,
        "order_per_line": pool.order_handling / lines,
    }


def activity_overhead(p: Product, rates: dict[str, float]) -> float:
    return (p.units * p.machine_hours * rates["machining_per_hour"]
            + p.setups * rates["setup_per_setup"]
            + p.order_lines * rates["order_per_line"])


# -------------------------------------------------------------- profitability

@dataclass
class Margin:
    code: str
    name: str
    revenue: float
    direct: float
    overhead: float

    @property
    def gross(self) -> float:
        return self.revenue - self.direct

    @property
    def net(self) -> float:
        return self.revenue - self.direct - self.overhead

    @property
    def net_pct(self) -> float:
        return self.net / self.revenue if self.revenue else 0.0


def margins(products: list[Product], pool: OverheadPool, method: str) -> list[Margin]:
    if method == "plantwide":
        rate = plantwide_rate(products, pool)
        oh = {p.code: plantwide_overhead(p, rate) for p in products}
    elif method == "activity":
        rates = activity_rates(products, pool)
        oh = {p.code: activity_overhead(p, rates) for p in products}
    else:
        raise ValueError(f"unknown method: {method!r}")
    return [Margin(p.code, p.name, p.revenue, p.units * p.direct_cost, oh[p.code])
            for p in products]


def flips(products: list[Product], pool: OverheadPool) -> list[tuple[str, float, float]]:
    """Products whose sign changes between the two methods.

    This is the finding the model exists to produce.
    """
    a = {m.code: m for m in margins(products, pool, "plantwide")}
    b = {m.code: m for m in margins(products, pool, "activity")}
    out = []
    for code in a:
        if (a[code].net >= 0) != (b[code].net >= 0):
            out.append((code, a[code].net, b[code].net))
    return out


# ------------------------------------------------------- absorption variance

@dataclass(frozen=True)
class AbsorptionInputs:
    budgeted_overhead: float
    budgeted_hours: float
    actual_overhead: float
    actual_hours: float

    @property
    def budgeted_rate(self) -> float:
        if self.budgeted_hours == 0:
            raise ValueError("budgeted hours is zero")
        return self.budgeted_overhead / self.budgeted_hours


def absorption_variance(i: AbsorptionInputs) -> dict[str, float]:
    """Split over/under absorption into its two real causes.

    expenditure variance = we spent more or less than budget
    volume variance      = we ran more or fewer hours than budget

    Positive means over-absorbed, a credit to the P&L. Negative means
    under-absorbed, a charge. The two parts always sum to the total.
    """
    absorbed = i.actual_hours * i.budgeted_rate
    total = absorbed - i.actual_overhead
    expenditure = i.budgeted_overhead - i.actual_overhead
    volume = (i.actual_hours - i.budgeted_hours) * i.budgeted_rate
    return {
        "budgeted_rate": i.budgeted_rate,
        "overhead_absorbed": absorbed,
        "expenditure_variance": expenditure,
        "volume_variance": volume,
        "total_over_under": total,
    }
