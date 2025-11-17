def rabin_karp(text, pattern, base=256, mod=10**9+7):
    if not pattern:
        return []

    m, n = len(pattern), len(text)
    if m > n:
        return []

    hpattern = 0
    htext = 0
    h = 1

    for _ in range(m - 1):
        h = (h * base) % mod

    for i in range(m):
        hpattern = (hpattern * base + ord(pattern[i])) % mod
        htext = (htext * base + ord(text[i])) % mod

    result = []

    for i in range(n - m + 1):

        if hpattern == htext and text[i : i + m] == pattern:
            result.append(i)

        if i < n - m:
            htext = (base * (htext - ord(text[i]) * h) + ord(text[i + m])) % mod

            if htext < 0:
                htext += mod

    return result
