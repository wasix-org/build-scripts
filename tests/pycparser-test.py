import unittest
from pycparser import c_parser, c_ast, c_generator

C_CODE = """
int add(int a, int b) {
    return a + b;
}

int main() {
    int result = add(3, 4);
    return result;
}
"""

class TestPycparserBasics(unittest.TestCase):

    def setUp(self):
        self.parser = c_parser.CParser()
        self.ast = self.parser.parse(C_CODE)

    def test_parse_code(self):
        self.assertIsInstance(self.ast, c_ast.FileAST)
        func_defs = [node for node in self.ast.ext if isinstance(node, c_ast.FuncDef)]
        self.assertGreaterEqual(len(func_defs), 1, "No function definitions found")

    def test_ast_traversal(self):
        func_names = []

        class FuncDefVisitor(c_ast.NodeVisitor):
            def visit_FuncDef(self, node):
                func_names.append(node.decl.name)

        visitor = FuncDefVisitor()
        visitor.visit(self.ast)

        self.assertIn("add", func_names)
        self.assertIn("main", func_names)

    def test_generate_c_from_ast(self):
        generator = c_generator.CGenerator()
        regenerated_code = generator.visit(self.ast)

        self.assertIn("int add(int a, int b)", regenerated_code)
        self.assertIn("int main()", regenerated_code)


if __name__ == '__main__':
    unittest.main()