import pytest

from app.utils.observationUtils import extract_cde_observation


def test_returns_full_observation_without_cde_tag():
    observation = "Cliente recebe somente pela manhã."

    assert extract_cde_observation(observation) == observation


def test_can_hide_observation_without_cde_tag():
    observation = "Cliente recebe somente pela manhã."

    assert extract_cde_observation(observation, show_untagged=False) == ""


def test_returns_only_content_between_cde_tags():
    observation = """Texto externo
>CDE
Texto exibido
Outra linha exibida
>CDE
Outro texto externo"""

    assert extract_cde_observation(observation) == (
        "Texto exibido\nOutra linha exibida"
    )


@pytest.mark.parametrize(
    "opening_tag,closing_tag",
    [
        (">CDE", ">CDE"),
        ("> CDE", "> CDE"),
        (">   cde", ">cde"),
        (">cDe", "> CDe"),
    ],
)
def test_accepts_spaces_and_case_variations(opening_tag, closing_tag):
    observation = f"fora {opening_tag} mostrar {closing_tag} fora"

    assert extract_cde_observation(observation) == "mostrar"


def test_does_not_accept_line_break_inside_tag():
    observation = "fora >\nCDE mostrar >\nCDE fora"

    assert extract_cde_observation(observation) == observation


def test_does_not_match_tag_as_word_prefix():
    observation = "fora >CDEMAIS mostrar >CDEMAIS fora"

    assert extract_cde_observation(observation) == observation


def test_joins_multiple_tagged_sections():
    observation = "fora >CDE primeiro >CDE fora >cde segundo >CDE fora"

    assert extract_cde_observation(observation) == "primeiro\nsegundo"


@pytest.mark.parametrize("show_untagged", [True, False])
def test_returns_full_observation_for_unclosed_tag(show_untagged):
    observation = "fora >CDE sem fechamento"

    assert (
        extract_cde_observation(observation, show_untagged=show_untagged) == observation
    )


def test_returns_empty_for_null_observation():
    assert extract_cde_observation(None) == ""
