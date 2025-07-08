import unittest
import six
import io


class TestSixBasicFunctions(unittest.TestCase):

    def test_integer_types(self):
        self.assertTrue(isinstance(1, six.integer_types))
        self.assertFalse(isinstance(1.5, six.integer_types))

    def test_string_types(self):
        self.assertTrue(isinstance(u'hello', six.string_types))
        self.assertTrue(isinstance('hello', six.string_types))

    def test_text_type(self):
        self.assertTrue(isinstance(six.u('hello'), six.text_type))

    def test_binary_type(self):
        self.assertTrue(isinstance(six.b('hello'), six.binary_type))

    def test_iteritems_and_itervalues(self):
        d = {'a': 1, 'b': 2}
        items = list(six.iteritems(d))
        values = list(six.itervalues(d))
        self.assertIn(('a', 1), items)
        self.assertIn(2, values)

    def test_next_function(self):
        it = iter([1, 2, 3])
        self.assertEqual(six.next(it), 1)

    def test_urllib_imports(self):
        # Just test that these are importable from six
        self.assertIsNotNone(six.moves.urllib.request)
        self.assertIsNotNone(six.moves.urllib.parse)

    def test_StringIO(self):
        buf = six.StringIO()
        buf.write("test")
        self.assertEqual(buf.getvalue(), "test")

    def test_print_function(self):
        buf = io.StringIO()
        six.print_("Hello", "World", file=buf)
        self.assertEqual(buf.getvalue().strip(), "Hello World")

    def test_add_metaclass(self):
        class Meta(type):
            def __new__(mcls, name, bases, namespace):
                namespace['added_attr'] = 'yes'
                return super(Meta, mcls).__new__(mcls, name, bases, namespace)

        @six.add_metaclass(Meta)
        class MyClass(object):
            pass

        self.assertEqual(MyClass.added_attr, 'yes')


if __name__ == '__main__':
    unittest.main()