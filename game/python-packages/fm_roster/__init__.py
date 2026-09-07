"""Pure, Ren'Py-independent decision logic for roster QoL features.

Modules here take plain data (dicts/lists) and return decisions/plans. The .rpy
layer gathers game state, calls these, and applies the results via existing
engine primitives. Keeping the logic pure makes it unit-testable without a
Ren'Py runtime and keeps the untestable glue thin.
"""
