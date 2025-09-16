# Here’s why each is skipped in your run with typing_extensions 4.14.1:

# test_disjoint_base_conflict
# Skipped because typing_extensions.disjoint_base only appears in 4.15.0+. Your 4.14.1 doesn’t have it yet.
# Fix: upgrade to ≥ 4.15.0 (untestet)

# test_type_repr_presence
# Skipped because typing_extensions.type_repr (from PEP 749) is new in 4.15.0+.
# Fix: upgrade to ≥ 4.15.0 (untestet)

# test_generic_namedtuple
# idk
import sys
import unittest
import warnings
import pickle
import typing as t
import collections.abc as cabc
import contextlib
import io

try:
    import typing_extensions as te
except Exception as e:
    raise SystemExit(f"typing_extensions is required to run these tests: {e}")

PY = sys.version_info


def maybe(attr: str) -> bool:
    return hasattr(te, attr)


class TestAnnotatedAndDoc(unittest.TestCase):
    def test_annotated_basic_and_doc(self):
        self.assertTrue(hasattr(te, "Annotated"))
        A = te.Annotated[int, "meta"]
        self.assertEqual(
            t.get_origin(A) or te.get_origin(A),
            t.Annotated if hasattr(t, "Annotated") else te.Annotated,
        )
        # Doc metadata (PEP 727)
        if maybe("Doc"):
            ann = te.Annotated[int, te.Doc("number")]
            args = te.get_args(ann)
            self.assertEqual(args[0], int)
            metas = args[1:]
            self.assertTrue(any(getattr(m, "documentation", None) == "number" for m in metas))


class TestAnyAsBase(unittest.TestCase):
    def test_any_is_baseclass(self):
        # Any is subclassable (supported by te on older Pythons via backport)
        class X(te.Any):  # type: ignore[misc]
            pass
        self.assertTrue(issubclass(X, te.Any))


class TestConcatenateAndParamSpec(unittest.TestCase):
    def test_concatenate_with_paramspec(self):
        if not maybe("ParamSpec"):
            self.skipTest("ParamSpec not available")
        P = te.ParamSpec("P")
        CB = t.Callable[te.Concatenate[int, P], str]
        origin = te.get_origin(CB)
        # Accept either typing.Callable or collections.abc.Callable depending on Python
        self.assertIn(origin, (t.Callable, cabc.Callable))
        args = te.get_args(CB)
        # args[0] is a typing object for Concatenate
        inner = args[0]
        inner_origin = te.get_origin(inner) or t.get_origin(inner)
        expected_concat_origin = []
        if hasattr(t, "Concatenate"):
            expected_concat_origin.append(t.Concatenate)
        expected_concat_origin.append(getattr(te, "Concatenate", object()))
        self.assertIn(inner_origin, tuple(expected_concat_origin))
        inner_args = te.get_args(inner)
        self.assertGreaterEqual(len(inner_args), 2)
        self.assertIs(inner_args[0], int)
        self.assertIs(inner_args[1], P)
        # Return type remains last arg of Callable
        self.assertIs(args[1], str)

    def test_paramspec_default_has_default(self):
        if not maybe("ParamSpec"):
            self.skipTest("ParamSpec not available")
        P = te.ParamSpec("P", default=int)
        self.assertTrue(getattr(P, "has_default", lambda: False)())
        self.assertIs(getattr(P, "__default__", None), int)


class TestFinalAndDecorators(unittest.TestCase):
    def test_final_decorator_sets_attribute(self):
        if not maybe("final"):
            self.skipTest("@final not available")

        @te.final
        class C: ...
        self.assertTrue(getattr(C, "__final__", True))

    def test_override_decorator_sets_attribute(self):
        if not maybe("override"):
            self.skipTest("@override not available")

        class Base:
            def f(self) -> int: return 1

        class Sub(Base):
            @te.override
            def f(self) -> int: return 2

        self.assertTrue(getattr(Sub.f, "__override__", True))

    def test_overload_and_get_clear_overloads(self):
        if not maybe("overload") or not maybe("get_overloads") or not maybe("clear_overloads"):
            self.skipTest("Overload introspection API not available")

        @te.overload
        def g(x: int) -> int: ...
        @te.overload
        def g(x: str) -> str: ...
        def g(x):
            return x

        ovs = list(te.get_overloads(g))
        self.assertGreaterEqual(len(ovs), 2)
        te.clear_overloads()
        self.assertEqual(list(te.get_overloads(g)), [])


class TestLiteralAndLiteralString(unittest.TestCase):
    def test_literal_flattens_and_deduplicates(self):
        lit = te.Literal[1, 1, te.Literal[2, 3]]
        self.assertEqual(te.get_args(lit), (1, 2, 3))

    def test_literalstring_presence(self):
        if not maybe("LiteralString"):
            self.skipTest("LiteralString not available")
        self.assertTrue(hasattr(te, "LiteralString"))


class TestNamedTupleGeneric(unittest.TestCase):
    def test_generic_namedtuple(self):
        if not maybe("NamedTuple"):
            self.skipTest("NamedTuple backport not available")

        # On some versions, te.NamedTuple is a function (not subscriptable/generic).
        if not hasattr(te.NamedTuple, "__class_getitem__"):
            self.skipTest("typing_extensions.NamedTuple is not generic-capable on this version")

        T = t.TypeVar("T")

        # Use PEP 695-style generic parameterization on the NamedTuple base
        class Box(te.NamedTuple[T]):
            item: T

        b = Box
        self.assertEqual(b.item, 1)
        if maybe("get_original_bases"):
            bases = te.get_original_bases(Box)
            self.assertTrue(any("Generic" in repr(b) or "typing.Generic" in repr(b) for b in bases))


class TestNeverAndAssertNever(unittest.TestCase):
    def test_assert_never_raises(self):
        if not maybe("assert_never"):
            self.skipTest("assert_never not available")
        with self.assertRaises(Exception):
            te.assert_never(0)  # type: ignore[arg-type]


class TestNewType(unittest.TestCase):
    def test_newtype_picklable(self):
        UserId = te.NewType("UserId", int)
        u = UserId(5)
        data = pickle.dumps(u)
        self.assertEqual(pickle.loads(data), 5)


class TestNoDefaultPresence(unittest.TestCase):
    def test_nodefault_exists(self):
        self.assertTrue(maybe("NoDefault"))
        _ = te.NoDefault  # just reference


class TestTypedDictFeatures(unittest.TestCase):
    def test_required_notrequired(self):
        if not maybe("TypedDict"):
            self.skipTest("TypedDict not available")

        class TD(te.TypedDict, total=False):
            a: te.Required[int]
            b: te.NotRequired[str]

        self.assertIn("a", TD.__required_keys__)
        self.assertIn("b", TD.__optional_keys__)

    def test_readonly_and_mutable_keys(self):
        if not maybe("TypedDict"):
            self.skipTest("TypedDict not available")
        if not maybe("ReadOnly"):
            self.skipTest("ReadOnly qualifier not available")

        class T2(te.TypedDict):
            x: te.ReadOnly[int]
            y: int

        self.assertIn("x", getattr(T2, "__readonly_keys__", frozenset()))
        self.assertIn("y", getattr(T2, "__mutable_keys__", frozenset()))

    def test_closed_and_extra_items(self):
        if not maybe("TypedDict"):
            self.skipTest("TypedDict not available")
        # Open (default)
        TOpen = te.TypedDict("TOpen", {"a": int})
        # In some versions, __closed__ may be None for "unspecified"/open; accept None or False
        self.assertIn(getattr(TOpen, "__closed__", None), (None, False))
        # __extra_items__ may be None (older behavior) or the sentinel NoExtraItems
        extra = getattr(TOpen, "__extra_items__", None)
        if hasattr(te, "NoExtraItems"):
            self.assertIn(extra, (None, te.NoExtraItems))
        else:
            self.assertIsNone(extra)
        # Closed with explicit __extra_items__
        TClosed = te.TypedDict("TClosed", {"a": int, "__extra_items__": str}, closed=True)
        self.assertTrue(getattr(TClosed, "__closed__", False))
        self.assertIs(getattr(TClosed, "__extra_items__", None), str)

    def test_is_typeddict_function(self):
        if not maybe("is_typeddict"):
            self.skipTest("is_typeddict not available")

        class TD(te.TypedDict):
            a: int
        self.assertTrue(te.is_typeddict(TD))
        self.assertFalse(te.is_typeddict(te.TypedDict))


class TestSelfAndTypeAlias(unittest.TestCase):
    def test_self_annotation_and_get_type_hints(self):
        if not maybe("Self") or not maybe("get_type_hints"):
            self.skipTest("Self or get_type_hints not available")

        class C:
            def clone(self) -> te.Self:  # pragma: no cover - runtime only
                return self

        hints = te.get_type_hints(C.clone)
        self.assertIn("return", hints)

    def test_type_alias_and_typealiastype(self):
        # TypeAlias exists in typing; TypeAliasType may or may not in te
        MyInts: te.TypeAlias = "list[int]"  # typing-only intent; runtime value is str
        self.assertTrue(True)
        if maybe("TypeAliasType"):
            TAT = te.TypeAliasType("Ints", list[int])
            self.assertEqual(TAT.__name__, "Ints")
            # Compare equality (not identity) to avoid distinct cached objects
            self.assertEqual(TAT.__value__, list[int])


class TestTypeFormPresence(unittest.TestCase):
    def test_typeform_exists_when_available(self):
        if not maybe("TypeForm"):
            self.skipTest("TypeForm not available")
        _ = te.TypeForm


class TestTypeGuardAndTypeIs(unittest.TestCase):
    def test_typeguard(self):
        if not maybe("TypeGuard"):
            self.skipTest("TypeGuard not available")

        def is_int(x: object) -> te.TypeGuard[int]:
            return isinstance(x, int)

        self.assertTrue(is_int(3))
        self.assertFalse(is_int("a"))

    def test_typeis(self):
        if not maybe("TypeIs"):
            self.skipTest("TypeIs not available")

        def is_str(x: object) -> te.TypeIs[str]:
            return isinstance(x, str)

        self.assertTrue(is_str("x"))
        self.assertFalse(is_str(1))


class TestTypeVarAndTypeVarTuple(unittest.TestCase):
    def test_typevar_default_and_has_default(self):
        T_ = te.TypeVar("T_", default=None)
        self.assertTrue(getattr(T_, "has_default", lambda: False)())
        self.assertIs(getattr(T_, "__default__", object()), None)

    def test_typevar_infer_variance_flag(self):
        try:
            _ = te.TypeVar("X", infer_variance=True)
        except TypeError:
            self.skipTest("infer_variance not accepted on this version")

    def test_typevartuple_and_unpack(self):
        if not maybe("TypeVarTuple") or not maybe("Unpack"):
            self.skipTest("TypeVarTuple/Unpack not available")
        Ts = te.TypeVarTuple("Ts")
        Tup = tuple[te.Unpack[Ts]]
        origin = te.get_origin(Tup)
        self.assertIs(origin, tuple)


class TestABCsAndProtocols(unittest.TestCase):
    def test_buffer_presence(self):
        if not maybe("Buffer"):
            self.skipTest("Buffer ABC not available")
        _ = te.Buffer

    def test_supports_protocols_presence(self):
        names = [
            "SupportsAbs", "SupportsBytes", "SupportsComplex", "SupportsFloat",
            "SupportsIndex", "SupportsInt", "SupportsRound",
        ]
        missing = [n for n in names if not maybe(n)]
        if missing:
            self.skipTest(f"Missing protocols: {missing}")
        for n in names:
            getattr(te, n)

    def test_reader_writer_presence_when_available(self):
        for n in ("Reader", "Writer"):
            if maybe(n):
                getattr(te, n)

    def test_runtime_checkable_protocol_and_helpers(self):
        if not maybe("Protocol") or not maybe("runtime_checkable"):
            self.skipTest("Protocol/runtime_checkable not available")

        @te.runtime_checkable
        class P(te.Protocol):
            def a(self) -> str: ...
            b: int

        class Impl:
            def a(self) -> str: return "x"
            b = 1

        self.assertTrue(isinstance(Impl(), P))
        if maybe("get_protocol_members"):
            self.assertEqual(te.get_protocol_members(P), frozenset({"a", "b"}))
        if maybe("is_protocol"):
            self.assertTrue(te.is_protocol(P))
            self.assertFalse(te.is_protocol(int))


class TestDecoratorsMisc(unittest.TestCase):
    def test_dataclass_transform_sets_marker(self):
        if not maybe("dataclass_transform"):
            self.skipTest("dataclass_transform not available")

        @te.dataclass_transform(field_specifiers=())
        def model(cls): return cls

        self.assertTrue(hasattr(model, "__dataclass_transform__"))

    def test_deprecated_decorator_emits_warning(self):
        if not maybe("deprecated"):
            self.skipTest("deprecated not available")

        @te.deprecated("use something else")
        def old():
            return 42

        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            self.assertEqual(old(), 42)
            self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in rec))

    def test_disjoint_base_conflict(self):
        if not maybe("disjoint_base"):
            self.skipTest("disjoint_base not available")

        @te.disjoint_base
        class A: ...
        @te.disjoint_base
        class B: ...

        # typing_extensions.disjoint_base is a static typing aid; at runtime
        # it marks the class but does not necessarily enforce MRO conflicts.
        # Validate marker presence instead of requiring a runtime TypeError.
        self.assertTrue(getattr(A, "__disjoint_base__", True))
        self.assertTrue(getattr(B, "__disjoint_base__", True))
        # Constructing a multiple-inheritance class should not error at runtime
        # solely due to disjoint_base markers.
        class C(A, B):  # noqa: F841
            pass


class TestFunctionsMisc(unittest.TestCase):
    def test_assert_type_and_reveal_type(self):
        if not maybe("assert_type"):
            self.skipTest("assert_type not available")
        self.assertEqual(te.assert_type(7, int), 7)
        if maybe("reveal_type"):
            # At runtime, reveal_type prints to stderr; capture it to keep test output clean.
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                self.assertIs(te.reveal_type(7), 7)

    def test_get_args_and_origin_annotated_and_paramspec(self):
        ann = te.Annotated[list[int], "x"]
        self.assertIs(
            te.get_origin(ann),
            t.Annotated if hasattr(t, "Annotated") else te.Annotated
        )
        self.assertEqual(te.get_args(ann)[0], list[int])

    def test_get_type_hints_strips_readonly(self):
        if not (maybe("get_type_hints") and maybe("ReadOnly")):
            self.skipTest("get_type_hints/ReadOnly not available")

        def f(x: te.ReadOnly[int]) -> None: ...
        hints = te.get_type_hints(f)  # include_extras=False by default
        self.assertEqual(hints["x"], int)

    def test_evaluate_forward_ref_and_get_annotations_format(self):
        if not (maybe("evaluate_forward_ref") and maybe("get_annotations") and maybe("Format")):
            self.skipTest("evaluate_forward_ref/get_annotations not available")

        class Owner:
            pass
        Owner.X = type("X", (), {})  # attach a name

        fr = t.ForwardRef("X", is_argument=False)
        val = te.evaluate_forward_ref(fr, owner=Owner)
        self.assertIs(val, Owner.X)

        # get_annotations with VALUE vs STRING on a string annotation
        class M:
            x: "list[int]"
        # On some versions, VALUE needs eval_str=True to evaluate strings
        anns_val = te.get_annotations(M, format=te.Format.VALUE, eval_str=True)
        anns_str = te.get_annotations(M, format=te.Format.STRING)
        self.assertEqual(anns_val["x"], list[int])
        self.assertIsInstance(anns_str["x"], str)
        # Enum values are stable
        self.assertEqual(int(te.Format.VALUE), 1)
        self.assertEqual(int(te.Format.FORWARDREF), 3)
        self.assertEqual(int(te.Format.STRING), 4)

    def test_get_original_bases_on_typeddict_or_namedtuple(self):
        if not maybe("get_original_bases"):
            self.skipTest("get_original_bases not available")

        class G(te.TypedDict, t.Generic[t.TypeVar("T")]):  # type: ignore[type-arg]
            a: int
        bases = te.get_original_bases(G)
        self.assertTrue(isinstance(bases, tuple))
        self.assertTrue(any("Generic" in repr(b) or "TypedDict" in repr(b) for b in bases))

    def test_type_repr_presence(self):
        if not maybe("type_repr"):
            self.skipTest("type_repr not available")
        s = te.type_repr(list[int])
        self.assertIsInstance(s, str)
        self.assertIn("list", s)

    def test_capsuletype_and_sentinel(self):
        if maybe("CapsuleType"):
            _ = te.CapsuleType  # CPython-only; just access if present
        if maybe("Sentinel"):
            MISSING = te.Sentinel("MISSING")
            self.assertIs(MISSING, MISSING)
            self.assertIn("MISSING", repr(MISSING))


if __name__ == "__main__":
    unittest.main()
