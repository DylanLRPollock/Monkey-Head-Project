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
- Python 3.14.x

## Python 3.14.x research status

Python 3.14.x is considered **research-stage only**.

It may be explored in isolated branches or throwaway environments, but it should not be treated as the supported project runtime until the dependency stack, audio compatibility packages, ML packages, PyGPT/PyHuey integration, and HueyOS runtime path have all been validated.

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
