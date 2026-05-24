# Publishing GemFilter to PyPI

GemFilter uses GitHub Actions and PyPI Trusted Publishing for releases.

Trusted Publishing is preferred over a long-lived PyPI API token. PyPI exchanges the GitHub Actions OIDC identity for a short-lived publishing token during the release workflow.

## One-time PyPI setup

Configure a Trusted Publisher on PyPI for the `gemfilter` project.

Use these values:

| Field | Value |
|---|---|
| PyPI project | `gemfilter` |
| Owner | `liangzid` |
| Repository | `GemFilter` |
| Workflow filename | `publish.yml` |
| Environment name | `pypi` |

If the PyPI project does not exist yet, create it through PyPI's pending publisher flow using the same values.

References:

- PyPI Trusted Publishers: https://docs.pypi.org/trusted-publishers/
- Publishing with a Trusted Publisher: https://docs.pypi.org/trusted-publishers/using-a-publisher/
- PyPA publish action: https://github.com/pypa/gh-action-pypi-publish

## Release process

1. Update the version in:
   - `pyproject.toml`
   - `gemfilter/__init__.py`
   - README badges or docs if needed

2. Run tests locally:

   ```bash
   python -m pytest -q
   ```

3. Commit and push:

   ```bash
   git add .
   git commit -m "Release GemFilter vX.Y.Z"
   git push origin master
   ```

4. Create and push the matching tag:

   ```bash
   git tag -a vX.Y.Z -m "GemFilter vX.Y.Z"
   git push origin vX.Y.Z
   ```

5. Create a GitHub release for the same tag.

   ```bash
   gh release create vX.Y.Z --title "GemFilter vX.Y.Z" --notes "Release notes..."
   ```

6. The workflow `.github/workflows/publish.yml` runs automatically when the GitHub release is published.

## Important checks

- The GitHub release tag must match the version in `pyproject.toml`.
  - Example: `version = "0.2.1"` requires tag `v0.2.1`.
- The publish job uses the GitHub Actions environment named `pypi`.
- The publish job must have `id-token: write`; this is required for PyPI Trusted Publishing.
- Do not add a PyPI API token unless Trusted Publishing is unavailable.

## Manual workflow dispatch

The workflow also supports `workflow_dispatch` for manual runs. Use manual dispatch only when you intentionally want to publish the current checked-out version and PyPI will accept that version.

PyPI does not allow replacing an already-published version.
