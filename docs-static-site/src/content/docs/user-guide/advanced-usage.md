---
title: Advanced Usage
description: Advanced Git workflows for History Workbench power users.
---

This section is for advanced users who want more control over project history. History Workbench uses Git for version control, so users familiar with Git can use regular Git tools alongside the workbench for workflows that are not implemented in the FreeCAD interface yet.

Advanced Git usage can help with tasks such as:

- Editing saved iteration messages (Git commit messages).
- Adding non-FreeCAD files to the **Reviewed** area (Git staging area) so they are saved with the same iteration, such as text documents, spreadsheets, CSV files, or reference data.
- Backing up a Project to a remote repository (Git remote), such as GitHub, GitLab, or a private Git server.
- Inspecting project history from external Git clients when you need lower-level version-control tools.

History Workbench still needs to be used to mark FreeCAD documents as **Reviewed** (staged). This step stores YAML snapshot files in the Project repository, which are needed to display the document tree.