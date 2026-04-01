---
name: commit
description: >
  End-to-end workflow to commit changes, push the current branch, and open a GitHub draft PR
  with a CI-compliant title and filled PR template. Use when the user asks to commit, push,
  open a PR, ship changes, or prepare a draft for review.
---

# Commit, Push, and Draft PR

Use this when the user wants changes committed, pushed, and a **draft** pull request opened on GitHub.

**Prerequisites**

- `git` with a clean enough state to commit (resolve conflicts first).
- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated (`gh auth status`).
- Work on a **feature branch**, not `main` / default branch, unless the user explicitly asks otherwise.

---

## 1. Inspect and stage

- Run `git status` and `git diff` (and `git diff --staged` if anything is already staged).
- Stage only what belongs in this PR: `git add` with paths or `git add -p` for partial hunks.
- Do **not** commit secrets, `.env`, or unrelated files.

---

## 2. PR title (must pass CI)

The workflow [`.github/workflows/pr_title_check.yaml`](.github/workflows/pr_title_check.yaml) uses **semantic PR titles** ([Conventional Commits](https://www.conventionalcommits.org/) style).

**Allowed types** (exactly these):

`feat` · `fix` · `docs` · `test` · `build` · `ci` · `chore`

**Format**

```text
<type>(<optional-scope>): <subject>
```

- **Optional scope** in parentheses helps readers (e.g. `frontend`, `backend`, `django`, `ci`). Scopes are not validated by CI today; pick one when it clarifies the change.
- **Subject** must match `^[a-z].+$` — start with a **lowercase** letter, then at least one more character (no empty subject).

**Examples**

- `feat(frontend): add invoice generator wired to openapi types`
- `fix(backend): correct invoice reference query binding`
- `chore(deps): bump openapi-typescript in frontend`

Use the **same line** for:

1. The **last commit message** title (first line), and
2. The **GitHub PR title** (so local history matches the PR).

If there are multiple commits before push, either squash intent into one clear commit for small PRs or ensure the **PR title** still summarizes the whole change set.

---

## 3. Commit

- First line: semantic title (as above). Optional blank line, then body bullets for **why** / **notable details** if useful.
- Example:

```bash
git commit -m "feat(frontend): add invoice generator wired to openapi types" -m "- Align payloads with InvoiceServiceDefinitions
- Type create/pdf/reference responses from generated OpenAPI"
```

---

## 4. Push branch

```bash
git push -u origin HEAD
```

If the branch does not exist on the remote yet, `-u` sets upstream for later pushes.

---

## 5. PR body from the repo template

Read [`.github/pull_request_template.md`](.github/pull_request_template.md). The body must follow that structure:

- `## Description` — short summary (one short paragraph is enough).
- `### Added` — bullet list (or `- None`).
- `### Updated` — bullet list (or `- None`).
- `### Deleted` — bullet list (or `- None`).

**Constraints**

- **At most 3–4 bullets per section** (Added / Updated / Deleted). Combine related points if needed.
- Keep bullets **high level**; call out **important** behavior, contracts, migrations, breaking changes, or security-relevant edits.
- Omit noise (typos, trivial renames) unless they matter for review.

Write the body to a temp file and pass it to `gh` so formatting is preserved:

```bash
gh pr create --draft --title "feat(frontend): add invoice generator wired to openapi types" --body-file /path/to/pr-body.md
```

Alternatively build `--body` with a heredoc; avoid stripping markdown.

---

## 6. Open the draft PR

```bash
gh pr create --draft --title "<same as commit subject line>" --body-file pr-body.md
```

- Add `--base <branch>` if the default base is wrong.
- If `gh` prompts for title/body, supply the prepared title and body instead of improvised text.

**Result:** one draft PR, title CI-ready, description filled from the template with concise bullets.

---

## Quick checklist

| Step                                                                 | Done |
| -------------------------------------------------------------------- | ---- |
| Title uses allowed **type** and lowercase **subject**                |      |
| Same first line for commit (when single logical commit) and PR title |      |
| Template sections filled; **≤3–4 bullets** per Added/Updated/Deleted |      |
| `git push` succeeded                                                 |      |
| `gh pr create --draft` succeeded                                     |      |

---

## Troubleshooting

- **`gh: command not found`** — Install GitHub CLI; do not substitute a web-only flow unless the user prefers it.
- **PR title check fails after merge** — Rare; title is checked on open/edit. Fix title with `gh pr edit <n> --title "..."`.
- **Uncommitted work the user did not want included** — Unstage or stash before committing; never commit unrelated files to “save work.”
