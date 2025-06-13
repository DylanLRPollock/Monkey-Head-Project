from scripts.check_inter_program_connectivity import (
    check_inter_program_connectivity,
)


def test_check_inter_program_connectivity():
    assert check_inter_program_connectivity() is True
