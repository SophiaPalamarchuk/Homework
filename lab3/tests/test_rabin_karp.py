from src.rabin_karp import rabin_karp

def test_rk_basic():
    assert rabin_karp("ababcabcabababd", "ababd") == [10]

def test_rk_multiple():
    assert rabin_karp("aaaaa", "aa") == [0, 1, 2, 3]

def test_rk_empty():
    assert rabin_karp("abc", "") == []
