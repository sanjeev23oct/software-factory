"""Personal and infrastructure data that should not reach a model or land in code.

    from pii import redact, find
    text, counts = redact(text)        # "[EMAIL-1]", "[IP-2]" ... in place of the values
    find(text)                         # [(kind, value)] for checking a change

Structured values only: emails, phone numbers, IP and MAC addresses, Aadhaar and PAN numbers,
card numbers. Checksums (Verhoeff for Aadhaar, Luhn for cards) keep ordinary numbers from
matching. Names and free-text details cannot be recognised this way.
"""

import ipaddress
import re

# Values that are safe by definition: documentation and test ranges, placeholders.
SAFE_EMAIL_DOMAINS = re.compile(r"@(?:[\w-]+\.)*(?:example\.(?:com|org|net)|test|invalid|localhost|example)$", re.I)
SAFE_IPS = [ipaddress.ip_network(n) for n in ("127.0.0.0/8", "0.0.0.0/32", "255.255.255.255/32", "192.0.2.0/24",
                                               "198.51.100.0/24", "203.0.113.0/24", "::1/128", "2001:db8::/32")]

PATTERNS = [
    ("EMAIL", re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w-])")),
    ("CARD", re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")),
    ("AADHAAR", re.compile(r"(?<!\d)[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?!\d)")),
    ("PHONE", re.compile(r"(?<![\w+])(?:\+91[ -]?|0)?[6-9]\d{4}[ -]?\d{5}(?!\d)")),
    ("PAN", re.compile(r"(?<![A-Z0-9])[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z](?![A-Z0-9])")),
    ("MAC", re.compile(r"(?<![0-9A-Fa-f:-])(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f:-])")),
    ("IP", re.compile(r"(?<![\w.:])(?:(?:\d{1,3}\.){3}\d{1,3}|(?:[0-9A-Fa-f]{1,4}:){2,7}[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{1,4})*)(?![\w:])(?!\.\w)")),   # a full stop that ends the sentence is not part of it
]

_VERHOEFF_D = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5], [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
               [3, 4, 0, 1, 2, 8, 9, 5, 6, 7], [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
               [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3], [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
               [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]]
_VERHOEFF_P = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4], [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
               [8, 9, 1, 6, 0, 4, 3, 5, 2, 7], [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
               [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]]


def _verhoeff(digits):
    c = 0
    for i, d in enumerate(reversed(digits)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][int(d)]]
    return c == 0


def _luhn(digits):
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d) * (2 if i % 2 else 1)
        total += n - 9 if n > 9 else n
    return total % 10 == 0


def _real(kind, value):
    """False for matches that are not what they look like: versions, test values, bad checksums."""
    digits = re.sub(r"\D", "", value)
    if kind == "EMAIL":
        return not SAFE_EMAIL_DOMAINS.search(value)
    if kind == "CARD":
        return 13 <= len(digits) <= 19 and _luhn(digits) and len(set(digits)) > 2
    if kind == "AADHAAR":
        return len(digits) == 12 and _verhoeff(digits)
    if kind == "IP":
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            return False
        return not any(address in net for net in SAFE_IPS if net.version == address.version)
    if kind == "MAC":
        return value.lower() not in ("00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff")
    return True


def find(text, allow=()):
    """[(kind, value)] in the order they appear, skipping values matching any `allow` pattern."""
    found, taken = [], []
    for kind, pattern in PATTERNS:
        for m in pattern.finditer(text):
            if any(m.start() < end and start < m.end() for start, end in taken):
                continue   # already claimed by a more specific kind
            value = m.group().strip()
            if _real(kind, value) and not any(re.search(a, value) for a in allow):
                found.append((m.start(), kind, value))
                taken.append((m.start(), m.end()))
    return [(kind, value) for _, kind, value in sorted(found)]


def redact(text, allow=()):
    """(text with each value replaced by a numbered placeholder, {kind: count})."""
    names, counts = {}, {}
    for kind, value in find(text, allow):
        if value not in names:
            counts[kind] = counts.get(kind, 0) + 1
            names[value] = "[{}-{}]".format(kind, counts[kind])
    for value in sorted(names, key=len, reverse=True):
        text = text.replace(value, names[value])
    return text, counts


def describe(counts):
    labels = {"EMAIL": "email", "PHONE": "phone number", "IP": "IP address", "MAC": "MAC address",
              "AADHAAR": "Aadhaar number", "PAN": "PAN", "CARD": "card number"}
    plural = lambda word: word + ("es" if word.endswith("s") else "s")
    return ", ".join("{} {}".format(n, labels.get(k, k.lower()) if n == 1 else plural(labels.get(k, k.lower())))
                     for k, n in sorted(counts.items()))
