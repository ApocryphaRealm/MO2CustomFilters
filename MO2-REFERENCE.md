# MO2 reference - how Mod Organizer 2 itself does what this plugin touches

The owner, 2026-09-23: *"why doesn't MO2's filter crash? we should learn from MO2's implementation"* and *"add a gate for
future MO2 plugins to always compare how MO2 implements a function before trying to add onto it or alter it."* This file
is that comparison for MO2 Custom Filters; gate rule `mo2-plugin-documents-mo2s-own-implementation` requires one in
every MO2 plugin repo of ours, citing MO2's source at the release tag.

MO2 version: **2.5.2** (revision 9c130cbf). Sources read on 2026-09-23:

- https://github.com/ModOrganizer2/modorganizer/blob/v2.5.2/src/filterlist.cpp
- https://github.com/ModOrganizer2/modorganizer/blob/v2.5.2/src/modlistsortproxy.cpp
- https://github.com/ModOrganizer2/modorganizer/blob/v2.5.2/src/modlistview.cpp

## What MO2 does

| Feature | MO2's implementation | Where |
|---|---|---|
| The filter pane | `FilterList` owns the `QTreeWidget` (`ui->filters`). `refresh()` calls `ui->filters->clear()` and re-adds every item: the special filters (Checked, Update available, Backup, Managed, Has category, Conflict, Has hidden files, Endorsed, Tracked, Has Nexus ID, Has game data), the content filters (`addContentCriteria`, one per `ModDataContent`), then the categories (`addCategoryCriteria`, recursive). It never counts mods per filter. | `filterlist.cpp` |
| When the pane is rebuilt | `refresh()` is not driven by a model signal. `ModListView::refreshFilters()` calls it as a plain function: it saves the selection, calls `m_filters->refresh()`, restores the selection. | `modlistview.cpp` |
| How a ticked filter reaches the list | `FilterList::cycleItem` -> `checkCriteria` -> `emit criteriaChanged(selectedCriteria())`; `ModListView` connects that to `setFilterCriteria`, which is `m_sortProxy->setCriteria(criteria)`. And/Or and the separators mode go the same way through `optionsChanged` -> `setOptions`. | `filterlist.cpp`, `modlistview.cpp` |
| How rows are hidden | Never by the view. `ModListSortProxy::filterAcceptsRow` decides; a row with children (a separator, a group) is shown when it matches itself or any child does. `setCriteria`, `updateFilter` (the search box) and `setOptions` each call `invalidateFilter()` and emit `filterInvalidated` and `filterActive`. | `modlistsortproxy.cpp` |
| The view's model | Set once in `setup()`: `m_sortProxy = new ModListSortProxy(...)`; `setModel(m_sortProxy)`. The proxy's source model changes; the view's model does not. `modelReset` on the proxy -> `refreshExpandedItems()`. | `modlistview.cpp` |

What MO2 never does: it never hands a foreign callback a model signal to run inside its own mutation, and nothing
outside MO2 runs during `FilterList::refresh()` or a proxy invalidation.

## What this plugin does, and where it follows MO2

| Our feature | Our implementation (1.0.5) | Follows MO2 how |
|---|---|---|
| Two extra tabs (Separators, Keywords) beside MO2's pane | Our own `QTreeWidget`s in our own `QTabWidget`; MO2's `categoriesGroup` moved into tab 1 untouched. | We own what we draw, as `FilterList` owns its tree. |
| Narrowing the mod list by our ticks | `QTreeView.setRowHidden` on MO2's view, on top of what MO2's proxy already shows; re-applied whenever the view changes. | We cannot add criteria to `ModListSortProxy` (C++, not exposed to plugins), so we hide rows in the view instead - the one place we depart from MO2, and the reason we must re-apply after every proxy invalidation. |
| Knowing when to re-apply or recount | A Python-owned `QTimer` polls a cheap signature every 1.5 s (the view's model identity, row count, first and last names; `modlist.txt` and the mods folder's mtimes; the filter tree's item count; whether our counts are on it) and starts the work once it has held still for a tick. User clicks on MO2's filter tree, column headers, search box, And/Or and Clear re-apply at once. | MO2 rebuilds and invalidates from plain calls on its own stack; we do the same from our own timer, and take only the user-driven widget signals MO2's own widgets emit on a click. No model signals, no `onNextRefresh`, no mobase callbacks (each of those had MO2 invoking a Python slot mid-mutation; three crashes, one fault signature). |
| Counts on MO2's own filters | `_count_mo2_filters` re-fetches every item by index (`topLevelItem(i)`), writes the count into its text and a base-label role, and skips an empty tree. | `refresh()` deletes every item (`clear()`), so nothing may hold an item across a refresh; the poll's "counts on it" check re-puts them after MO2's clear. |
| The per-filter tallies | Computed the way `ModListSortProxy::categoryMatchesMod` / `contentMatchesMod` decide them: state flags, categories, content ids; conflict and hidden flags read from the mod list's own Conflicts / Flags tooltips. | Same predicates as MO2's proxy, so a count equals what ticking that filter shows. |

## Open departures to revisit

- Hiding rows in the view rather than filtering in the proxy: correct only after a re-apply; a future MO2 that exposes
  criteria to plugins (or a proxy hook) would remove the poll's re-apply path entirely.
- Reading conflict / hidden flags through tooltips is MO2's presentation, not its API; if `IModInterface` ever exposes
  the flags, use them.
