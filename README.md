# margin-model

**An overhead absorption and product profitability model.** It allocates one
overhead pool two ways, a single plantwide rate and an activity-based rate, and
shows which products change sign between them. It also splits over and under
absorption into the two variances that cause it.

Sample data is synthetic. There are no real products, plants or customers in this repo.

```
units, price, direct cost ──┐
                            ├─► plantwide rate   total overhead / total machine hours
machine hrs, setups, lines ─┘
                            ├─► activity rates   one rate per driver
                            ├─► comparison       who changes sign, and by how much
                            └─► absorption       expenditure variance + volume variance
```

---

## The finding

Under a single plantwide machine-hour rate, **all six products are profitable**.
Allocate the same pool by the activities that actually cause it and **two of them
are loss-making, carrying 12.2% of revenue**.

| Product | Revenue | Net: plantwide | Net: activity | Swing |
|---|---:|---:|---:|---:|
| P1 Valve body, standard | 4,956,000 | 1,074,602 | 1,627,324 | +552,722 |
| P2 Valve body, heavy | 3,034,000 | 508,411 | 719,822 | +211,410 |
| P3 Manifold, 2 port | 2,592,000 | 541,929 | 715,005 | +173,076 |
| **P4 Manifold, custom** | 892,800 | 106,792 | **-626,066** | **-732,858** |
| P5 Coupling, cast | 3,172,000 | 597,552 | 936,200 | +338,648 |
| **P6 Coupling, machined set** | 1,009,800 | 99,713 | **-443,286** | **-542,999** |

Total profit is identical under both methods, because both absorb the same pool.
The argument is never about the total. It is about who carries it.

## Why the blanket rate hides this

A plantwide rate charges overhead in proportion to machine hours and nothing
else. P4 and P6 are low volume and high touch: between them they are 5.4% of
units but **71% of the setups** and **60% of the order lines**. Setup and order
handling cost real money and have nothing to do with how long a part sits on a
machine, so a machine-hour rate moves that cost onto the high-volume products
that did not cause it.

| | Plantwide | Activity |
|---|---|---|
| Machine hour | 92.65 | 50.96 |
| Setup | absorbed in the hourly rate | 7,714.29 each |
| Order line | absorbed in the hourly rate | 501.03 each |

## Over and under absorption

Absorption variance is usually reported as one number, which makes it
unactionable. It has two causes and they are fixed by different people.

| | |
|---|---:|
| Budgeted overhead | 5,220,000 |
| Budgeted machine hours | 58,000 |
| Budgeted absorption rate | 90.00 |
| Actual overhead | 5,400,000 |
| Actual machine hours | 54,900 |
| Overhead absorbed | 4,941,000 |
| **Expenditure variance** | **-180,000** |
| **Volume variance** | **-279,000** |
| **Total under absorbed** | **-459,000** |

Expenditure is a spending problem: 180,000 more was spent than budgeted. Volume
is a capacity problem: 3,100 fewer hours were run than planned, so 279,000 of
fixed overhead never reached a product. Reporting only the 459,000 tells you
something is wrong without telling you who can fix it.

## The Excel model

`product-profitability-model.xlsx` is the same model with **live formulas**, not
pasted values. Every rate, allocation and variance points back at the Inputs
sheet, so changing a driver changes the answer.

| Sheet | What it does |
|---|---|
| Inputs | Shaded cells. The only place anything is typed. |
| Plantwide | Single rate on machine hours |
| Activity | One rate per driver |
| Comparison | Net margin both ways, and which products flip |
| Absorption | Expenditure and volume variance |

Rebuild it:

```bash
pip install openpyxl
PYTHONPATH=src python -m marginmodel.workbook product-profitability-model.xlsx
```

## Tests

The invariant that makes the comparison honest is that neither method may create
or destroy overhead.

```bash
python tests/test_costing.py
```

```
PASS test_at_least_one_product_flips_sign_between_methods
PASS test_both_methods_absorb_the_whole_pool
PASS test_plantwide_rate_rejects_zero_hours
PASS test_revenue_and_direct_cost_do_not_move_between_methods
PASS test_the_two_variances_sum_to_total_over_under_absorption
PASS test_under_absorbed_when_hours_fall_short_of_budget

6/6 passed
```

## What this is not

It is not a costing system and it does not read from an ERP. It is a model for
answering one question: when someone says a product is profitable, profitable
under which allocation.
