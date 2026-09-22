# Changelog - MO2 Custom Filters

Versions are issued by the project's version gate. Written as the change happens (rule 61).

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
