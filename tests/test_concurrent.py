"""Tests for digital_oracle.concurrent – the gather() utility."""

from __future__ import annotations

import threading
import time
import unittest

from digital_oracle.concurrent import GatherError, GatherResult, gather


class TestGatherBasic(unittest.TestCase):
    """Core gather() behaviour."""

    def test_all_succeed(self):
        result = gather({
            "a": lambda: 1,
            "b": lambda: "hello",
            "c": lambda: [1, 2, 3],
        })
        self.assertTrue(result.ok)
        self.assertEqual(result.get("a"), 1)
        self.assertEqual(result.get("b"), "hello")
        self.assertEqual(result.get("c"), [1, 2, 3])

    def test_empty_tasks(self):
        result = gather({})
        self.assertTrue(result.ok)
        self.assertEqual(result.results, {})
        self.assertEqual(result.errors, {})

    def test_single_task(self):
        result = gather({"only": lambda: 42})
        self.assertTrue(result.ok)
        self.assertEqual(result.get("only"), 42)


class TestGatherErrorHandling(unittest.TestCase):
    """Partial failure and error propagation."""

    def test_partial_failure_returns_successful_results(self):
        def bad():
            raise ValueError("boom")

        result = gather({
            "good": lambda: 42,
            "bad": bad,
        })
        self.assertFalse(result.ok)
        self.assertEqual(result.get("good"), 42)
        self.assertIn("bad", result.errors)
        self.assertIsInstance(result.errors["bad"], ValueError)

    def test_get_reraises_stored_error(self):
        def bad():
            raise RuntimeError("oops")

        result = gather({"task": bad})
        with self.assertRaises(RuntimeError) as ctx:
            result.get("task")
        self.assertIn("oops", str(ctx.exception))

    def test_get_or_returns_default_on_failure(self):
        def bad():
            raise RuntimeError("oops")

        result = gather({"task": bad})
        self.assertIsNone(result.get_or("task", None))
        self.assertEqual(result.get_or("task", "fallback"), "fallback")

    def test_get_or_returns_result_on_success(self):
        result = gather({"task": lambda: 99})
        self.assertEqual(result.get_or("task", None), 99)

    def test_all_fail(self):
        def bad_a():
            raise ValueError("a")

        def bad_b():
            raise TypeError("b")

        result = gather({"a": bad_a, "b": bad_b})
        self.assertFalse(result.ok)
        self.assertEqual(len(result.errors), 2)
        self.assertEqual(len(result.results), 0)


class TestGatherFailFast(unittest.TestCase):
    """fail_fast=True raises GatherError immediately."""

    def test_fail_fast_raises_gather_error(self):
        def bad():
            raise ValueError("fail fast")

        with self.assertRaises(GatherError) as ctx:
            gather({"bad": bad, "good": lambda: 1}, fail_fast=True)

        exc = ctx.exception
        self.assertIn("bad", exc.errors)
        self.assertIsInstance(exc.errors["bad"], ValueError)

    def test_fail_fast_attaches_partial_results(self):
        """GatherError should carry whatever results completed before the failure."""
        def bad():
            raise ValueError("boom")

        with self.assertRaises(GatherError) as ctx:
            gather({"bad": bad}, fail_fast=True)

        exc = ctx.exception
        self.assertIsInstance(exc.results, dict)
        self.assertIsInstance(exc.errors, dict)


class TestGatherConcurrency(unittest.TestCase):
    """Verify tasks actually run in parallel."""

    def test_tasks_overlap_in_time(self):
        """Three 100ms tasks should complete in ~100ms, not ~300ms."""
        def slow():
            time.sleep(0.1)
            return True

        start = time.monotonic()
        result = gather({"a": slow, "b": slow, "c": slow})
        elapsed = time.monotonic() - start

        self.assertTrue(result.ok)
        self.assertLess(elapsed, 0.25)

    def test_max_workers_limits_parallelism(self):
        """max_workers=1 serialises execution but still returns correct results."""
        result = gather(
            {"a": lambda: 1, "b": lambda: 2, "c": lambda: 3},
            max_workers=1,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.get("a"), 1)
        self.assertEqual(result.get("b"), 2)
        self.assertEqual(result.get("c"), 3)

    def test_tasks_run_on_different_threads(self):
        """Each task should execute on a distinct thread."""
        tids: dict[str, int] = {}
        lock = threading.Lock()

        def record(name: str):
            def fn():
                with lock:
                    tids[name] = threading.current_thread().ident
                return name
            return fn

        result = gather({
            "a": record("a"),
            "b": record("b"),
        })
        self.assertTrue(result.ok)
        # At least one task should run on a thread different from the main thread
        main_tid = threading.current_thread().ident
        self.assertTrue(
            tids["a"] != main_tid or tids["b"] != main_tid,
            "at least one task should run off the main thread",
        )


class TestGatherResult(unittest.TestCase):
    """GatherResult data class behaviour."""

    def test_ok_true_when_no_errors(self):
        r = GatherResult(results={"a": 1}, errors={})
        self.assertTrue(r.ok)

    def test_ok_false_when_errors_present(self):
        r = GatherResult(results={}, errors={"a": ValueError()})
        self.assertFalse(r.ok)

    def test_frozen(self):
        r = GatherResult()
        with self.assertRaises(AttributeError):
            r.ok = False  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
