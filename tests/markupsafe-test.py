from markupsafe import escape, Markup

def test_escape():
    assert escape("<div>") == "&lt;div&gt;"
    assert escape("1 > 2 & 3 < 4") == "1 &gt; 2 &amp; 3 &lt; 4"
    assert escape("'single quotes'") == "&#39;single quotes&#39;"
    assert escape('"double quotes"') == '&#34;double quotes&#34;'
    print("test_escape passed.")

def test_markup_construction():
    m = Markup("<strong>Safe</strong>")
    assert str(m) == "<strong>Safe</strong>"
    assert m.__html__() == "<strong>Safe</strong>"
    print("test_markup_construction passed.")

def test_markup_concat():
    m = Markup("<strong>")
    result = m + "hello & goodbye</strong>"
    assert str(result) == "<strong>hello &amp; goodbye&lt;/strong&gt;"
    print("test_markup_concat passed.")

def test_markup_join():
    parts = [Markup("<b>") + "bold", " and ", "plain</b>"]
    joined = Markup("").join(parts)
    assert str(joined) == "<b>bold and plain&lt;/b&gt;"
    print("test_markup_join passed.")

def test_equality_and_safety():
    m1 = Markup("<i>italics</i>")
    m2 = Markup("<i>italics</i>")
    assert m1 == m2
    assert m1 == "<i>italics</i>"  # Markup subclasses str
    print("test_equality_and_safety passed.")

if __name__ == "__main__":
    test_escape()
    test_markup_construction()
    test_markup_concat()
    test_markup_join()
    test_equality_and_safety()
    print("All tests passed.")