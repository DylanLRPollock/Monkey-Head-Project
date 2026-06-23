# Python Support Policy

## Current supported Python version

Monkey-Head-Project / HueyOS currently supports **Python 3.13.x only**.

Supported range:

```text
>=3.13,<3.14
```

## Not currently supported

The following Python versions are not part of the current supported runtime contract:

- Python 3.11.x
- Python 3.12.x

## Python 3.14.x testing status

Python 3.14.x is the active **testing-only** compatibility lane.

It is exercised in experimental CI/package-smoke jobs, but it should not be treated as the supported project runtime until the dependency stack, audio compatibility packages, ML packages, PyGPT/PyHuey integration, and HueyOS runtime path have all been validated.

The 3.14 lane intentionally overrides `requires-python` during install so compatibility can be measured without advertising 3.14 as a supported release/runtime target.

## Tooling enforcement

- `pyproject.toml` requires `>=3.13,<3.14`.
- `.python-version` pins local version-manager flows to `3.13`.
- The Windows `Makefile` path defaults to `py -3.13`.
- Stable CI/package validation runs on Python 3.13; Python 3.14 stays experimental.

## Reason

The active project target is a reproducible V1 runtime. A narrow Python support window reduces dependency churn and keeps the current lab baseline testable.

## Current rule

Use Python 3.13.x for:

- development installs
- lab installs
- staging installs
- editable installs
- requirements validation
- dependency freeze records
- V1 proof-loop work

Do not claim support for another Python version until it has been validated and promoted through a dedicated compatibility pass.
