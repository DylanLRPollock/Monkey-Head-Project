# Dependency snapshots

These files are historical PyHuey environment snapshots kept for reference only.

- They are **not** active install manifests for HueyOS V1.
- CI, editable installs, and the main container build surfaces use the root
  `pyproject.toml` and `requirements.txt` instead.
- The `.pip-snapshot` extension intentionally keeps GitHub dependency scanners
  from treating these archived references as live `requirements*.txt` manifests.

If you need to recreate one of these historical environments, copy the snapshot
to a temporary requirements file outside the active repo manifests and install it
explicitly for that one-off purpose.
