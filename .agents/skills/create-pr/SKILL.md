---
name: create-pr
description: Commit changes, push the branch, and open a draft PR with a semantic title and filled-out template.
user_invocable: true
---

## When to use this skill

Use this skill when the user wants to commit, push, and open a pull request in one step.

## Workflow

### Step 1: Inspect changes

Run these commands in parallel to understand what's being committed:

```bash
git status
git diff --staged
git diff
git log --oneline -5
```

### Step 2: Stage and commit

- Stage all relevant changed files (avoid secrets, `.env`, large binaries).
- Write a commit message that summarizes the changes concisely.
- End the commit message with: `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`

### Step 3: Push the branch

```bash
git push -u origin HEAD
```

If the branch doesn't have an upstream yet, `-u` sets it.

### Step 4: Open a draft PR

Create the PR using `gh pr create`. The title and body MUST follow the project conventions below.

#### PR Title Convention

The title MUST match the semantic PR title format enforced by `.github/workflows/pr_title_check.yaml`:

```
type(scope): lowercase description
```

**Allowed types:** `feat`, `fix`, `docs`, `test`, `build`, `ci`, `chore`

**Scope** is optional but recommended. Use the service or area name: `backend`, `frontend`, `analyzer`, `dagster`, `dbt`, `tilt`, `infra`, etc.

**Subject** must start with a lowercase letter.

Examples:

- `feat(backend): add user timezone endpoint`
- `fix(frontend): correct trace propagation in server actions`
- `chore(backend): clean up dead code and improve linting`

#### PR Body Convention

Follow the template from `.github/pull_request_template.md`. Keep it brief — a short description (1-3 sentences) and 3-5 bullet points max per section. Omit sections that don't apply.

```
## Description

Brief explanation of what this PR does and why.

### Added

- Item (only if something new was added)

### Updated

- Item (only if something existing was changed)

### Deleted

- Item (only if something was removed)
```

#### Command

```bash
gh pr create --draft --title "type(scope): description" --body "$(cat <<'EOF'
## Description

Brief explanation.

### Added

- None

### Updated

- Item

### Deleted

- None
EOF
)"
```

### Step 5: Return the PR URL

Print the PR URL so the user can open it.
