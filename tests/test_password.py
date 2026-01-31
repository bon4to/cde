import pytest

from app.models import misc


class TestHashKey:
    """Tests for hash_key function."""

    def test_returns_hashed_string(self):
        """Should return a hashed string."""
        result = misc.hash_key("password123")
        assert isinstance(result, str)
        assert result != "password123"

    def test_different_passwords_produce_different_hashes(self):
        """Should produce different hashes for different passwords."""
        hash1 = misc.hash_key("password123")
        hash2 = misc.hash_key("different_password")
        assert hash1 != hash2

    def test_same_password_produces_different_hashes(self):
        """Should produce different hashes due to salt even for same password."""
        hash1 = misc.hash_key("password123")
        hash2 = misc.hash_key("password123")
        # PBKDF2 uses salt, so same password produces different hashes
        assert hash1 != hash2


class TestCheckKey:
    """Tests for check_key function."""

    def test_valid_password_returns_true(self):
        """Should return True for correct password."""
        password = "test_password"
        hashed = misc.hash_key(password)
        result = misc.check_key(hashed, password)
        assert result is True

    def test_invalid_password_returns_false(self):
        """Should return False for incorrect password."""
        password = "test_password"
        hashed = misc.hash_key(password)
        result = misc.check_key(hashed, "wrong_password")
        assert result is False

    def test_empty_password(self):
        """Should handle empty password correctly."""
        password = ""
        hashed = misc.hash_key(password)
        result = misc.check_key(hashed, password)
        assert result is True
