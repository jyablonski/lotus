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

Follow the template from `.github/pull_request_template.md`. **Brevity is critical:**

- **Description**: 1-2 sentences max. State what changed and why at a high level — do not enumerate individual files, functions, or implementation details.
- **Added/Updated/Deleted**: 3-5 bullet points max **total across all sections**. Each bullet should be a short, high-level summary (e.g. "bcrypt password hashing" not "replaced SHA-256 HashPassword with bcrypt.GenerateFromPassword in utils.go"). Omit sections that don't apply — do not include a section just to write "None".

The reviewer can read the diff for details. The PR body should only convey **what** and **why**, never **how**.

```
## Description

One-two sentence high-level summary.

### Updated

- Short bullet
- Short bullet
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
