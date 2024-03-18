import pytest

from bouwdossiers import tools


@pytest.mark.parametrize(
    "test_input, expected_stadsdeel, expected_dossiernr",
    [
        ("AB1234", "AB", "1234"),  # default formatting
        ("AB_1234", "AB", "1234"),  # with underscore formatting
        ("ab1234", "AB", "1234"),  # with lowercase letter stadsdeelcode formatting
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
        ("ABCD1234", "ABCD", "1234"),  # default formatting
        ("ABCD_1234", "ABCD", "1234"),  # with underscore formatting
        ("abcd1234", "ABCD", "1234"),  # with lowercase letter stadsdeelcode formatting
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
def test_separate_dossier_four_letters(
    test_input, expected_stadsdeel, expected_dossiernr
):
    stadsdeel, dossiernr = tools.separate_dossier(test_input)
    assert stadsdeel == expected_stadsdeel
    assert dossiernr == expected_dossiernr


@pytest.mark.parametrize(
    "test_input",
    [
        "ABC",  # missing dossiernr
        "1234",  # missing stadsdeelcode
        "A1234",  # only one letter stadsdeelcode should also fail
        "ABCDE1234",  # five or more letter stadsdeelcodes should also fail
    ],
)
def test_separate_dossier_errors(test_input):
    # Test whether wrongly formatted inputs fail
    with pytest.raises(tools.InvalidDossier):
        tools.separate_dossier(test_input)
