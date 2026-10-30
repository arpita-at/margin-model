"""Synthetic manufacturer. No real products, plants or customers."""
from .costing import Product, OverheadPool, AbsorptionInputs

# Six products across three plants. The spread that matters is setup and
# order-line intensity: P4 and P6 are low volume, high touch. A plantwide
# machine-hour rate cannot see that.
PRODUCTS = [
    Product("P1", "Valve body, standard",   "Plant A", units=42000, price=118.00,
            direct_material=41.00, direct_labour=12.50, machine_hours=0.42, setups=12,  order_lines=180),
    Product("P2", "Valve body, heavy",      "Plant A", units=18500, price=164.00,
            direct_material=63.00, direct_labour=17.00, machine_hours=0.61, setups=18,  order_lines=240),
    Product("P3", "Manifold, 2 port",       "Plant B", units=27000, price=96.00,
            direct_material=33.50, direct_labour=10.00, machine_hours=0.35, setups=15,  order_lines=210),
    Product("P4", "Manifold, custom",       "Plant B", units=3100,  price=288.00,
            direct_material=109.00, direct_labour=38.00, machine_hours=1.15, setups=74, order_lines=620),
    Product("P5", "Coupling, cast",         "Plant C", units=61000, price=52.00,
            direct_material=18.20, direct_labour=6.40,  machine_hours=0.19, setups=9,   order_lines=150),
    Product("P6", "Coupling, machined set", "Plant C", units=5400,  price=187.00,
            direct_material=58.00, direct_labour=29.00, machine_hours=0.88, setups=61,  order_lines=540),
]

POOL = OverheadPool(machining=2_970_000.0, setup=1_458_000.0, order_handling=972_000.0)

ABSORPTION = AbsorptionInputs(
    budgeted_overhead=5_220_000.0,
    budgeted_hours=58_000.0,
    actual_overhead=5_400_000.0,
    actual_hours=54_900.0,
)
