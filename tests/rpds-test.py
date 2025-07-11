from rpds import HashTrieMap, HashTrieSet, List

def test_hashtrie_map():
    m = HashTrieMap()
    m2 = m.insert("a", 1)
    m3 = m2.insert("b", 2)
    assert m == HashTrieMap()  # m unchanged
    assert m2.get("a") == 1
    assert m3.get("b") == 2
    assert m3.get("a") == 1
    assert m3.remove("a").get("a") is None

def test_hashtrie_set():
    s = HashTrieSet()
    s2 = s.insert("x")
    s3 = s2.insert("y")
    assert s == HashTrieSet()  # s unchanged
    assert "x" in s2
    assert "y" in s3
    assert "x" in s3
    assert "z" not in s3
    assert "x" not in s3.remove("x")

def test_list():
    l = List()
    l2 = l.push_front(1)
    l3 = l2.push_front(2)
    assert l == List()  # l unchanged
    assert list(l3) == [2, 1]

    # Simulate "pop front"
    front = next(iter(l3))
    tail = List(list(l3)[1:])
    assert front == 2
    assert list(tail) == [1]

if __name__ == "__main__":
    test_hashtrie_map()
    test_hashtrie_set()
    test_list()
    print("All rpds-py basic tests passed.")