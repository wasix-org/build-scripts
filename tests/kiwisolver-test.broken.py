import unittest
import math

try:
    # Core API
    from kiwisolver import Variable, Solver
except Exception as e:
    raise RuntimeError(
        "This test suite requires the 'kiwisolver' package to be installed."
    ) from e

# Optional APIs that may or may not be present depending on kiwisolver version
try:
    from kiwisolver import strength  # constants/utilities for strengths
except Exception:
    strength = None

# Exception classes (guarded; some names may differ by version)
try:
    from kiwisolver import UnsatisfiableConstraint
except Exception:
    UnsatisfiableConstraint = None

try:
    from kiwisolver import DuplicateConstraint
except Exception:
    DuplicateConstraint = None

try:
    from kiwisolver import UnknownConstraint
except Exception:
    UnknownConstraint = None

try:
    from kiwisolver import UnknownEditVariable
except Exception:
    UnknownEditVariable = None


def approx_equal(a, b, tol=1e-9):
    return abs(a - b) <= tol


class KiwiSolverComprehensiveTests(unittest.TestCase):
    def setUp(self):
        # Variables used across many tests
        self.x1 = Variable("x1")
        self.x2 = Variable("x2")
        self.xm = Variable("xm")
        self.solver = Solver()

    # ---------- Basic system & required constraints ----------

    def test_basic_required_constraints(self):
        cons = [
            self.x1 == 0,
            self.x2 <= 100,
            self.x2 == self.xm + 5,
            self.xm == (self.x1 + self.x2) / 2,
        ]
        for c in cons:
            self.solver.addConstraint(c)

        # Without edits or soft constraints, the canonical Cassowary solution is:
        # x1 = 0, x2 = 10, xm = 5
        self.solver.updateVariables()
        self.assertTrue(approx_equal(self.x1.value(), 0.0))
        self.assertTrue(approx_equal(self.x2.value(), 10.0))
        self.assertTrue(approx_equal(self.xm.value(), 5.0))

    # ---------- Strengths (soft constraints) ----------

    def test_soft_constraint_weak_preference(self):
        # Same base constraints
        self.solver.addConstraint(self.x1 >= 0)
        self.solver.addConstraint(self.x2 <= 100)
        self.solver.addConstraint(self.x2 >= self.x1 + 10)
        self.solver.addConstraint(self.xm == (self.x1 + self.x2) / 2)

        # Prefer x1 == 40 (weak)
        # Use the pipe operator to set strength, as supported by kiwisolver's Python bindings.
        self.solver.addConstraint((self.x1 == 40) | "weak")

        # Make xm editable (strong) and suggest 60
        self.solver.addEditVariable(self.xm, "strong")
        self.solver.suggestValue(self.xm, 60)
        self.solver.updateVariables()

        # Expected solution: xm=60, x1=40, x2=80
        self.assertTrue(approx_equal(self.xm.value(), 60.0))
        self.assertTrue(approx_equal(self.x1.value(), 40.0))
        self.assertTrue(approx_equal(self.x2.value(), 80.0))

    def test_conflicting_soft_constraints_strength_ordering(self):
        # If both constraints conflict, stronger one should dominate.
        # Constrain x1 to a feasible range to anchor the system.
        self.solver.addConstraint(self.x1 >= 0)
        self.solver.addConstraint(self.x1 <= 100)

        weak_target = (self.x1 == 10) | "weak"
        strong_target = (self.x1 == 20) | "strong"

        self.solver.addConstraint(weak_target)
        self.solver.addConstraint(strong_target)
        self.solver.updateVariables()

        self.assertTrue(approx_equal(self.x1.value(), 20.0))

    def test_strength_module_if_available(self):
        if strength is None:
            self.skipTest("kiwisolver.strength not available in this version")

        # Using strength constants/utilities (if present)
        self.solver.addConstraint(self.x1 >= 0)
        self.solver.addConstraint((self.x1 == 5) | strength.weak)
        self.solver.updateVariables()
        self.assertTrue(approx_equal(self.x1.value(), 5.0))

    # ---------- Edit variables: suggest & update ----------

    def test_edit_variables_suggest_and_update(self):
        # Base constraints, same as in the docs
        self.solver.addConstraint(self.x1 >= 0)
        self.solver.addConstraint(self.x2 <= 100)
        self.solver.addConstraint(self.x2 >= self.x1 + 10)
        self.solver.addConstraint(self.xm == (self.x1 + self.x2) / 2)
        # Add a soft "x1 wants to be 40"
        self.solver.addConstraint((self.x1 == 40) | "weak")

        # Make xm editable and push it around
        self.solver.addEditVariable(self.xm, "strong")

        # First suggestion: 60
        self.solver.suggestValue(self.xm, 60)
        self.solver.updateVariables()
        self.assertTrue(approx_equal(self.xm.value(), 60.0))
        self.assertTrue(approx_equal(self.x1.value(), 40.0))
        self.assertTrue(approx_equal(self.x2.value(), 80.0))

        # Second suggestion: 90 (forces x2 cap at 100)
        self.solver.suggestValue(self.xm, 90)
        self.solver.updateVariables()
        self.assertTrue(approx_equal(self.xm.value(), 90.0))
        # x2 hits upper bound 100, so x1 must be 80 to keep xm midpoint
        self.assertTrue(approx_equal(self.x1.value(), 80.0))
        self.assertTrue(approx_equal(self.x2.value(), 100.0))

    def test_suggest_without_edit_variable_raises_if_supported(self):
        if UnknownEditVariable is None:
            self.skipTest("UnknownEditVariable not available in this version")

        with self.assertRaises(UnknownEditVariable):
            self.solver.suggestValue(self.xm, 50)

    # ---------- Adding/removing constraints ----------

    def test_remove_constraint_changes_solution(self):
        # Constrain two variables:
        # x1 == 0 (required) and x2 >= x1 + 10 (required)
        c_eq = (self.x1 == 0)
        c_gap = (self.x2 >= self.x1 + 10)
        self.solver.addConstraint(c_eq)
        self.solver.addConstraint(c_gap)
        self.solver.updateVariables()

        self.assertTrue(approx_equal(self.x1.value(), 0.0))
        self.assertTrue(approx_equal(self.x2.value(), 10.0))

        # Remove the gap constraint; now nothing pushes x2 above 0
        self.solver.removeConstraint(c_gap)
        self.solver.updateVariables()

        # With only x1 == 0, the default solution tends to keep others at 0
        self.assertTrue(approx_equal(self.x1.value(), 0.0))
        self.assertTrue(approx_equal(self.x2.value(), 0.0))

    def test_remove_unknown_constraint_raises_if_supported(self):
        if UnknownConstraint is None:
            self.skipTest("UnknownConstraint not available in this version")

        phantom = (self.x1 >= 0)
        with self.assertRaises(UnknownConstraint):
            self.solver.removeConstraint(phantom)

    # ---------- Exceptions for infeasible/duplicate constraints ----------

    def test_unsatisfiable_required_constraints_raise_if_supported(self):
        if UnsatisfiableConstraint is None:
            self.skipTest("UnsatisfiableConstraint not available in this version")

        self.solver.addConstraint(self.x1 == 0)
        with self.assertRaises(UnsatisfiableConstraint):
            self.solver.addConstraint(self.x1 == 10)

    def test_duplicate_constraint_raises_if_supported(self):
        if DuplicateConstraint is None:
            self.skipTest("DuplicateConstraint not available in this version")

        c = (self.x1 >= 0)
        self.solver.addConstraint(c)
        with self.assertRaises(DuplicateConstraint):
            self.solver.addConstraint(c)

    # ---------- Constraint.violated() (Kiwi ≥ 1.4) ----------

    def test_constraint_violated_if_available(self):
        # Only run if the method exists on a constraint instance.
        c = (self.x1 == 40) | "weak"
        if not hasattr(c, "violated"):
            self.skipTest("Constraint.violated() not available in this version")

        # Build the system
        self.solver.addConstraint(self.x1 >= 0)
        self.solver.addConstraint(self.x2 <= 100)
        self.solver.addConstraint(self.x2 >= self.x1 + 10)
        self.solver.addConstraint(self.xm == (self.x1 + self.x2) / 2)
        self.solver.addConstraint(c)

        # Push xm to 90 -> x1 becomes 80 (so the weak x1==40 is violated)
        self.solver.addEditVariable(self.xm, "strong")
        self.solver.suggestValue(self.xm, 90)
        self.solver.updateVariables()

        self.assertTrue(c.violated())
        # If we bring xm back to 60 -> x1==40, constraint no longer violated
        self.solver.suggestValue(self.xm, 60)
        self.solver.updateVariables()
        self.assertFalse(c.violated())

    # ---------- Expression building & arithmetic ----------

    def test_expression_arithmetic(self):
        # Check that expressions with scaling and constants behave as expected.
        # Constrain: 2*x1 + 3 == 13  -> x1 == 5
        self.solver.addConstraint(2 * self.x1 + 3 == 13)
        self.solver.updateVariables()
        self.assertTrue(approx_equal(self.x1.value(), 5.0))

        # Add another constraint tying x2 to x1: x2 == 3*x1 - 5 -> with x1=5, x2=10
        self.solver.addConstraint(self.x2 == 3 * self.x1 - 5)
        self.solver.updateVariables()
        self.assertTrue(approx_equal(self.x2.value(), 10.0))

    # ---------- Reset (if available) ----------

    def test_reset_if_available(self):
        if not hasattr(self.solver, "reset"):
            self.skipTest("Solver.reset() not available in this version")

        self.solver.addConstraint(self.x1 >= 0)
        self.solver.addConstraint(self.x1 <= 10)
        self.solver.updateVariables()
        self.assertTrue(0.0 <= self.x1.value() <= 10.0)

        self.solver.reset()
        # After reset, re-adding a conflicting constraint such as x1 == 20 should no longer
        # conflict with earlier bounds (since they’re gone).
        self.solver.addConstraint(self.x1 == 20)
        self.solver.updateVariables()
        self.assertTrue(approx_equal(self.x1.value(), 20.0))

    # ---------- Mixed: add/remove edits, re-solve ----------

    def test_add_remove_edit_variable(self):
        self.solver.addConstraint(self.xm == (self.x1 + self.x2) / 2)
        self.solver.addConstraint(self.x1 >= 0)
        self.solver.addConstraint(self.x2 >= 0)

        # Add xm as edit variable and suggest a value
        self.solver.addEditVariable(self.xm, "medium")
        self.solver.suggestValue(self.xm, 30)
        self.solver.updateVariables()
        self.assertTrue(approx_equal(self.xm.value(), 30.0))

        # Remove edit variable (if supported) and ensure we can still re-solve via hard constraints
        if hasattr(self.solver, "removeEditVariable"):
            self.solver.removeEditVariable(self.xm)
            # Now force x1 and x2 directly
            self.solver.addConstraint(self.x1 == 10)
            self.solver.addConstraint(self.x2 == 50)
            self.solver.updateVariables()
            self.assertTrue(approx_equal(self.xm.value(), 30.0))  # midpoint of 10 and 50

    # ---------- Inequalities saturation & bounds ----------

    def test_bounds_and_saturation(self):
        # x1 bounded [0, 100], prefer weakly at 70, and pull with xm midpoint to 40/100
        self.solver.addConstraint(self.x1 >= 0)
        self.solver.addConstraint(self.x1 <= 100)
        self.solver.addConstraint((self.x1 == 70) | "weak")

        self.solver.addConstraint(self.x2 <= 100)
        self.solver.addConstraint(self.x2 >= 0)
        self.solver.addConstraint(self.xm == (self.x1 + self.x2) / 2)

        self.solver.addEditVariable(self.xm, "strong")
        self.solver.suggestValue(self.xm, 50)  # midpoint target

        self.solver.updateVariables()
        # With xm=50 and both x in [0,100], one symmetric solution is x1=50, x2=50,
        # but the weak preference for x1=70 should bias the solution toward x1≥50.
        # In practice, Cassowary/kiwi respects the stronger edit but tries to satisfy weakly:
        # Expected: x1=70, x2=30  (midpoint 50)
        self.assertTrue(approx_equal(self.xm.value(), 50.0))
        self.assertTrue(approx_equal(self.x1.value(), 70.0))
        self.assertTrue(approx_equal(self.x2.value(), 30.0))


if __name__ == "__main__":
    unittest.main()