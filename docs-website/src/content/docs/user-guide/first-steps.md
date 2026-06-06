---
title: First Steps
description: Actionable steps to get started with the History Workbench
---

Before initializing a project, it's recommended to turn off file compression. FreeCAD documents are binary files by default, which means small model edits can produce large file changes. Turning off file compression results in larger files on disk, but smaller overall disk usage when saving iterations over time, as only the differences between files need to be stored each time.

To disable document compression:

1. In FreeCAD, open **Edit > Preferences > General > Document**.
2. Set **Document save compression level** to `0`.
3. Click "OK".

## Initializing Your Project

To initialize your project, jump to the section relevant to you:

- [Blank Project](#blank-project) — starting from scratch with no existing models
- [Existing Project](#existing-project) — adding history tracking to an existing project
- [Existing Git Project](#existing-git-project) — for projects already using git

### Blank Project

Follow these steps if you haven't started modeling your parts yet.

#### 1. Create a FreeCAD document

In FreeCAD, create a blank document and save it in the folder you want to use as the base of your project. The folder and all of its sub-folders will be set up to be tracked using this procedure.

Example location: `C:\Users\JohnDoe\Documents\FreeCAD\MyProject\

#### 2. Initialize Project Command

Click <img src="/freecad/history_wb/resources/icons/CreateGitRepository.svg" width="16" alt="" /> **Initialize Project** in the History Workbench, select the folder that contains your document, and press "Initialize".

That's it -- you are now ready to start tracking your model history.

### Existing Project

Existing projects need to have snapshots generated for all FreeCAD files, to be able to start using the comparison functionality.

#### 1. Open a FreeCAD document

Start FreeCAD and open any document from the folder you want to use as the root of your Project.

#### 2. Initialize Project command

Click <img src="freecad/history_wb/resources/icons/CreateGitRepository.svg" width="16" alt="" /> **Initialize Project** in the History Workbench, select the folder that contains your project files, and click "Initialize".

#### 3. Open All Project Documents

Click <img src="freecad/history_wb/resources/icons/OpenAllDocuments.svg" width="16" alt="" /> **Open All Documents** to open all FreeCAD documents in the project folder.

#### 4. Recompute All Documents

Click <img src="freecad/history_wb/resources/icons/RecomputeAll.svg" width="16" alt="" /> **Recompute All** to make sure document state is current. Ensure there aren't recomputation errors. If there are, it is advisable to fix them, otherwise the base snapshot(s) will have incomplete data stored.

#### 5. Create the First Iteration

Select **Current Files** in the iteration list, then click **Mark All Reviewed**. This prepares both the documents and their snapshots.

Finally, use the <img src="freecad/history_wb/resources/icons/Commit.svg" width="16" alt="" /> **Save Iteration** command to write an initial message like "My first iteration", and press Save.

Now you are ready to work on your project.

### Existing Git Project

If you already use git in your project and want to start using the workbench, you need to create a baseline commit that contains all the snapshots for your FreeCAD documents. Simply follow the steps from "Existing Project" above, starting at step 3.
