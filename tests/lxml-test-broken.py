import unittest
from lxml import etree, html, objectify
from io import StringIO, BytesIO


class TestLxmlFeatures(unittest.TestCase):

    def test_parse_xml_string(self):
        etree.fromstring("<root><child/></root>")

    def test_create_and_serialize(self):
        root = etree.Element("root")
        etree.SubElement(root, "child").text = "text"
        self.assertIn(b"<child>text</child>", etree.tostring(root))

    def test_tree_modification(self):
        root = etree.Element("root")
        child = etree.SubElement(root, "child")
        root.remove(child)
        self.assertEqual(len(root), 0)

    def test_namespace_xpath(self):
        xml = '''<root xmlns:h="http://example.com"><h:child>data</h:child></root>'''
        root = etree.fromstring(xml)
        result = root.xpath('//h:child', namespaces={'h': 'http://example.com'})
        self.assertEqual(result[0].text, 'data')

    def test_xmlschema_validation(self):
        schema = etree.XMLSchema(etree.XML('''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:element name="root" type="xs:string"/>
        </xs:schema>'''))
        valid = etree.XML("<root>text</root>")
        self.assertTrue(schema.validate(valid))

    def test_dtd_validation(self):
        dtd = etree.DTD(StringIO("<!ELEMENT root (#PCDATA)>"))
        doc = etree.XML("<root>text</root>")
        self.assertTrue(dtd.validate(doc))

    def test_relaxng_validation(self):
        rng = etree.RelaxNG(etree.XML('''
        <element name="root" xmlns="http://relaxng.org/ns/structure/1.0">
          <text/>
        </element>'''))
        self.assertTrue(rng.validate(etree.XML("<root>text</root>")))

    def test_xpath_custom(self):
        root = etree.XML("<root><val>1</val><val>2</val></root>")
        vals = root.xpath("//val/text()")
        self.assertEqual(vals, ["1", "2"])

    def test_custom_xpath_function(self):
        class MyResolver(etree.Resolver):
            def resolve(self, url, id, context):
                return self.resolve_string("<external>content</external>", context)
        parser = etree.XMLParser()
        parser.resolvers.add(MyResolver())
        tree = etree.parse(StringIO('<!DOCTYPE root SYSTEM "foo.dtd"><root/>'), parser)

    def test_xslt_transform(self):
        xml = etree.XML("<root><name>World</name></root>")
        xslt = etree.XSLT(etree.XML('''
        <xsl:stylesheet version="1.0"
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
          <xsl:template match="/"><hello><xsl:value-of select="root/name"/></hello></xsl:template>
        </xsl:stylesheet>'''))
        result = xslt(xml)
        self.assertEqual(str(result), "<?xml version=\"1.0\"?>\n<hello>World</hello>\n")

    def test_html_parsing(self):
        doc = html.fromstring("<html><body><h1>Title</h1></body></html>")
        self.assertEqual(doc.xpath("//h1")[0].text, "Title")

    def test_html_fragment(self):
        frags = html.fragments_fromstring("<p>One</p><p>Two</p>")
        self.assertEqual([f.text for f in frags], ["One", "Two"])

    def test_elementpath(self):
        root = etree.XML("<root><a/><b/></root>")
        result = root.find("a")
        self.assertEqual(result.tag, "a")

    def test_elementtree_io(self):
        root = etree.Element("root")
        tree = etree.ElementTree(root)
        buffer = BytesIO()
        tree.write(buffer)
        buffer.seek(0)
        parsed = etree.parse(buffer)
        self.assertEqual(parsed.getroot().tag, "root")

    def test_iterparse(self):
        stream = BytesIO(b"<root><a/><b/></root>")
        tags = [el.tag for _, el in etree.iterparse(stream)]
        self.assertIn("a", tags)

    def test_objectify_usage(self):
        root = objectify.fromstring("<root><val>5</val></root>")
        self.assertEqual(root.val, 5)

    def test_custom_parser_options(self):
        parser = etree.XMLParser(remove_blank_text=True)
        xml = etree.XML("<root>\n  <child>text</child>\n</root>", parser)
        self.assertEqual(len(xml), 1)

    def test_comments_and_pis(self):
        root = etree.XML("<root><!-- comment --><?pi test?></root>")
        self.assertEqual(len(root), 2)

    def test_cdata_section(self):
        root = etree.Element("root")
        cdata = etree.CDATA("some <CDATA> content")
        root.text = cdata
        self.assertIn("<![CDATA[", etree.tostring(root).decode())


if __name__ == "__main__":
    unittest.main()