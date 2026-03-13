import pytest

from hueyos.install_gui import validate_license_acceptance


def test_validate_license_acceptance_requires_opt_in():
    with pytest.raises(PermissionError):
        validate_license_acceptance(False)


def test_validate_license_acceptance_passes_when_accepted():
    validate_license_acceptance(True)
