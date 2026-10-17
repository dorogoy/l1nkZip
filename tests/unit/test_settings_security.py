import os
import subprocess
import sys

from pydantic import ValidationError
import pytest

from l1nkzip.config import PUBLIC_GENERATOR_ALPHABET, Settings


def test_public_generator_alphabet_is_rejected():
    with pytest.raises(ValidationError, match="public default"):
        Settings(generator_string=PUBLIC_GENERATOR_ALPHABET)


def test_short_generator_alphabet_is_rejected():
    with pytest.raises(ValidationError, match="at least"):
        Settings(generator_string="abcdefghij")


def test_missing_generator_string_is_rejected(monkeypatch):
    monkeypatch.delenv("GENERATOR_STRING", raising=False)
    with pytest.raises(ValidationError, match="public default"):
        Settings()


def test_repeated_generator_characters_are_rejected():
    with pytest.raises(ValidationError, match="repeated"):
        Settings(generator_string="a" * len(PUBLIC_GENERATOR_ALPHABET))


def test_long_custom_generator_alphabet_is_accepted():
    alphabet = "zyxwvutsrqponmlkjihgfedcba98765"
    settings = Settings(generator_string=alphabet)
    assert settings.generator_string == alphabet


def test_default_token_is_rejected():
    with pytest.raises(ValidationError, match="default token '__change_me__' is not allowed"):
        Settings(token="__change_me__")


def test_short_token_is_rejected():
    with pytest.raises(ValidationError, match="at least 16 characters"):
        Settings(token="short_token_123")


def test_whitespace_token_is_rejected():
    with pytest.raises(ValidationError, match="at least 16 characters"):
        Settings(token=" " * 16)


def test_missing_token_is_rejected(monkeypatch):
    monkeypatch.delenv("TOKEN", raising=False)
    with pytest.raises(ValidationError, match="default token '__change_me__' is not allowed"):
        Settings()


def test_valid_token_is_accepted():
    token = "a_valid_admin_token_12345"
    settings = Settings(token=token)
    assert settings.token == token


def test_process_refuses_to_start_with_public_alphabet():
    env = os.environ.copy()
    env["GENERATOR_STRING"] = PUBLIC_GENERATOR_ALPHABET
    env["DB_TYPE"] = "inmemory"
    completed = subprocess.run(
        [sys.executable, "-c", "import l1nkzip.main"],
        cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "public default" in completed.stderr + completed.stdout


def test_process_refuses_to_start_with_default_token():
    env = os.environ.copy()
    env["TOKEN"] = "__change_me__"
    env["DB_TYPE"] = "inmemory"
    completed = subprocess.run(
        [sys.executable, "-c", "import l1nkzip.main"],
        cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "default token '__change_me__' is not allowed" in completed.stderr + completed.stdout
