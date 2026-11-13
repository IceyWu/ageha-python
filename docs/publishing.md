# Release Guide / 发布指南

Author: **Lev Wu**. Package: ageha. Repository: IceyWu/ageha-python.
The repository owner is the current GitHub login, not the author display name.

## Accounts

PyPI and TestPyPI are separate accounts. Register on both, verify email and
enable two-factor authentication. Passwords and recovery codes stay with the user.

## TestPyPI Trusted Publisher

After login open https://test.pypi.org/manage/account/publishing/ and add a
pending publisher for GitHub:

| Field | Value |
|---|---|
| PyPI project name | ageha |
| Owner | IceyWu |
| Repository name | ageha-python |
| Workflow name | preview.yml |
| Environment name | preview |

Run Actions > Preview Release > Run workflow on main.
CI generates a unique 0.1.0.devN version, tests Linux and Windows, builds wheel
and source distributions, validates metadata and publishes using OIDC.
Verification compares both artifacts against registry SHA-256 hashes and imports
the downloaded wheel in an isolated environment.

## Production

When real model code is ready, configure a pending publisher at
https://pypi.org/manage/account/publishing/ with workflow release.yml and
environment pypi. All other fields match the TestPyPI configuration.
Set repository variable PYPI_ENABLED=true only when ready for real releases.

Release Please maintains a version PR using Conventional Commits. Merge it to
create a tag and GitHub release, then publish within the same workflow.
No long-lived PyPI API token is required. The workflow explicitly checks the
release PR branch, since GITHUB_TOKEN-created PRs do not trigger PR workflows.

## Versioning

- fix: a patch release.
- feat: a feature release (0.x minor bumps enabled).
- feat!: or BREAKING CHANGE: a breaking change.
- docs: and chore: normally do not produce standalone releases.

The manifest starts at 0.0.0. Review generated version changes before merging.

## Recovery

Before publishing, revert the source commit or close the version PR.
After publishing, never replace a distribution. Yank a broken version and publish
a corrected newer version. Set PYPI_ENABLED=false to disable production uploads.
Every preview run uses a unique version.

If uploading failed after creating a release, inspect the failure and re-run the
failed workflow jobs while artifacts remain available. Do not create another
release with the same version or modify previously uploaded artifacts.
