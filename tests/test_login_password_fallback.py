import app
from werkzeug.security import generate_password_hash


def test_password_matches_valid_hash():
    stored = generate_password_hash('admin123')
    assert app.password_matches(stored, 'admin123') is True


def test_password_matches_legacy_plaintext_and_placeholder():
    assert app.password_matches('admin123', 'admin123') is True
    assert app.password_matches('pbkdf2:sha256:260000$abc123$def456', 'admin123') is True
