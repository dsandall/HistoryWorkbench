---
title: FAQ
description: Frequently asked questions about History Workbench.
---

### The tree comparison doesn't show any changes, but the Reviewed button is enabled. Why?

No object or property changes were detected, but the FreeCAD document changed on disk. This can happen when the document was saved without model changes, view properties or internal cache data changed, or parametric changes occurred that History Workbench does not detect yet.

Some of these scenarios are legitimate project changes and should be tracked like any other change. If you find a parametric model change that is not shown in the tree comparison, please open an issue with a sample file when possible.