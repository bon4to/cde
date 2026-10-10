import os

import pytest


@pytest.fixture
def settings_app(monkeypatch):
    os.environ["DEFAULT_DIR"] = os.getcwd()

    import cde as cde_module

    cde_module.app.config["TESTING"] = True
    cde_module.app.config["SECRET_KEY"] = "test-secret"
    monkeypatch.setattr(cde_module.cde, "get_unit", staticmethod(lambda: "API"))
    monkeypatch.setattr(
        cde_module.cde,
        "is_paid_feature_locked",
        staticmethod(lambda _id_page: False),
    )
    monkeypatch.setattr(cde_module.lt, "log", lambda *_args, **_kwargs: None)
    return cde_module


def set_session(client, user_grant):
    with client.session_transaction() as session:
        session["logged_in"] = True
        session["id_user"] = 1
        session["user_grant"] = user_grant


def test_admin_can_update_customer_observation_policy(settings_app, monkeypatch):
    saved_values = []
    monkeypatch.setattr(
        settings_app.systemSettings.SystemSettings,
        "set_show_untagged_customer_observations",
        saved_values.append,
    )

    client = settings_app.app.test_client()
    set_session(client, user_grant=1)
    response = client.post(
        "/logi/settings/",
        data={"show_untagged_observations": "on"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/logi/settings/?saved=observation-policy"
    )
    assert saved_values == [True]


def test_admin_can_open_logistics_settings(settings_app, monkeypatch):
    monkeypatch.setattr(
        settings_app.systemSettings.SystemSettings,
        "show_untagged_customer_observations",
        lambda: True,
    )

    client = settings_app.app.test_client()
    set_session(client, user_grant=1)
    response = client.get("/logi/settings/")

    assert response.status_code == 200
    assert b"Observa\xc3\xa7\xc3\xb5es do cliente sem marca\xc3\xa7\xc3\xa3o" in response.data
    assert b"Observa\xc3\xa7\xc3\xb5es da carga e outros campos" in response.data
    assert b"MOSTRAR TUDO" in response.data


def test_policy_filters_only_customer_observation(settings_app, monkeypatch):
    monkeypatch.setattr(
        settings_app.systemSettings.SystemSettings,
        "show_untagged_customer_observations",
        lambda: False,
    )
    rows = [["Observação do cliente", "Observação da carga"]]
    columns = ["OBS_CLIENTE", "OBS_CARGA"]

    filtered = settings_app.CargaUtils.filter_customer_observations(rows, columns)

    assert filtered == [["", "Observação da carga"]]


def test_non_admin_cannot_update_customer_observation_policy(
    settings_app, monkeypatch
):
    monkeypatch.setattr(
        settings_app.cde,
        "has_permission",
        staticmethod(lambda _id_user, _id_page: True),
    )
    monkeypatch.setattr(
        settings_app.systemSettings.SystemSettings,
        "set_show_untagged_customer_observations",
        lambda _value: pytest.fail("non-admin changed system setting"),
    )

    client = settings_app.app.test_client()
    set_session(client, user_grant=3)
    response = client.post("/logi/settings/")

    assert response.status_code == 403
