---
title: Commands
description: Reference for all History Workbench commands.
---

| Command | Icon | Description |
|---------|------|-------------|
| Open History Panel | <img src="/HistoryWorkbench/icons/Logo.svg" width="32" alt="" /> | Open or focus the History panel. Use it to quickly switch to the history window if it has gone out of focus. |
| Refresh Project | <img src="/HistoryWorkbench/icons/RefreshRepository.svg" width="32" alt="" /> | Refresh the detected project and reload iterations. If an iteration is already selected, the tree comparison is refreshed. Use it when opening FreeCAD documents located within a project and after making any changes. |
| Recompute Active Document | <img src="/HistoryWorkbench/icons/RecomputeActiveDocument.svg" width="32" alt="" /> | Recompute the active document. Use it when you need to recompute only the currently active document. |
| Recompute All | <img src="/HistoryWorkbench/icons/RecomputeAll.svg" width="32" alt="" /> | Recompute every open document. Use it to ensure all document state is current before doing reviews. Useful for projects with many document inter-dependencies. |
| Open All Documents in Project | <img src="/HistoryWorkbench/icons/OpenAllDocuments.svg" width="32" alt="" /> | Open every `.FCStd` file found in the project. Useful for initializing a project. |
| Initialize Project | <img src="/HistoryWorkbench/icons/CreateGitRepository.svg" width="32" alt="" /> | Initialize a new project for the selected directory. Use it when setting up a new folder of CAD files for the first time. |
| Close Comparison Windows | <img src="/HistoryWorkbench/icons/DiffCloseDiffWindows.svg" width="32" alt="" /> | Close every document starting with `Diff_` without saving. Use it when you want to quickly clean up comparison windows after reviewing 3D diffs. |
| Save Iteration | <img src="/HistoryWorkbench/icons/Commit.svg" width="32" alt="" /> | Save reviewed changes as an iteration. Use it after reviewing and marking documents as reviewed to save the result. |
| Configure Author | <img src="/HistoryWorkbench/icons/ConfigureGit.svg" width="32" alt="" /> | Configure iteration author name and email. Visible in the menu only. |
| Edit Ignored Files | <img src="/HistoryWorkbench/icons/GitIgnore.svg" width="32" alt="" /> | Edit project's ignored files list (`.gitignore` content). Visible in the menu only. |
