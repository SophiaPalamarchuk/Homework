from src.kmp import kmp_search

def test_kmp_basic():
    assert kmp_search("ababcabcabababd", "ababd") == [10]

def test_kmp_multiple():
    assert kmp_search("aaaaa", "aa") == [0, 1, 2, 3]

def test_kmp_empty():
    assert kmp_search("abc", "") == []
