# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Documentation and audit tracking continue for v101.1 stabilization work; no additional completed items are recorded here yet.

## [101.1] - 2026-05-12

### Added
- Package build/install smoke workflow for wheel/sdist build, fresh-environment install, import checks (`huey`, `hueyos`, `huey.api`), and CLI checks (`huey --help`, `huey-api --help`).
- Security policy document for Bandit baseline usage and CI enforcement of new medium/high findings.

### Changed
- PyHuey cockpit alignment phase 1: added `pyhuey` console-script alias while retaining `pygpt`, updated package description/URLs for PyHuey cockpit identity, and preserved upstream PyGPT compatibility/provenance.
- Namespace migration kickoff documented with canonical `hueyos` direction and `huey` compatibility path preserved during transition.
- Docker alignment documented for v101.1 with HueyOS runtime expectations (`huey-api`, non-root `hueyos`, repository package install) instead of PyGPT as primary runtime.
