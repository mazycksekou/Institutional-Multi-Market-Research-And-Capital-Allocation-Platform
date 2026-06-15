# Phase 10H23D – Feature Ablation Layout Density + Run Guards

## What changed

- **Active Fields** no longer dominates the page.  
  The giant tag stack is replaced by a compact count and two collapsed expanders (`View active fields` / `View removed fields`).  
  Field selection is now removal‑first: the operator chooses groups or individual fields to *remove*.

- **Field group controls** are grouped under `Field Groups` and `Remove Individual Fields`.  
  A helper label updates the counts of active/removed fields in real time.

- **SQLite database path** is moved from the main canvas to the sidebar under `Runtime Data Source`.  
  A file‑existence check runs immediately; a warning or success message is displayed.  
  The run button is disabled when the database is missing.

- **Rebuild Dataset** is moved to the sidebar under `Advanced Maintenance` with clear help text.  
  It is no longer a normal operator step.

- **Run guards** prevent calling the backend when:
  - the SQLite path does not exist,
  - no active fields remain,
  - no sport is selected (in single‑sport mode).  
  The button is disabled and a warning is shown.

- **Results stay prominent** after a run: the plain‑English verdict, Decisions, Net Result, ROI %, Win Rate %, Ready Status, Rows tested, Active Fields count, and Removed Fields count are always visible without scrolling.

- **No vendor/API/scraper connector** was added.  
- **Phase 10H24** remains blocked until UI review is complete.
