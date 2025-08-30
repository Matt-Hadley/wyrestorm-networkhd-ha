# CI/CD Workflows

GitHub Actions workflows for Home Assistant custom integration.

## Workflows

### `pr-validation.yml` - Pull Request Validation

**Pull Requests:**

- Complete health check (`make health-check`) including:
  - Configuration validation
  - Code formatting and quality checks (Ruff, MyPy)
  - Security audits and dependency checks
  - Comprehensive testing with coverage
  - Home Assistant component validation
- HACS validation for integration compliance
- Hassfest validation for HA standards
- Coverage reporting with PR comments
- Artifact uploads (test reports, coverage)

### `release.yml` - Release Management

**Main Branch:**

- Automated release creation via [release-please](https://github.com/googleapis/release-please-action)
- Complete health check validation
- Coverage badge updates
- HACS integration zip creation
- GitHub release with distribution files (.zip)
- Post-release HACS and Hassfest validation

**_How Release-Please Works:_**

1. **Analyzes commits** since last release using conventional commit format
2. **Creates release PR** with updated changelog and version bump
3. **Merging the PR** triggers the actual release workflow:
   - Runs full validation suite
   - Updates coverage badge with released code coverage
   - Updates manifest.json version
   - Creates integration zip files for HACS
   - Creates GitHub release with assets
   - Validates HACS compliance post-release

**Notes:**

- Dependency updates handled by Dependabot (see `.github/dependabot.yml`)
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

- **HACS Integration**: Automatic validation on PR and post-release
- **Hassfest Validation**: Home Assistant component standards compliance
- **Manifest Version**: Automatically updated during releases
- **Integration Zip**: Created for HACS distribution

## Monitoring

- **GitHub Actions Tab**: View workflow runs
- **Status Checks**: Required for PR merging
- **HACS Validation**: Ensures integration compliance
- **Artifacts**: Download test packages and reports

## Resources

- [GitHub Actions](https://docs.github.com/en/actions)
- [Release-Please Action](https://github.com/googleapis/release-please-action)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [HACS Documentation](https://hacs.xyz/docs/publish/integration/)
- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)