import pytest

from bouwdossiers import tools


@pytest.mark.parametrize(
    "test_input, stadsdeel, dossiernr",
    [
        ('ABC1234', 'ABC', '1234'),  # default formatting
        ('ABC_1234', 'ABC', '1234'),  # with underscore formatting
        ('abc1234', 'ABC', '1234'),  # with lowercase letter stadsdeelcode formatting
        ('abc_1234', 'ABC', '1234'),  # with underscore and lowercase letter stadsdeelcode formatting
    ]
)
def test_separate_dossier(test_input, stadsdeel, dossiernr):
    stadsdeel, dossiernr = tools.separate_dossier('ABC1234')
    assert stadsdeel == 'ABC'
    assert dossiernr == '1234'


@pytest.mark.parametrize(
    "test_input",
    [
        'ABC',  # missing dossiernr
        '1234',  # missing stadsdeelcode
        'A1234',  # only one letter stadsdeelcode should also fail
        'ABCD1234'  # four or more letter stadsdeelcodes should also fail
    ]
)
def test_separate_dossier_errors(test_input):
    # Test whether wrongly formatted inputs fail
    with pytest.raises(tools.InvalidDossier):
        tools.separate_dossier(test_input)
