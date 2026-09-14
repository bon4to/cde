from app.services import licenseManager


def test_external_license_generator_script_exists():
    script = open("scripts/generate_license_key.py", "r", encoding="utf-8").read()

    assert "--module" in script
    assert "--secret" in script
    assert "encrypt_license_payload" in script
    assert "from flask" not in script


def test_license_token_round_trip_allows_modules():
    token = licenseManager.encrypt_license_payload(
        {"modules": ["MOV008", "PRC010"]},
        "test-secret",
    )

    payload = licenseManager.decrypt_license_token(token, "test-secret")

    assert payload["modules"] == ["MOV008", "PRC010"]


def test_license_token_rejects_wrong_secret():
    token = licenseManager.encrypt_license_payload(
        {"modules": ["ENV006"]},
        "right-secret",
    )

    assert licenseManager.decrypt_license_token(token, "wrong-secret") == {}


def test_load_license_reads_external_file(tmp_path, monkeypatch):
    license_file = tmp_path / "cde-license.key"
    token = licenseManager.encrypt_license_payload(
        {"modules": ["mov008", "ENV006"]},
        "test-secret",
    )
    license_file.write_text(token, encoding="utf-8")

    monkeypatch.setenv(licenseManager.LICENSE_FILE_ENV, str(license_file))
    monkeypatch.setenv(licenseManager.LICENSE_SECRET_ENV, "test-secret")

    assert licenseManager.allowed_modules() == {"MOV008", "ENV006"}
    assert licenseManager.is_module_allowed("mov008")
    assert not licenseManager.is_module_allowed("PRC010")
