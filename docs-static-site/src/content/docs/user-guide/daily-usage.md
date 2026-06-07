---
title: Daily Usage
description: How to use History Workbench in your daily CAD workflow.
---

Use History Workbench as a review loop after normal CAD work.

1. **Work in FreeCAD as usual:** Model, recompute, save, and edit your project files normally. Recompute your document(s) and ensure there are no errors.
2. **Refresh the project:** In the History workbench, click <img src="/HistoryWorkbench/icons/RefreshRepository.svg" width="16" alt="" class="command-icon" /> **Refresh Project** so the history list and document status reflect the latest files.
3. **Review file changes:** Click the **Current Files** iteration item in the list. The document tree shows added, removed, and modified objects since the last reviewed state.
4. **Inspect detailed properties:** Click a changed object in the model tree. The property panel shows changed dimensions, placements, expressions, constraints, quantities, links, and other editable properties.
5. **Open 3D comparisons:** For changed Part, PartDesign, or Sketcher objects, click <img src="/HistoryWorkbench/icons/VisualDiff.svg" width="16" alt="" class="command-icon" /> **3D Comparison** next to the object to open a separate comparison document. Removed material is shown in red, added material in green, and unchanged material in gray. You may use FreeCAD's unified measurement tool to measure changes.
6. **Mark documents reviewed:** Click the **Reviewed** button on individual documents when they are ready, or click **Mark All Reviewed** after reviewing all of them. This essentially creates a copy of the files and places them into the Reviewed Area.
7. **Keep working if needed:** Return to the CAD model and make more edits, if needed. The next **Current Files** comparison is made against the documents you already marked as reviewed, making it easy to incrementally make changes.
8. **Verify reviewed work:** Click the **Reviewed** iteration item in the history list to confirm exactly what will be saved in the next iteration.
9. **Save an iteration:** Click <img src="/HistoryWorkbench/icons/Commit.svg" width="16" alt="" class="command-icon" /> **Save Iteration**, enter a description of the changes, and confirm.

> [!NOTE]
> Tree comparisons focus on structured FreeCAD object and property data, but may not capture every CAD model change yet. Use 3D comparisons as an additional review step before saving an iteration.

## Restoring Files from Reviewed or Saved Iterations

Use restore when you want to bring one file, or many files, back to a prior saved state on disk.

1. Select **Reviewed** or a specific saved iteration in the history list.
2. Restore one file with the per-file **Restore** button, or restore many files with **Restore All**.
3. For **Restore All**, choose a scope:
   - **Listed FreeCAD files:** Restore only the FreeCAD files changed in the selected iteration.
   - **All FreeCAD files:** Restore all previously saved FreeCAD files to how they were in this iteration. Any previously saved FreeCAD files that did not exist in that iteration are removed. New files not yet saved to history are kept.
4. Confirm the warning dialog.

Restore behavior:

- Restore changes current files on disk only; saved iteration history is unchanged.
- All project documents currently open in FreeCAD are closed before restore and reopened after restore.
- Unsaved in-memory changes in those project documents are lost. **Save all documents before running this operation.**
- New FreeCAD files not yet saved in history are left unchanged during **All FreeCAD files** restore.

> [!WARNING]
> **The file restore process closes (without saving) ALL open FreeCAD files, including those not selected for restoration!** This is because any links to the restored files, such as subshape binders, expressions, etc, are not updated if the files are open, and may cause unintended consequences. Closing all files is a safety precaution, but it is imperative that you save your work first.
