# MO2 Custom Filters

A Mod Organizer 2 plugin that adds two tabs to the filter pane beside MO2's own filters - **Separators**
and **Keywords** - puts a search box on each, and shows on every filter, MO2's own included, how many
mods it holds.

## What it does

* **Separators tab.** Every separator in the profile, in list order, with the number of mods under it.
  Tick one to show only its mods; tick again to invert (everything *but* those mods); a third click
  clears it. Any number can be ticked, and MO2's own **And / Or** switch decides how they combine.
* **Keywords tab.** Every `[Tag]` found in a mod name, plus any keyword you add. Same three-state ticks.
  Right-click empty space to **add** a keyword; right-click one you made to **edit** or **remove** it.
  `[NoDelete]` is the one keyword shipped by default. Leading words (a mod name that *starts* with
  "test", say) can be made keywords too, through the plugin's settings.
* **Search boxes.** Each tab has one at the bottom, beside its Clear button, that narrows the entries
  shown on that tab - handy in a list with a hundred separators.
* **Counts on MO2's own filters.** `<Active>`, `<Conflicted>`, `<Contains Plugins>`, every category and
  the rest get a `(count)` too, worked out the way MO2 decides membership and refreshed when mods
  change.
* **Plays by MO2's rules.** Our ticks sit on top of whatever MO2's own filters and search box already
  show. MO2's Clear buttons clear ours as well. The ticks use MO2's own three filter-state pictures, so
  they match whichever theme you run. Nothing is written anywhere except the plugin's own two settings.

## Requirements

Mod Organizer 2 **2.5.x** (tested on 2.5.2). It has a PyQt5 fallback for 2.4 but has not been tried
there. No game, no other plugin.

## Installation

Copy `plugins\MO2CustomFilters.py` into your MO2 instance's `plugins` folder (next to the other
`.py` plugins) and restart MO2. The Separators and Keywords tabs appear in the Filters pane.

To remove it, delete the file. It leaves nothing behind but its two settings and a small log.

## Settings

Under **Settings > Plugins > MO2 Custom Filters**, or from the Keywords tab's right-click menu:

| Setting | Default | Meaning |
|---|---|---|
| `keywords` | `[NoDelete]` | Your keywords, comma-separated. Matched anywhere in a mod name as a whole word, any case. |
| `keyword_prefixes` | *(none)* | Leading words that count as keywords - a mod named `test Something` gets the keyword `test`. |

## Debugging

`<instance>\plugins\data\mo2-custom-filters.log` records what the plugin did (tabs added, ticks,
counts, anything it could not do). Send it with any bug report.

## How the counts are made

* **Separators / Keywords:** the number of mods MO2's own filters and search currently leave visible,
  so the count tells you what ticking the entry would show. An entry with none is greyed.
* **MO2's filters:** a tally over the whole profile, computed the way `ModListSortProxy` decides each
  criterion - enabled state, categories, Nexus ID, endorsed / tracked, backup / foreign, contents
  from the game plugin's content feature, and the conflict and hidden-file flags read from the mod
  list's own Conflicts and Flags columns. MO2 works those two out a few seconds after start-up, and
  the counts refresh when it does.

## Licence

GPL-3.0-or-later. Copyright (C) 2026 ApocryphaRealm. See `LICENSE` and `NOTICE.md`.
