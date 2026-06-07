---
title: In-Depth Document Diff And Staging Testing
description: In-depth manual test plan for document diff behavior across working tree, staging, and commit modes with a reusable git repository.
---
This plan creates one reusable git repository that exercises document diff behavior across working tree, staging, and commit modes, plus staging behavior for snapshots and deleted files. The flow is designed so one repository can be kept and reused for regression checks after code changes.

It includes testing snapshot error scenarios, such as snapshot missing or corrupted, and how diffs behave in each.

## Goal

Create one repository with these document scenarios:

| File | Scenario |
|---|---|
| `clean_open.FCStd` | open, unchanged |
| `modified_parametric.FCStd` | real parametric diff |
| `modified_binary_only.FCStd` | git changed, no parametric diff |
| `deleted.FCStd` | deleted document |
| `added.FCStd` | new document |
| `missing_old_snapshot.FCStd` | old YAML missing |
| `missing_new_snapshot.FCStd` | new YAML missing |
| `invalid_old_snapshot.FCStd` | old YAML invalid |
| `invalid_new_snapshot.FCStd` | new YAML invalid |

Expected mode coverage:

- Working tree mode: dirty files plus open eligible docs.
- Staging mode: staged files only.
- Commit mode: files changed in selected commit.

## Phase 0 - Create Manual Test Repo

1. Create repository:

```bash
mkdir ~/fc-history-manual-test
cd ~/fc-history-manual-test
git init
```

2. Open FreeCAD with History workbench enabled.

3. Create these documents in repo root:

```text
clean_open.FCStd
modified_parametric.FCStd
modified_binary_only.FCStd
deleted.FCStd
missing_old_snapshot.FCStd
missing_new_snapshot.FCStd
invalid_old_snapshot.FCStd
invalid_new_snapshot.FCStd
```

4. Recommended contents:

- each file should have drastically different model contents, dimensions, and object names from the others
- avoid creating near-duplicates, because when `deleted.FCStd` is removed and `added.FCStd` is introduced, git may detect a rename instead of separate delete and add events
- `modified_parametric.FCStd` uses an obvious dimension such as Box Length `10 mm`
- save all files

1. In History workbench, run Stage Documents for all open docs.

Expected:

- `.history_snapshots/.../*.yaml` files created
- FCStd files staged
- YAML snapshot files staged

6. Before committing, remove baseline YAML for `missing_old_snapshot.FCStd` from index and disk:

```bash
git restore --staged .history_snapshots/missing_old_snapshot.yaml
rm .history_snapshots/missing_old_snapshot.yaml
```

Use actual generated YAML path if different.

7. Corrupt baseline YAML for `invalid_old_snapshot.FCStd`:

```bash
printf 'not: [valid\n' > .history_snapshots/invalid_old_snapshot.yaml
git add .history_snapshots/invalid_old_snapshot.yaml
```

8. Commit baseline:

```bash
git add .
git commit -m "baseline manual history test repo"
```

Expected baseline state:

- all FCStd committed
- most YAML committed
- `missing_old_snapshot.FCStd` has no committed YAML
- `invalid_old_snapshot.FCStd` has invalid committed YAML

## Phase 1 - Create Working Tree Changes

In FreeCAD:

1. Keep or open `clean_open.FCStd`. Do not change it.
2. Open `modified_parametric.FCStd`. Change real model parameter, for example Box Length `10 -> 20`. Save.
3. Open `modified_binary_only.FCStd`. Save without semantic model changes.
4. If git does not mark it dirty, change view-only or non-parametric metadata if possible, then save again.
5. Create `added.FCStd`. Add simple object that is clearly different from `deleted.FCStd`. Save.
6. Delete `deleted.FCStd` from disk:

```bash
rm deleted.FCStd
```

7. Open and modify `missing_old_snapshot.FCStd` with real parametric change. Save.
8. Open and modify `missing_new_snapshot.FCStd` with real parametric change. Save.
9. Open and modify `invalid_old_snapshot.FCStd` with real parametric change. Save.
10. Open and modify `invalid_new_snapshot.FCStd` with real parametric change. Save.

Do not stage yet.

## Phase 2 - Test Working Tree Mode Before Staging

Open diff UI in Working Tree mode.

Expected rows:

| File | Expected document state | Expected issues |
|---|---|---|
| `clean_open.FCStd` | `UNCHANGED` | none |
| `modified_parametric.FCStd` | `MODIFIED` | none, tree diff visible |
| `modified_binary_only.FCStd` | `MODIFIED` | `GIT_CHANGED_NO_PARAMETRIC_DIFF`, empty or no tree changes |
| `deleted.FCStd` | `DELETED` | none if old snapshot valid, deleted tree diff visible |
| `added.FCStd` | `ADDED` | none, full-tree added diff |
| `missing_old_snapshot.FCStd` | `MODIFIED` | old snapshot `MISSING`, full-tree added diff from empty baseline |
| `missing_new_snapshot.FCStd` | `MODIFIED` | none yet, because working snapshot exists |
| `invalid_old_snapshot.FCStd` | `MODIFIED` or issue-only | old snapshot `INVALID`, likely no tree diff |
| `invalid_new_snapshot.FCStd` | `MODIFIED` | none yet, because working snapshot exists |

Also verify:

- deleted open document warning if `deleted.FCStd` is still open
- deletion wins over open document state
- no working snapshot created for deleted path
- state remains `DELETED`

## Phase 3 - Test Stage Documents

Use History workbench Stage Documents.

Select:

- `modified_parametric.FCStd`
- `modified_binary_only.FCStd`
- `added.FCStd`
- `missing_old_snapshot.FCStd`
- `missing_new_snapshot.FCStd`
- `invalid_old_snapshot.FCStd`
- `invalid_new_snapshot.FCStd`
- deleted path `deleted.FCStd`

Expected:

- open docs saved before staging
- YAML snapshots written for selected snapshots
- FCStd and YAML staged
- deleted FCStd staged
- deleted YAML removed from disk and staged if tracked
- duplicate paths not staged twice
- deleted open doc not saved or resurrected

Check:

```bash
git status --short
```

Expected examples:

```text
M  modified_parametric.FCStd
M  .history_snapshots/modified_parametric.yaml

M  modified_binary_only.FCStd
M  .history_snapshots/modified_binary_only.yaml

D  deleted.FCStd
D  .history_snapshots/deleted.yaml

A  added.FCStd
A  .history_snapshots/added.yaml
```

Exact YAML paths may differ.

## Phase 4 - Create Staged Snapshot Issue Cases

Before testing Staging mode, break staged content manually.

### Case A - Missing New Snapshot

Remove staged YAML for `missing_new_snapshot.FCStd`:

```bash
git restore --staged .history_snapshots/missing_new_snapshot.yaml
rm .history_snapshots/missing_new_snapshot.yaml
```

Keep FCStd staged:

```bash
git add missing_new_snapshot.FCStd
```

Expected later:

- new snapshot `MISSING`
- no tree diff for modified file because new snapshot absent

### Case B - Invalid New Snapshot

Corrupt and stage YAML for `invalid_new_snapshot.FCStd`:

```bash
printf 'not: [valid\n' > .history_snapshots/invalid_new_snapshot.yaml
git add .history_snapshots/invalid_new_snapshot.yaml
```

Expected later:

- new snapshot `INVALID`
- no valid tree diff

## Phase 5 - Test Staging Mode

Open diff UI in Staging mode.

Expected rows include only staged changed files:

| File | Expected state | Expected issues |
|---|---|---|
| `modified_parametric.FCStd` | `MODIFIED` | none |
| `modified_binary_only.FCStd` | `MODIFIED` | `GIT_CHANGED_NO_PARAMETRIC_DIFF` if snapshot unchanged |
| `deleted.FCStd` | `DELETED` | none if old snapshot existed |
| `added.FCStd` | `ADDED` | none |
| `missing_old_snapshot.FCStd` | `MODIFIED` | old snapshot `MISSING`, full-tree added diff |
| `missing_new_snapshot.FCStd` | `MODIFIED` | new snapshot `MISSING`, no tree diff |
| `invalid_old_snapshot.FCStd` | `MODIFIED` | old snapshot `INVALID`, no or issue-only diff |
| `invalid_new_snapshot.FCStd` | `MODIFIED` | new snapshot `INVALID`, no or issue-only diff |

Verify not shown:

- `clean_open.FCStd`, unless staged or dirty

## Phase 6 - Commit All Staged Changes

Commit staged state:

```bash
git commit -m "manual diff matrix commit"
```

Save commit hash:

```bash
git rev-parse HEAD
```

## Phase 7 - Test Commit Mode

In UI, select commit `manual diff matrix commit`.

Expected same as Staging mode:

| File | Expected state | Expected issues |
|---|---|---|
| `modified_parametric.FCStd` | `MODIFIED` | none |
| `modified_binary_only.FCStd` | `MODIFIED` | `GIT_CHANGED_NO_PARAMETRIC_DIFF` if snapshots same |
| `deleted.FCStd` | `DELETED` | none |
| `added.FCStd` | `ADDED` | none |
| `missing_old_snapshot.FCStd` | `MODIFIED` | old snapshot `MISSING` |
| `missing_new_snapshot.FCStd` | `MODIFIED` | new snapshot `MISSING` |
| `invalid_old_snapshot.FCStd` | `MODIFIED` | old snapshot `INVALID` |
| `invalid_new_snapshot.FCStd` | `MODIFIED` | new snapshot `INVALID` |

Important commit-mode checks:

- results sorted by git path
- only files from selected commit appear
- deleted file loads old snapshot from parent commit
- added file uses empty old snapshot
- missing or invalid snapshots surface as side issues

## Phase 8 - Test Restore Feature Reuse

Use Restore to reset files back to baseline or selected commit.

Recommended fast loops:

1. Restore `modified_parametric.FCStd` to baseline. Working Tree mode should stop showing parametric diff after save and stage cleanup.
2. Restore `deleted.FCStd` from baseline. Working Tree mode should change from `DELETED` to clean or unchanged if open.
3. Restore `added.FCStd` by removing it or restoring repo to baseline. Working Tree mode should remove added row.
4. Restore `missing_new_snapshot.FCStd`, then stage normally through workbench. Staging and commit mode should lose `new snapshot MISSING`.
5. Restore `invalid_new_snapshot.FCStd`, then regenerate and stage YAML. Staging and commit mode should lose `new snapshot INVALID`.

Useful reset command when returning to clean baseline:

```bash
git restore --source HEAD~1 --worktree --staged .
git clean -fd
```

Do not run this if preserving later commits matters.

## Extra Failure Checks

### Stage Conflict Rejection

Call Stage Documents with same path in snapshot inputs and deleted path inputs.

Expected:

- failure result
- message like `Cannot stage paths as both present and deleted`
- no git staging after conflict

Manual path:

- keep one document open
- also mark same path as deleted in UI or action if UI allows it

### Save Failure

Make document read-only or simulate FreeCAD save failure.

Expected:

- Stage Documents returns failure
- no later YAML write or git staging for that document

### Deleted YAML Tracked Check

For deleted file with tracked YAML:

- YAML removed from disk
- YAML deletion staged

For deleted file with no tracked YAML:

- no git pathspec error
- only FCStd deletion staged

## Reusable Repo Result

Keep repository as fixture with these commits:

```text
commit 1: baseline manual history test repo
commit 2: manual diff matrix commit
```

Use:

- baseline commit for restore tests
- matrix commit for Commit mode regression checks
- working tree edits on top for Working Tree and Staging mode regression checks
