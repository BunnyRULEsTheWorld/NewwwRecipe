# Versioning and Sync Workflow

This project uses GitHub `main` as the single source of truth.

## Core rule

A file is not part of the official project simply because it exists locally, in a ZIP, in a chat attachment, or in a WorkBuddy workspace. It becomes official only after it is committed and pushed to this repository.

## One-time recovery / consolidation

When a local working copy may contain files that are newer than GitHub:

1. Do **not** overwrite either side blindly.
2. Make a backup copy of the local project folder.
3. In the local Git repository, fetch the remote state:

```bash
git fetch origin
git status
git branch --show-current
git log --oneline --decorate -n 10
git log --oneline --decorate origin/main -n 10
```

4. If the local folder is not already linked to this repository, clone a fresh copy instead of trying to repair unknown Git metadata:

```bash
git clone https://github.com/BunnyRULEsTheWorld/NewwwRecipe.git NewwwRecipe-clean
```

5. Treat the clean clone as the integration directory. Copy only genuine newer project artifacts from the old working folder into the corresponding paths.
6. Never copy `.git/`, `.venv/`, `.env`, caches, IDE folders, temporary exports, or API keys.
7. Review changes before committing:

```bash
git status
git diff --stat
git diff
```

8. Run the relevant tests / benchmark smoke checks.
9. Commit the recovered baseline in logical commits and push it.

## Normal WorkBuddy workflow

For every future change, WorkBuddy should follow this exact sequence.

### 1. Start from current GitHub state

```bash
git switch main
git fetch origin
git pull --ff-only origin main
```

`--ff-only` is deliberate: if local `main` has diverged, stop instead of silently creating a merge commit.

### 2. Create a task branch

Use one branch per coherent change:

```bash
git switch -c feat/<short-name>
# or fix/<short-name>, docs/<short-name>, exp/<short-name>
```

Examples:

```text
feat/fridge-ui
exp/evidence-only
fix/cie-parser
docs/final-readme
```

### 3. Modify only on the task branch

Before editing, read:

- `PROJECT_STATE.md`
- `AGENTS.md`
- relevant docs / schemas / scripts

Do not change benchmark definitions, frozen cases, canonical metrics or CIE weights incidentally while implementing an unrelated task.

### 4. Validate before commit

At minimum:

```bash
git status
git diff --check
git diff --stat
pytest
```

If the change touches benchmark data or evaluation code, also run the corresponding validation / smoke command and inspect generated outputs.

### 5. Commit with a meaningful message

Recommended prefixes:

- `feat:` user-facing functionality
- `fix:` bug fix
- `exp:` experiment / evaluation work
- `data:` benchmark data or annotation update
- `docs:` documentation
- `chore:` repository maintenance

### 6. Synchronize before integration

Before merging, update against current `main`:

```bash
git fetch origin
git rebase origin/main
```

Resolve conflicts on the task branch, rerun validation, then push the branch.

### 7. Merge only reviewed, working changes to `main`

Preferred policy: branch -> review/diff -> merge -> delete branch.

After merge:

```bash
git switch main
git pull --ff-only origin main
```

## What must never happen

- editing directly on `main` for ordinary development;
- force-pushing `main`;
- committing `.env`, API keys, tokens or credentials;
- deciding the newest file by filename suffix such as `(1)`, `(final)`, `(new)`;
- maintaining a second unofficial “latest” project folder outside Git;
- replacing benchmark artifacts with regenerated approximations when the original experiment files exist elsewhere;
- silently changing frozen benchmark cases or canonical metrics.

## Version milestones

Use Git tags for stable checkpoints rather than copied folders or renamed ZIPs.

Suggested tags:

```text
v0.1-benchmark-baseline
v0.2-app-integrated
v0.3-validation-complete
v1.0-submission
```

Create a tag only after the corresponding state is actually present and reproducible in `main`.

## Daily rule

The answer to “which version is newest?” should always be:

```text
origin/main + its latest commit SHA
```

Everything else is a working copy.
