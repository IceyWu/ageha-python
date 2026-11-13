# Release guide

Ageha uses GitHub Actions for quality checks, preview distribution, and versioned
releases. Authentication uses PyPI Trusted Publishing through GitHub OIDC.

## Workflows

| Workflow | Trigger | Result |
| :--- | :--- | :--- |
| CI | Push to main, pull request, or manual run | Lint, tests, build, metadata checks, and isolated wheel installation |
| Preview Release | Manual run on main | A unique development version published to TestPyPI and verified after upload |
| Release | Push to main or manual run | A maintained version PR; after merge, a version tag and GitHub release |

Preview Release checks both distribution hashes against the registry, downloads
the published wheel, and imports it in a fresh environment.

## Versioning

Release Please reads Conventional Commit messages and updates the version,
changelog, and lockfile through a version PR.

| Commit | Release intent |
| :--- | :--- |
| fix: | Patch |
| feat: | Feature; advances the minor version during 0.x |
| feat!: or BREAKING CHANGE: | Breaking change |
| docs: or chore: | Normally no standalone release |

Review the version PR before merging. The Release workflow explicitly checks
the generated branch because GITHUB_TOKEN-created PRs do not trigger normal
pull-request workflows.

## Publishing configuration

| Destination | Workflow file | GitHub environment |
| :--- | :--- | :--- |
| TestPyPI | preview.yml | preview |
| PyPI | release.yml | pypi |

Trusted Publisher configuration must match the repository owner, repository
name, workflow filename, and environment. See the
[PyPI documentation](https://docs.pypi.org/trusted-publishers/) for account setup
and publisher configuration.

Production uploads require the repository variable PYPI_ENABLED=true and a
configured PyPI Trusted Publisher.

## Recovery

Before upload, revert the source commit or close the version PR. After upload,
published files are immutable: yank a broken version and release a corrected
version. Set PYPI_ENABLED=false to suspend production uploads.

If an upload fails after creating a GitHub release, inspect the failed step
before retrying. Re-run failed jobs while their artifacts remain available.
Each Preview Release run generates a unique version.
