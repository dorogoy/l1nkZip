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
