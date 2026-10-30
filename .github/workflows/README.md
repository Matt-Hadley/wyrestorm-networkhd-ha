# CI/CD Workflows

GitHub Actions workflows for Home Assistant custom integration.

## Workflows

### `pr-validation.yml` - Pull Request Validation

**Pull Requests:**

- **Quality Checks & Tests** job: `make health-check`, which runs
  - Ruff format check and lint
  - MyPy (strict) against the installed Home Assistant and library types
  - Prettier check of JSON, YAML and Markdown
  - Vulture (dead code) and Bandit (security)
  - the tests with coverage (`coverage.xml`, `htmlcov/`)
  - project structure and version checks
- Coverage comment on the PR, and the reports uploaded as artifacts
- **HACS Validation** job: HACS action and hassfest

Every check fails the job on errors. `main` is protected: a pull request needs the **Quality Checks & Tests** and **HACS
Validation** checks to pass before it is merged.

### `release.yml` - Release Management

**Main Branch:**

- Automated release creation via [release-please](https://github.com/googleapis/release-please-action), configured by
  `release-please-config.json` and `.release-please-manifest.json`
- HACS and hassfest validation of the release tag (a failure stops the release)
- Complete health check validation
- Coverage badge updates
- HACS integration zip creation
- GitHub release with distribution files (.zip) and build provenance attestations

**_How Release-Please Works:_**

1. **Analyzes commits** since last release using conventional commit format
2. **Creates release PR** with updated changelog and the version bumped in `manifest.json`
3. **Merging the PR** triggers the actual release workflow:
   - Validates the tag with HACS and hassfest
   - Runs full validation suite
   - Updates coverage badge with released code coverage
   - Creates integration zip files for HACS
   - Creates GitHub release with assets

**Notes:**

- Dependency updates handled by Dependabot (see `.github/dependabot.yml`), including the SHA-pinned actions
- Workflows default to read-only permissions; each job grants only what it uses
- Integration published as zip files for HACS (not PyPI)

## Required Secrets

```bash
# Coverage badge (for gist updates)
GIST_SECRET=your_github_personal_access_token_with_gist_scope
GIST_ID=your_coverage_badge_gist_id
```

**Note:** No PyPI secrets needed - this publishes to HACS via GitHub releases.

## Usage

**Feature Development:**

```bash
git commit -m "feat: add new sensor type"
git push origin feature-branch
# Create PR on GitHub
```

**Bug Fix:**

```bash
git commit -m "fix: resolve coordinator timeout issue"
git push origin fix-branch
# Create PR on GitHub
```

**Breaking Change:**

```bash
git commit -m "feat!: change coordinator API

BREAKING CHANGE: Coordinator constructor now requires explicit timeout"
git push origin breaking-branch
# Create PR on GitHub
```

## Home Assistant Specific

- **HACS Integration**: Validation on every PR and before each release
- **Hassfest Validation**: Home Assistant component standards compliance
- **Manifest Version**: Bumped by release-please in the release PR
- **Integration Zip**: Created for HACS distribution

## Monitoring

- **GitHub Actions Tab**: View workflow runs
- **Required status checks**: Quality Checks & Tests and HACS Validation must pass to merge into `main`
- **Artifacts**: Download test packages and reports

## Resources

- [GitHub Actions](https://docs.github.com/en/actions)
- [Release-Please Action](https://github.com/googleapis/release-please-action)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [HACS Documentation](https://hacs.xyz/docs/publish/integration/)
- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
