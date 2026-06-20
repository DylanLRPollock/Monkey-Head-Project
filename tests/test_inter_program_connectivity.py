# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Inter Program Connectivity module (tests)

from scripts.check_inter_program_connectivity import (
    check_inter_program_connectivity as legacy_connectivity_check,
)
from scripts.repo.check_inter_program_connectivity import (
    check_inter_program_connectivity as structured_connectivity_check,
)


def test_check_inter_program_connectivity():
    assert legacy_connectivity_check() is True
    assert structured_connectivity_check() is True
