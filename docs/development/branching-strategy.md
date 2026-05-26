# Branching Strategy

```
feature/my-feature ──PR──▶  dev  ──PR──▶  main  ──▶  Release
```

## Branches

| Branch | Purpose | Protected |
|--------|---------|-----------|
| **main** | Stable release branch. Commits here are tagged and released. | Yes — no direct pushes |
| **dev** | Integration branch for completed features. | Yes — no direct pushes |
| **feature/*** | Feature branches off `dev` — individual work items. | No |

## Workflow

1. **Feature work**: Branch from `dev` as `feature/<name>`. Do the work. Open a PR into `dev`.
2. **Merge to dev**: Squash-merge the feature PR into `dev`. Dev should always be in a working/testable state.
3. **Weekly release**: Once a week (or as needed), open a PR from `dev` → `main`.
4. **Release**: Merge `dev` → `main`. Tag the merge commit as `v<version>`. Build the release artifact (Flatpak).
5. **Distribute**: Upload the release to GitHub Releases with changelog.

## Hotfixes

If a critical fix is needed on `main` before the weekly merge:
1. Branch from `main` as `hotfix/<name>`.
2. Open a PR into `main`.
3. After merge, immediately merge `main` back into `dev` so dev includes the fix.
