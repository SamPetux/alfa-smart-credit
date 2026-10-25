from backend.app.identity.passwords import hash_password, verify_password


def test_hash_and_verify() -> None:
    hashed = hash_password("client-demo-pass")
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password("client-demo-pass", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("client-demo-pass", None)
