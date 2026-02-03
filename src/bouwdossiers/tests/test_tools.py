import pytest

from bouwdossiers import tools


@pytest.mark.parametrize(
    "test_input, expected_stadsdeel, expected_dossiernr",
    [
        ("AB_1234", "AB", "1234"),  # default formatting
        ("AB_34-16-0501", "AB", "34-16-0501"),  # default formatting
        ("AB_P15-43398", "AB", "P15-43398"),  # default formatting
        ("ab_1234", "AB", "1234"),  # with lowercase letter stadsdeelcode formatting
        (
            "ab_1234",
            "AB",
            "1234",
        ),  # with underscore and lowercase letter stadsdeelcode formatting
        (
            "ab_1234",
            "AB",
            "1234",
        ),  # with underscore and lowercase letter stadsdeelcode formatting
        # The same but with four letters
        ("ABCD_1234", "ABCD", "1234"),  # default formatting
        ("ABCD_34-16-0501", "ABCD", "34-16-0501"),  # default formatting
        ("ABCD_P15-43398", "ABCD", "P15-43398"),  # default formatting
        ("abcd_1234", "ABCD", "1234"),  # with lowercase letter stadsdeelcode formatting
        (
            "abcd_1234",
            "ABCD",
            "1234",
        ),  # with underscore and lowercase letter stadsdeelcode formatting
        (
            "abcd_1234",
            "ABCD",
            "1234",
        ),  # with underscore and lowercase letter stadsdeelcode formatting
    ],
)
def test_separate_dossier_four_letters(test_input, expected_stadsdeel, expected_dossiernr):
    stadsdeel, dossiernr = tools.separate_dossier(test_input)
    assert stadsdeel == expected_stadsdeel
    assert dossiernr == expected_dossiernr


@pytest.mark.parametrize(
    "test_input",
    [
        "ABC",  # missing dossiernr
        "1234",  # missing stadsdeelcode
        "A_1234",  # only one letter stadsdeelcode should also fail
        "ABCDE_1234",  # five or more letter stadsdeelcodes should also fail
    ],
)
def test_separate_dossier_errors(test_input):
    # Test whether wrongly formatted inputs fail
    with pytest.raises(tools.InvalidDossier):
        tools.separate_dossier(test_input)
