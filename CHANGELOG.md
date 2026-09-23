# Changelog - MO2 Custom Filters

Versions are issued by the project's version gate. Written as the change happens (rule 61).

## 1.0.5 - 2026-09-23

* Fixes MO2 closing when a mod is enabled or disabled, on a rename, and once with nobody touching it (three minutes
  after start, when MO2's directory refresh finished and it rebuilt its filter list). Every one of those crashes
  left the same fault signature: the main thread inside one of the plugin's slots with no line number, which is a
  slot being invoked from MO2's own signal mid-mutation, not anything the slot did. Two earlier issues of 1.0.5
  (callbacks that only started timers; timers Python-owned and guarded) each answered a narrower hypothesis and
  each still crashed. The plugin now takes nothing from MO2's internals: no model signals (dataChanged,
  rowsInserted, modelReset, layoutChanged), no hook on MO2's filter tree, no mobase callbacks, no onNextRefresh
  callback. A timer the plugin owns polls a cheap signature of the mod list and the filter tree every 1.5 s
  (modlist.txt and the mods folder's times, the view's row count and end names, the filter tree's item count and
  whether the counts are on it) and starts the work once it has held still for a full tick. Only user-driven
  widget signals remain - clicks on the plugin's own lists, MO2's search box, And/Or, Clear, its filter tree and
  the column headers - so a click still re-applies the filters within a third of a second; a refresh or an
  install is picked up by the next poll. Modelled on how MO2 itself does it: its filter list is rebuilt with a
  plain clear-and-refill and its filtering is a proxy invalidation, and nothing outside MO2 is called during either.

## 1.0.4 - 2026-09-23

* Fixes MO2 closing when a mod or separator is renamed. The filter recount asked MO2's content feature to walk
  each mod's file tree, and the tree of a just-renamed mod is not safe to walk - MO2 died with an access violation
  (found by the new fault log). The content kinds (Plugins, Textures, Meshes, Scripts, SKSE, BSA, Interface, Sound,
  INI, MCM...) are now read off the top level of the mod folder and mapped to MO2's own content ids, so nothing per
  mod touches MO2 beyond its path.
* Recounts triggered by the mod list's model wait until MO2 has finished any refresh in flight
  (`IOrganizer.onNextRefresh`), and the settle timer is 300 ms instead of 50.
* Arms Python's faulthandler on import (shared `plugins\data\faults.log`), the standing rule for every MO2 plugin of
  ours: a native crash names the plugin and line instead of leaving only a minidump.

## 1.0.3 - 2026-09-22

* Ticking a separator now shows the mods under it in every list layout. A row with children - a separator when MO2's
  collapsible separators are on, or a group row when the list is grouped by category, Nexus ID or priority - was
  treated as though it were a mod, so it and everything beneath it were hidden. Containers are now shown when
  anything under them matches, and opened so their mods are in view. Reported by ProteusBlack on the mod page.

## 1.0.2 - 2026-09-22

* The Separators and Keywords tabs are rebuilt on every MO2 refresh, so a renamed mod (MO2 Patch Tagger's
  `[Patch]` prefix, a rename you make yourself followed by a refresh) shows up without a restart.

## 1.0.1 - 2026-09-22

* MO2's own Filters tab gets a search box too, in the bottom row where the "Filter separators" dropdown
  was; the dropdown keeps its three modes and moves up beside Clear and Edit... (the owner: "can you
  make that dropdown a searchbar then to match the other 2 tabs").

## 1.0.0 - 2026-09-22 - first release (not published; superseded the same day by 1.0.1)

* Two tabs beside MO2's own filters: **Separators** (every separator in list order) and **Keywords**
  (every `[Tag]` in a mod name, the leading words you configure, and any keyword you add).
* Three-state ticks like MO2's - include, invert, off - on any number of entries, combined by MO2's own
  And / Or, on top of MO2's own filters and search; MO2's Clear buttons clear them too.
* Ticks drawn with MO2's own three filter-state pictures, so they match the running theme.
* A count on every entry: for our tabs, what MO2's filters and search currently leave visible; for
  MO2's own filters, a tally of the whole profile made the way MO2 decides each criterion (conflict
  and hidden-file flags read from the mod list's own columns once MO2 has computed them).
* A search box on each of our tabs, beside its Clear button.
* Keywords managed from the Keywords tab's right-click menu: add on empty space, edit / remove on a
  keyword you made. `[NoDelete]` is the one keyword shipped by default; no leading words by default.
* Nothing written anywhere but the plugin's two settings and its log
  (`plugins\data\mo2-custom-filters.log`).

### Development history before 1.0.0 (as "Separator Filters", 2026-09-20 to 2026-09-22)

* 1.x stamped separators into MO2's category list (`categories.dat`) - withdrawn; it cluttered MO2's
  own filters with over a hundred entries.
* 2.0 moved to tabs in the filter pane and view-side row hiding. 2.1 three-state ticks, And / Or,
  Clear hooks, counts. 2.2 no toolbar button or popup; right-click keyword menu. 2.3 - 2.4 MO2's own
  tick pictures. 2.5 counts on MO2's own filters. 2.6 search boxes. Renamed MO2 Custom Filters.
