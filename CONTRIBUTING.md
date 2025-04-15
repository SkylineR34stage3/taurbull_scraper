# Contributing to TaurBull Scraper

Thank you for considering contributing to the TaurBull Scraper project! This document outlines our branching strategy and workflow to ensure smooth collaboration.

## Branching Strategy

We use a simplified Git Flow approach with the following branches:

### Main Branches

- `main` - The production branch containing stable, released code
- `develop` - The integration branch for features and fixes being prepared for release

### Supporting Branches

- `feature/*` - For developing new features (branched from `develop`)
- `bugfix/*` - For fixing bugs (branched from `develop`)
- `hotfix/*` - For critical production fixes (branched from `main`)
- `release/*` - For preparing releases (branched from `develop`)

## Workflow

### Feature Development

1. Create a feature branch from `develop`:
   ```
   git checkout develop
   git pull
   git checkout -b feature/your-feature-name
   ```

2. Work on your feature, committing changes with meaningful messages:
   ```
   git add .
   git commit -m "Add clear description of changes"
   ```

3. Push your feature branch to the remote repository:
   ```
   git push -u origin feature/your-feature-name
   ```

4. When ready, create a pull request to merge into `develop`

### Releases

1. When `develop` has accumulated enough features for a release:
   ```
   git checkout develop
   git pull
   git checkout -b release/1.0.0
   ```

2. Make any release-specific changes (version numbers, docs)
3. Create a pull request to merge into `main`
4. After the PR is approved and merged to `main`, tag the release:
   ```
   git checkout main
   git pull
   git tag -a v1.0.0 -m "Version 1.0.0"
   git push origin v1.0.0
   ```
5. Merge `main` back into `develop`:
   ```
   git checkout develop
   git merge main
   git push
   ```

### Hotfixes

For critical bugs in production:

1. Create a hotfix branch from `main`:
   ```
   git checkout main
   git pull
   git checkout -b hotfix/critical-fix
   ```

2. Fix the issue and create a PR to merge into both `main` and `develop`

## Testing

Always test your changes before creating a pull request:

- Run the scraper in dry-run mode
- Check that logs are properly generated
- Verify the formatted output

## Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Update documentation when necessary 