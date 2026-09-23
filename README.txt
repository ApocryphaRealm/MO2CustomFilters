MO2 Custom Filters
==================
Version 1.0.5

A Mod Organizer 2 plugin. Adds two tabs beside MO2's own filters - Separators and Keywords - with a
search box on each, and shows on every filter, MO2's own included, how many mods it holds.

THIS IS NOT A MOD. Do not install it with the mod manager.

REQUIREMENTS
------------
Mod Organizer 2 2.5.x (tested on 2.5.2).

INSTALLATION
------------
Copy plugins\MO2CustomFilters.py into your MO2 folder's "plugins" folder, next to the other .py
plugins, and restart MO2. The Separators and Keywords tabs appear in the Filters pane on the left.
To remove it, delete the file.

USE
---
- Tick a separator or keyword to show only its mods. Tick again to invert (everything but those).
  A third click clears it. Tick as many as you like; MO2's And / Or switch decides how they combine.
- Each tab has a search box at the bottom that narrows its entries, and a Clear button that unticks
  them. MO2's own Clear buttons clear them too.
- Keywords: right-click empty space on the Keywords tab to add a keyword; right-click one you made
  to edit or remove it. [NoDelete] is the one shipped by default. Every [Tag] in a mod name is
  listed automatically.
- Every entry shows a count. On the two new tabs it is what MO2's filters and search currently
  leave visible; on MO2's own filters it is a tally of the whole profile.

SETTINGS
--------
Settings > Plugins > MO2 Custom Filters:
  keywords          ([NoDelete])   your keywords, comma-separated, matched anywhere in a mod name
  keyword_prefixes  (empty)        leading words that count as keywords, e.g. "test"

DEBUGGING
---------
<your MO2 folder>\plugins\data\mo2-custom-filters.log - send it with any bug report.

LICENCE
-------
GPL-3.0-or-later. Copyright (C) 2026 ApocryphaRealm. See LICENSE and NOTICE.md.
Source: https://github.com/ApocryphaRealm/MO2CustomFilters
