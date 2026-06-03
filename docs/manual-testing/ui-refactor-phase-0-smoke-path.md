# UI Refactor Phase 0 Smoke Path

Use this smoke path before and after UI refactor slices to confirm no visible behavior drift.

## Preconditions

- Open FreeCAD with History workbench enabled.
- Load a git-backed project with at least one modified file.
- Keep one changed `Part::`, `PartDesign::`, or `Sketcher::SketchObject` node available for visual diff coverage.

## Smoke Steps

1. Open History workbench panel.
2. Click Refresh Project and Iterations.
3. Select `Current Files`.
4. Select `Reviewed`.
5. Select one commit entry.
6. In `Current Files`, click `+ Reviewed` for one document.
7. Click `+ Mark All Reviewed`.
8. Switch to `Reviewed`, click `Remove Reviewed` on one document.
9. Click `Remove All` in `Reviewed`.
10. From commit selection, trigger `Restore` and cancel dialog.
11. Click visual diff button for eligible node.
12. If open-document indicator appears, click it to open document.
13. Click `Save Iteration` and cancel dialog.
14. Trigger `Configure Author` flow and cancel dialog.

## Expected Result

- All actions respond.
- Cancel flows leave data unchanged.
- Selection switches remain stable.
- Summary/action buttons match selected mode (`Current Files`, `Reviewed`, commit).
- Visual diff and open-document indicator actions fire without UI errors.
