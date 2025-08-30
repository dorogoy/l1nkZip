import pytest

from l1nkzip.generator import (
    DEFAULT_BLOCK_SIZE,
    MIN_LENGTH,
    UrlEncoder,
    debase,
    decode,
    decode_url,
    enbase,
    encode,
    encode_url,
)


@pytest.fixture
def test_encoder():
    """Test encoder fixture"""
    return UrlEncoder(
        alphabet="mn6j2c4rv8bpygw95z7hsdaetxuk3fq", block_size=DEFAULT_BLOCK_SIZE
    )


def test_encode_url(test_encoder):
    """Test that URL encoding produces consistent results"""
    # The result must be always the same
    assert test_encoder.encode_url(23, MIN_LENGTH) == "5wppq"


def test_decode_url(test_encoder):
    """Test that URL decoding returns the original integer"""
    # Can be decoded returning the original integer
    assert test_encoder.decode_url("5wppq") == 23


def test_encode_decode():
    """Test that encoding and decoding are reversible"""
    for i in range(100):
        encoded = encode_url(i)
        decoded = decode_url(encoded)
        assert i == decoded


def test_min_length():
    """Test minimum length padding"""
    assert len(encode_url(1, min_length=5)) == 5
    assert len(encode_url(1000, min_length=10)) == 10


def test_alphabet():
    """Test custom alphabet functionality"""
    custom_alphabet = "0123456789abcdef"
    encoder = UrlEncoder(alphabet=custom_alphabet)
    encoded = encoder.encode_url(1234)
    assert all(char in custom_alphabet for char in encoded)
    decoded = encoder.decode_url(encoded)
    assert decoded == 1234


def test_generator_string():
    """Test that different alphabets produce different results"""
    encoder2 = UrlEncoder(
        alphabet="mn6j2c4rv8bpygw95z7hsdaetxuk3fqABCD",
        block_size=DEFAULT_BLOCK_SIZE,
    )
    assert encoder2.encode_url(23, MIN_LENGTH) != "5wppq"


def test_encode():
    """Test basic encoding functionality"""
    assert encode(123) == 14548992


def test_decode():
    """Test basic decoding functionality"""
    assert decode(14548992) == 123


def test_enbase():
    """Test base conversion encoding"""
    assert enbase(123) == "mmmjq"


def test_debase():
    """Test base conversion decoding"""
    assert debase("mmmjq") == 123


def test_url_encoder_initialization():
    """Test UrlEncoder initialization with custom parameters"""
    encoder = UrlEncoder(alphabet="abc123", block_size=16)
    assert encoder.alphabet == "abc123"
    assert encoder.block_size == 16
