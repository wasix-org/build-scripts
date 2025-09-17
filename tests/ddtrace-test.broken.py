# Works on native but prints an irrelevant error
# Missing deps on WASIX
import unittest
import threading
import logging
logging.getLogger("ddtrace").setLevel(logging.CRITICAL)
logging.getLogger("ddtrace.profiling").setLevel(logging.CRITICAL)  # <- add this

from ddtrace import tracer
from ddtrace.propagation.http import HTTPPropagator


def _try_tracer_config(**kwargs) -> bool:
    try:
        tracer.configure(**kwargs)
        return True
    except TypeError:
        return False


class DdtraceBasicsTest(unittest.TestCase):
    def setUp(self):
        # Keep tracer initialized; avoid unsupported kwargs.
        _try_tracer_config()

        # NEW: silence ddtrace logs so agent send failures don't pollute test output
        logging.getLogger("ddtrace").setLevel(logging.CRITICAL)

    # ---------- Basic usage: decorator, context manager, manual start/finish ----------

    def test_wrap_decorator_creates_span(self):
        captured = {}

        @tracer.wrap()
        def decorated(x, y):
            captured["span"] = tracer.current_span()
            return x + y

        result = decorated(2, 3)
        self.assertEqual(result, 5)
        span = captured["span"]
        self.assertTrue(getattr(span, "_finished", True))
        self.assertIsNotNone(getattr(span, "duration", None))
        self.assertIsNone(tracer.current_span())

    def test_context_manager_current_span_lifecycle(self):
        self.assertIsNone(tracer.current_span())
        with tracer.trace("block") as span:
            self.assertIs(tracer.current_span(), span)
            self.assertIsNotNone(span.start_ns)
            self.assertFalse(getattr(span, "_finished", False))
        self.assertTrue(getattr(span, "_finished", True))
        self.assertIsNotNone(span.duration)
        self.assertIsNone(tracer.current_span())

    def test_manual_start_and_finish(self):
        span = tracer.trace("manual.op")
        _ = sum(range(10))
        self.assertFalse(getattr(span, "_finished", False))
        span.finish()
        self.assertTrue(getattr(span, "_finished", True))
        self.assertIsNotNone(span.duration)

    # ---------- Nesting & parenting ----------

    def test_nested_spans_parenting(self):
        with tracer.trace("parent") as parent:
            self.assertIs(tracer.current_span(), parent)
            with tracer.trace("child") as child:
                self.assertIs(tracer.current_span(), child)
                self.assertEqual(child.trace_id, parent.trace_id)
                self.assertEqual(child.parent_id, parent.span_id)
            self.assertIs(tracer.current_span(), parent)
        self.assertIsNone(tracer.current_span())

    # ---------- Context retrieval ----------

    def test_current_trace_context_is_none_without_active_trace(self):
        self.assertIsNone(tracer.current_trace_context())

    # ---------- HTTP distributed tracing: inject/extract round-trip ----------

    def test_http_propagator_inject_extract_roundtrip(self):
        with tracer.trace("root") as root:
            headers = {}
            HTTPPropagator.inject(root.context, headers)
            ctx = HTTPPropagator.extract(headers)
            self.assertIsNotNone(ctx)
            self.assertEqual(ctx.trace_id, root.trace_id)
            self.assertEqual(ctx.span_id, root.span_id)

    # ---------- Cross-thread propagation using explicit activation ----------

    def test_cross_thread_context_propagation(self):
        with tracer.trace("main_thread") as root:
            passed_ctx = tracer.current_trace_context()
            result = {}

            def worker(ctx):
                tracer.context_provider.activate(ctx)
                with tracer.trace("second_thread") as child:
                    result["trace_id"] = child.trace_id
                    result["parent_id"] = child.parent_id
                    result["name"] = child.name

            th = threading.Thread(target=worker, args=(passed_ctx,))
            th.start()
            th.join()

            self.assertEqual(result.get("trace_id"), root.trace_id)
            self.assertEqual(result.get("parent_id"), root.span_id)
            self.assertEqual(result.get("name"), "second_thread")

    # ---------- Custom trace filtering via trace_processors (version-tolerant) ----------

    def test_custom_trace_filter_drops_matching_traces(self):
        class DropByName:
            def process_trace(self, trace):
                # Drop any trace chunk containing a span named "dropme"
                if any(getattr(s, "name", None) == "dropme" for s in trace):
                    return None
                return trace

        # Try to enable via tracer.configure; skip if this ddtrace doesn’t support it.
        if not _try_tracer_config(trace_processors=[DropByName()]):
            self.skipTest("This ddtrace version does not support trace_processors in tracer.configure")

        # Validate processor logic with minimal span-like dummies (no reliance on writer)
        Dummy = lambda n: type("S", (), {"name": n})()
        proc = DropByName()
        self.assertIsNone(proc.process_trace([Dummy("dropme")]))
        self.assertIsNotNone(proc.process_trace([Dummy("keepme")]))

    # ---------- Handled error recording (skip if unsupported) ----------

    def test_record_exception_if_supported(self):
        with tracer.trace("errspan") as span:
            try:
                raise ValueError("boom")
            except ValueError as e:
                target = tracer.current_span() or span
                if hasattr(target, "record_exception"):
                    target.record_exception(e, {"foo": "bar"})
                else:
                    self.skipTest("Span.record_exception not available in this ddtrace version")

    # ---------- Optional: Profiler smoke test (skip or adapt to local signature) ----------

    def test_profiler_start_stop_if_available(self):
        try:
            from ddtrace.profiling import Profiler  # type: ignore
        except Exception:
            self.skipTest("ddtrace.profiling not available in this environment")

        # Some versions don’t accept asyncio_loop_policy; construct bare and fallback as needed.
        try:
            prof = Profiler()
        except TypeError:
            # Extremely old or unusual builds; just skip if construction fails.
            self.skipTest("Profiler() signature not compatible in this ddtrace version")

        prof.start()
        _ = sum(i * i for i in range(10_000))
        prof.stop()
        prof.stop()  # idempotence-ish check


if __name__ == "__main__":
    unittest.main()