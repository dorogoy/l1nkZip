"""
Short URL Generator
===================

Python implementation for generating Tiny URL- and bit.ly-like URLs.

A bit-shuffling approach is used to avoid generating consecutive, predictable
URLs.  However, the algorithm is deterministic and will guarantee that no
collisions will occur.

The URL alphabet is fully customizable and may contain any number of
characters.  By default, digits and lower-case letters are used, with
some removed to avoid confusion between characters like o, O and 0.  The
default alphabet is shuffled and has a prime number of characters to further
improve the results of the algorithm.

The block size specifies how many bits will be shuffled.  The lower BLOCK_SIZE
bits are reversed.  Any bits higher than BLOCK_SIZE will remain as is.
BLOCK_SIZE of 0 will leave all bits unaffected and the algorithm will simply
be converting your integer to a different base.

The intended use is that incrementing, consecutive integers will be used as
keys to generate the short URLs.  For example, when creating a new URL, the
unique integer ID assigned by a database could be used to generate the URL
by using this module.  Or a simple counter may be used.  As long as the same
integer is not used twice, the same short URL will not be generated twice.

The module supports both encoding and decoding of URLs. The min_length
parameter allows you to pad the URL if you want it to be a specific length.

Sample Usage:

>>> import short_url
>>> url = short_url.encode_url(12)
>>> print url
LhKA
>>> key = short_url.decode_url(url)
>>> print key
12

Use the functions in the top-level of the module to use the default encoder.
Otherwise, you may create your own UrlEncoder object and use its encode_url
and decode_url methods.

Author: Michael Fogleman
License: MIT
Link: http://code.activestate.com/recipes/576918/
"""

import unittest

from l1nkzip.config import settings

DEFAULT_BLOCK_SIZE = 24
MIN_LENGTH = 5


class UrlEncoder(object):
    def __init__(
        self, alphabet=settings.generator_string, block_size=DEFAULT_BLOCK_SIZE
    ):
        self.alphabet = alphabet
        self.block_size = block_size
        self.mask = (1 << block_size) - 1
        self.mapping = list(range(block_size))
        self.mapping.reverse()

    def encode_url(self, n: int, min_length: int = MIN_LENGTH) -> str:
        return self.enbase(self.encode(n), min_length)

    def decode_url(self, n: str) -> int:
        return self.decode(self.debase(n))

    def encode(self, n: int) -> int:
        return (n & ~self.mask) | self._encode(n & self.mask)

    def _encode(self, n: int) -> int:
        result = 0
        for i, b in enumerate(self.mapping):
            if n & (1 << i):
                result |= 1 << b
        return result

    def decode(self, n: int) -> int:
        return (n & ~self.mask) | self._decode(n & self.mask)

    def _decode(self, n: int) -> int:
        result = 0
        for i, b in enumerate(self.mapping):
            if n & (1 << b):
                result |= 1 << i
        return result

    def enbase(self, x: int, min_length: int = MIN_LENGTH) -> str:
        result = self._enbase(x)
        padding = self.alphabet[0] * (min_length - len(result))
        return "%s%s" % (padding, result)

    def _enbase(self, x: int) -> str:
        n = len(self.alphabet)
        if x < n:
            return self.alphabet[x]
        return self._enbase(x // n) + self.alphabet[x % n]

    def debase(self, x: str) -> int:
        n = len(self.alphabet)
        result = 0
        for i, c in enumerate(reversed(x)):
            result += self.alphabet.index(c) * (n**i)
        return result


DEFAULT_ENCODER = UrlEncoder()


def encode(n: int) -> int:
    return DEFAULT_ENCODER.encode(n)


def decode(n: int) -> int:
    return DEFAULT_ENCODER.decode(n)


def enbase(n: int, min_length: int = MIN_LENGTH):
    return DEFAULT_ENCODER.enbase(n, min_length)


def debase(n: str) -> int:
    return DEFAULT_ENCODER.debase(n)


def encode_url(n: int, min_length: int = MIN_LENGTH) -> str:
    return DEFAULT_ENCODER.encode_url(n, min_length)


def decode_url(n: str) -> int:
    return DEFAULT_ENCODER.decode_url(n)


class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.encoder = UrlEncoder(
            alphabet="mn6j2c4rv8bpygw95z7hsdaetxuk3fq", block_size=DEFAULT_BLOCK_SIZE
        )

    def test_encode_url(self):
        # The result must be always the same
        self.assertEqual(self.encoder.encode_url(23, MIN_LENGTH), "5wppq")

    def test_decode_url(self):
        # Can be decoded returning the original integer
        self.assertEqual(self.encoder.decode_url("5wppq"), 23)

    def test_generator_string(self):
        encoder2 = UrlEncoder(
            alphabet="mn6j2c4rv8bpygw95z7hsdaetxuk3fqABCD",
            block_size=DEFAULT_BLOCK_SIZE,
        )
        self.assertNotEqual(encoder2.encode_url(23, MIN_LENGTH), "5wppq")


if __name__ == "__main__":
    for a in range(0, 200000, 37):
        b = encode(a)
        c = enbase(b)
        d = debase(c)
        e = decode(d)
        assert a == e
        assert b == d
        c = (" " * (7 - len(c))) + c
        print("%6d %12d %s %12d %6d" % (a, b, c, d, e))
