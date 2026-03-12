from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from digital_oracle.providers._coerce import _coerce_float, _coerce_int


class TestCoerceFloat(unittest.TestCase):

    def test_none_returns_none(self):
        self.assertIsNone(_coerce_float(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(_coerce_float(""))

    def test_bool_returns_none(self):
        self.assertIsNone(_coerce_float(True))
        self.assertIsNone(_coerce_float(False))

    def test_int_returns_float(self):
        self.assertEqual(_coerce_float(42), 42.0)
        self.assertIsInstance(_coerce_float(42), float)

    def test_float_returns_float(self):
        self.assertEqual(_coerce_float(3.14), 3.14)

    def test_negative_values(self):
        self.assertEqual(_coerce_float(-1.5), -1.5)
        self.assertEqual(_coerce_float(-7), -7.0)

    def test_zero(self):
        self.assertEqual(_coerce_float(0), 0.0)
        self.assertEqual(_coerce_float(0.0), 0.0)

    def test_string_numeric(self):
        self.assertEqual(_coerce_float("3.14"), 3.14)
        self.assertEqual(_coerce_float("42"), 42.0)
        self.assertEqual(_coerce_float("-1.5"), -1.5)

    def test_string_non_numeric_returns_none(self):
        self.assertIsNone(_coerce_float("abc"))
        self.assertIsNone(_coerce_float("N/A"))

    def test_nan_returns_none(self):
        self.assertIsNone(_coerce_float(float("nan")))

    def test_inf_returns_none(self):
        self.assertIsNone(_coerce_float(float("inf")))
        self.assertIsNone(_coerce_float(float("-inf")))

    def test_nan_string_returns_none(self):
        self.assertIsNone(_coerce_float("nan"))
        self.assertIsNone(_coerce_float("NaN"))

    def test_inf_string_returns_none(self):
        self.assertIsNone(_coerce_float("inf"))
        self.assertIsNone(_coerce_float("Infinity"))

    def test_unsupported_type_returns_none(self):
        self.assertIsNone(_coerce_float([1, 2]))
        self.assertIsNone(_coerce_float({"a": 1}))


class TestCoerceInt(unittest.TestCase):

    def test_none_returns_none(self):
        self.assertIsNone(_coerce_int(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(_coerce_int(""))

    def test_bool_returns_none(self):
        self.assertIsNone(_coerce_int(True))
        self.assertIsNone(_coerce_int(False))

    def test_int_returns_int(self):
        self.assertEqual(_coerce_int(42), 42)
        self.assertEqual(_coerce_int(-7), -7)
        self.assertEqual(_coerce_int(0), 0)

    def test_float_returns_int(self):
        self.assertEqual(_coerce_int(3.0), 3)
        self.assertEqual(_coerce_int(3.9), 3)

    def test_float_nan_returns_none(self):
        self.assertIsNone(_coerce_int(float("nan")))

    def test_float_inf_returns_none(self):
        self.assertIsNone(_coerce_int(float("inf")))
        self.assertIsNone(_coerce_int(float("-inf")))

    def test_string_numeric(self):
        self.assertEqual(_coerce_int("42"), 42)
        self.assertEqual(_coerce_int("-7"), -7)

    def test_string_float_returns_none(self):
        # "3.14" is not a valid int string
        self.assertIsNone(_coerce_int("3.14"))

    def test_string_non_numeric_returns_none(self):
        self.assertIsNone(_coerce_int("abc"))
        self.assertIsNone(_coerce_int("N/A"))

    def test_unsupported_type_returns_none(self):
        self.assertIsNone(_coerce_int([1, 2]))
        self.assertIsNone(_coerce_int({"a": 1}))


class TestCoerceSymmetry(unittest.TestCase):
    """Verify _coerce_float and _coerce_int handle booleans identically."""

    def test_bool_excluded_from_both(self):
        self.assertIsNone(_coerce_float(True))
        self.assertIsNone(_coerce_int(True))
        self.assertIsNone(_coerce_float(False))
        self.assertIsNone(_coerce_int(False))


if __name__ == "__main__":
    unittest.main()
