# MO2 Custom Filters - a Mod Organizer 2 plugin that adds two tabs to the FILTER pane on the left of the mod list:
# "Separators" (tick a separator to show its mods) and "Keywords" (tick a keyword to show the mods whose names carry
# it - "[NoDelete]", "test", "unpublished", or any word you add), and puts a mod count on every filter, MO2's own
# included. MO2's own filters stay exactly as they are, in the first tab, "Filters".
# (Developed as "Separator Filters"; renamed by the owner on 2026-09-22: "rename it to MO2 Custom Filters".)
#
# The owner, 2026-09-20: "make a plugin for Mod Organizer that adds to the filter feature to register the separators
# as filter categories so that you can filter by separator and then an alternate mode ... where you can prefix mods
# with keywords and filter by those keywords without having to type them in to the search bar". 2026-09-22: "i dont
# like how messy the filter tab looks, i want to add a tab to the mo2 filter area where our plugin can take place which
# preserves the mo2 filter and we can add a 3rd tab for keywords only".
#
# HOW IT WORKS (2.0). The first version stamped every separator into MO2's CATEGORY list (categories.dat), which put
# 127 separator names among the real categories - the mess. 2.0 never touches categories. When MO2's window is built,
# the "Filters" group box's own contents (the filter tree, Clear / Edit..., And / Or, Filter separators) are moved,
# untouched and still wired to MO2, into the first page of a tab widget; the two tabs of ours sit beside it. Picking
# ticked entries in our tabs narrows the mod list by hiding rows in the VIEW (QTreeView.setRowHidden), on top of
# whatever MO2's own filters and search box already show, and is re-applied whenever MO2 re-sorts, refreshes or
# re-filters the list. 2.1: tick boxes with MO2's three states (include / invert / off), combined by MO2's And / Or;
# MO2's Clear buttons clear them. Nothing is written anywhere except the plugin's own settings.
#
# SEPARATORS: a mod belongs to the separator that stands above it in the list (profile priority); mods above the first
# separator are "(no separator)". Works with MO2's collapsible separators on or off.
# KEYWORDS: every "[Tag]" in a mod name (listed with its brackets), every configured leading word (none by default;
# "test", "unpublished" are the owner's own), and every word you add (matched anywhere in the name as a whole word,
# ignoring case). The one keyword shipped by default is "[NoDelete]" (the owner, 2026-09-22).
#
# 2.2: no toolbar button and no popup (the owner, 2026-09-22: "i dont want the seperator filter to have a popup at all").
# Keywords are managed by right-clicking the Keywords tab: empty space -> Add; a keyword you made (or a leading word
# such as test / unpublished) -> Edit / Remove. [Tags] come from mod names and have nothing to edit.
#
# 2.4-2.6 (the owner, 2026-09-22): MO2's own three filter-state pictures for the tick boxes; a "(count)" on every
# entry of ours and on every one of MO2's own filters; a search box on each of our tabs.
#
# Copyright (C) 2026 ApocryphaRealm. GPL-3.0-or-later - see LICENSE and NOTICE.md.

__version__ = "1.0.4"    # issued by version-gate.ps1; never typed by hand

import os
import re
import time

try:
    from PyQt6.QtCore import QModelIndex, Qt, QTimer
    from PyQt6.QtWidgets import (
        QAbstractItemView, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMenu, QTreeWidget, QTreeWidgetItem,
        QComboBox, QPushButton, QRadioButton, QTabWidget, QTreeView, QVBoxLayout, QWidget,
    )
    from PyQt6.QtGui import QBrush, QColor, QIcon
    _DISPLAY = Qt.ItemDataRole.DisplayRole
    _USER = Qt.ItemDataRole.UserRole
    _HORIZONTAL = Qt.Orientation.Horizontal
    _SINGLE = QAbstractItemView.SelectionMode.SingleSelection
    _NO_SELECTION = QAbstractItemView.SelectionMode.NoSelection
    _ENABLED_FLAGS = Qt.ItemFlag.ItemIsEnabled
    _CUSTOM_MENU = Qt.ContextMenuPolicy.CustomContextMenu
    _TOOLTIP = Qt.ItemDataRole.ToolTipRole
except ImportError:  # MO2 builds that still ship PyQt5
    from PyQt5.QtCore import QModelIndex, Qt, QTimer
    from PyQt5.QtWidgets import (
        QAbstractItemView, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMenu, QTreeWidget, QTreeWidgetItem,
        QComboBox, QPushButton, QRadioButton, QTabWidget, QTreeView, QVBoxLayout, QWidget,
    )
    from PyQt5.QtGui import QBrush, QColor, QIcon
    _DISPLAY = Qt.DisplayRole
    _USER = Qt.UserRole
    _HORIZONTAL = Qt.Horizontal
    _SINGLE = QAbstractItemView.SingleSelection
    _NO_SELECTION = QAbstractItemView.NoSelection
    _ENABLED_FLAGS = Qt.ItemIsEnabled
    _CUSTOM_MENU = Qt.CustomContextMenu
    _TOOLTIP = Qt.ToolTipRole

import mobase

_GREY = QBrush(QColor(130, 130, 130))
_NORMAL = QBrush()
# MO2's filter tree items (src/filterlist.cpp CriteriaItem): IDRole = UserRole, TypeRole = UserRole + 1,
# StateRole = UserRole + 2; the mod list's IndexRole (src/modlist.h) = UserRole + 1. _BASE_ROLE is ours: the label
# before we appended a count.
_ID_ROLE, _TYPE_ROLE, _STATE_ROLE = _USER, _USER + 1, _USER + 2
_INDEX_ROLE = _USER + 1
_BASE_ROLE = _USER + 40
try:
    _STATE_ACTIVE, _STATE_ESSENTIAL, _STATE_VALID = int(mobase.ModState.ACTIVE), int(mobase.ModState.ESSENTIAL), int(mobase.ModState.VALID)
except Exception:  # noqa: BLE001 - IModList::ModStates in src/imodlist.h: ACTIVE 2, ESSENTIAL 4, VALID 32
    _STATE_ACTIVE, _STATE_ESSENTIAL, _STATE_VALID = 2, 4, 32
# MO2's own filter-state icons (src/filterlist.cpp) - the same three pictures its Filters tab shows
_STATE_ICONS = {1: ":/MO/gui/checked-checkbox", -1: ":/MO/gui/indeterminate-checkbox", None: ":/MO/gui/unchecked-checkbox"}


def _state_icon(state):
    return QIcon(_STATE_ICONS.get(state, _STATE_ICONS[None]))


PLUGIN_NAME = "MO2 Custom Filters"
NO_SEPARATOR = "(no separator)"
SETTING_PREFIXES = "keyword_prefixes"    # comma-separated leading words that count as keywords
SETTING_WORDS = "keywords"               # comma-separated words the owner adds; matched anywhere in a mod name


class MO2CustomFilters(mobase.IPlugin):
    def __init__(self):
        super().__init__()
        self._organizer = None
        self._window = None
        self._tabs = None                # _FilterTabs, once the window is built

    # ---- IPlugin ------------------------------------------------------------------------------
    def init(self, organizer):
        self._organizer = organizer
        try:
            organizer.onUserInterfaceInitialized(self._on_ui)
        except Exception as exc:  # noqa: BLE001
            self._log(f"could not subscribe to the window being built: {exc}")
        return True

    def name(self):
        return PLUGIN_NAME

    def author(self):
        return "ApocryphaRealm"

    def description(self):
        return "Separators and Keywords tabs beside MO2's own filters, a search box on each, and a mod count on every filter."

    def version(self):
        major, minor, patch = (int(x) for x in __version__.split("."))
        return mobase.VersionInfo(major, minor, patch, mobase.ReleaseType.FINAL)

    def requirements(self):
        return []

    def settings(self):
        return [
            # the owner, 2026-09-22: "i want the only default keyword included in the mod to be [NoDelete]"
            mobase.PluginSetting(SETTING_PREFIXES, "Leading words that count as keywords (comma-separated)", ""),
            mobase.PluginSetting(SETTING_WORDS, "Your own keywords, matched anywhere in a mod name as a whole word (comma-separated)", "[NoDelete]"),
        ]

    # ---- settings -----------------------------------------------------------------------------
    def _setting(self, key):
        return self._organizer.pluginSetting(PLUGIN_NAME, key)

    def _set(self, key, value):
        self._organizer.setPluginSetting(PLUGIN_NAME, key, value)

    def prefixes(self):
        raw = str(self._setting(SETTING_PREFIXES) or "")
        return [p.strip().lower() for p in raw.split(",") if p.strip()]

    def words(self):
        raw = str(self._setting(SETTING_WORDS) or "")
        seen, out = set(), []
        for w in raw.split(","):
            w = w.strip()
            if w and w.lower() not in seen:
                seen.add(w.lower())
                out.append(w)
        return out

    def set_prefixes(self, prefixes):
        self._set(SETTING_PREFIXES, ",".join(prefixes))
        self._log(f"leading keywords now: {', '.join(prefixes) or '(none)'}")
        if self._tabs:
            self._tabs.rebuild()

    def set_words(self, words):
        self._set(SETTING_WORDS, ",".join(words))
        self._log(f"keywords now: {', '.join(words) or '(none)'}")
        if self._tabs:
            self._tabs.rebuild()

    def _log(self, msg):
        """plugins\\data\\mo2-custom-filters.log - MO2 shows Python output only at debug level"""
        try:
            path = os.path.join(self._organizer.basePath(), "plugins", "data", "mo2-custom-filters.log")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
        except Exception:  # noqa: BLE001
            pass

    # ---- what belongs where -------------------------------------------------------------------
    def mod_names(self):
        """every mod and separator by profile priority - top of the mod list first"""
        return list(self._organizer.modList().allModsByProfilePriority())

    def separators_of(self, names):
        """{mod: separator display name}, and the separators in list order"""
        current, out, order = NO_SEPARATOR, {}, []
        for n in names:
            if n.endswith("_separator"):
                current = n[: -len("_separator")]
                order.append(current)
                continue
            out[n] = current
        return out, order

    def keywords_of(self, names):
        """{mod: set of keywords}"""
        prefixes = self.prefixes()
        words = [(w, re.compile(r"(?<![A-Za-z0-9])" + re.escape(w) + r"(?![A-Za-z0-9])", re.I)) for w in self.words()]
        out = {}
        for n in names:
            if n.endswith("_separator"):
                continue
            # a "[Tag]" in a mod name is listed WITH its brackets, so it is the same entry as a keyword written that way
            kws = {"[" + m.group(1).strip() + "]" for m in re.finditer(r"\[([^\]]+)\]", n)}
            first = n.split(" ", 1)[0].lower()
            if first in prefixes:
                kws.add(first)
            kws |= {w for w, rx in words if rx.search(n)}
            if kws:
                out[n] = kws
        return out

    # ---- the window ---------------------------------------------------------------------------
    def _on_ui(self, window):
        self._window = window
        try:
            self._tabs = _FilterTabs(self, window)
            self._log("filter tabs added beside MO2's own filters")
        except Exception as ex:  # noqa: BLE001
            import traceback
            self._log("adding the filter tabs FAILED - MO2's filter pane is unchanged: " + "".join(traceback.format_exception(ex)))


class _FilterTabs:
    """Moves MO2's own filter pane into tab 1 and adds tab 2 (Separators) and tab 3 (Keywords).

    2.1 (the owner, 2026-09-22: "we need our tabs to be affected by the mo2 filter search and clear buttons at the bottom
    and we need the tick boxes like the mo2 filters so we can select and deselect specific filters"):
      * every entry is a tick box with MO2's three states - one click includes it, a second inverts it (excludes its
        mods), a third clears it; any number can be ticked, across both tabs;
      * the ticked entries combine with MO2's own And / Or setting, and with MO2's own filters and search box, which
        narrow the list first;
      * MO2's Clear (in the filter pane) and Clear all Filters (under the mod list) clear our ticks too;
      * each entry's count is what MO2's filters and search currently leave visible; an entry with none is greyed.
    """

    INCLUDE, EXCLUDE = 1, -1

    def __init__(self, plugin, window):
        self._p = plugin
        self._state = {"sep": {}, "kw": {}}   # name -> INCLUDE | EXCLUDE
        self._model = None
        self._seps, self._kws, self._sep_order = {}, {}, []
        group = window.findChild(QGroupBox, "categoriesGroup")
        self._view = window.findChild(QTreeView, "modList")
        if group is None or self._view is None or group.layout() is None:
            raise RuntimeError(f"MO2's filter pane or mod list was not found (group={group is not None}, "
                               f"modList={self._view is not None}) - a different MO2 version?")
        self._and = window.findChild(QRadioButton, "filtersAnd")
        self._or = window.findChild(QRadioButton, "filtersOr")
        # 2.5 (the owner, 2026-09-22: "I like how the separators and keywords tabs display how many mods actually apply
        # to each separator. Can you make that take effect on MO2's filters as well?"): MO2's own filter tree
        # (src/filterlist.cpp - object "filters", two columns, the name in column 1) gets the same "(count)" suffix.
        self._mo2_tree = window.findChild(QTreeWidget, "filters") or window.findChild(QTreeWidget, "categoriesList")
        self._contents_cache = {}
        self._content_feature = None

        # MO2's own filter widgets, moved as they are - same objects, same signals - into the first page.
        own = QWidget()
        own_lay = QVBoxLayout(own)
        own_lay.setContentsMargins(0, 4, 0, 0)
        lay = group.layout()
        first = True
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w is not None:
                own_lay.addWidget(w, 1 if first else 0)
                first = False
            elif item.layout() is not None:
                own_lay.addLayout(item.layout())

        self._tabs = QTabWidget(group)
        self._tabs.addTab(own, "Filters")
        self._lists = {}
        self._search = {}
        for kind, title in (("sep", "Separators"), ("kw", "Keywords")):
            page = QWidget()
            pl = QVBoxLayout(page)
            pl.setContentsMargins(0, 4, 0, 0)
            # 2.4 (the owner, 2026-09-22: "the tickbox colors are still wrong, check out the mo2 filters and how they
            # change color"): MO2's filter list (src/filterlist.cpp, CriteriaItem) does not use Qt check states at all -
            # it is a two-column QTreeWidget whose first column (23 px) shows one of MO2's own icons per state:
            # :/MO/gui/unchecked-checkbox, checked-checkbox and indeterminate-checkbox (inverted). Those icons are
            # compiled into ModOrganizer.exe and reachable from a Python plugin, so our lists are built the same way
            # and change colour exactly as MO2's do, under any theme.
            lst = QTreeWidget()
            lst.setColumnCount(2)
            lst.setHeaderHidden(True)
            lst.setIndentation(0)
            lst.setRootIsDecorated(False)
            lst.setUniformRowHeights(True)
            lst.setAlternatingRowColors(True)
            lst.setAllColumnsShowFocus(True)
            lst.header().setMinimumSectionSize(0)
            lst.header().resizeSection(0, 23)
            lst.setSelectionMode(_NO_SELECTION)
            lst.itemClicked.connect(lambda it, col, k=kind: self._cycle(k, it))
            pl.addWidget(lst, 1)
            self._lists[kind] = lst
            if kind == "kw":
                # 2.2 (the owner, 2026-09-22: "i dont want the seperator filter to have a popup at all, just add a right
                # click context menu that has add when clicking empty space and remove or edit when clicking an already
                # made filter")
                lst.setContextMenuPolicy(_CUSTOM_MENU)
                lst.customContextMenuRequested.connect(self._keyword_menu)
                lst.setToolTip("Right-click empty space to add a keyword; right-click one you made to edit or remove it")
            # 2.6 (the owner, 2026-09-22: "i want that carried over to our tabs so you can search filters and
            # keywords"): a search box beside Clear, like the one under the mod list, that narrows this tab's entries
            row = QHBoxLayout()
            search = QLineEdit()
            search.setPlaceholderText("Search " + title.lower())
            search.setClearButtonEnabled(True)
            search.textChanged.connect(lambda _t, k=kind: self._apply_search(k))
            self._search[kind] = search
            row.addWidget(search, 1)
            clear = QPushButton("Clear")
            clear.setToolTip("Untick every entry on this tab")
            clear.clicked.connect(lambda _=False, k=kind: self.clear(k))
            row.addWidget(clear)
            pl.addLayout(row)
            self._tabs.addTab(page, title)
        lay.addWidget(self._tabs)
        self._mo2_search = None
        self._add_mo2_search(window, own_lay)

        # re-apply after MO2 re-sorts, refreshes or re-filters, and after its own filter controls change
        self._timer = QTimer(group)
        self._timer.setSingleShot(True)
        self._timer.setInterval(300)          # was 50: leave MO2 a moment after the model settles
        self._timer.timeout.connect(self._apply)
        for name in ("filtersClear", "clearFiltersButton"):
            b = window.findChild(QPushButton, name)
            if b is not None:
                b.clicked.connect(lambda _=False: self.clear(None))
        for rb in (self._and, self._or):
            if rb is not None:
                rb.toggled.connect(self._schedule)
        search = window.findChild(QLineEdit, "modFilterEdit")
        if search is not None:
            search.textChanged.connect(self._schedule)
        mod_list = plugin._organizer.modList()
        for hook in ("onModInstalled", "onModRemoved", "onModMoved", "onModStateChanged"):
            try:
                getattr(mod_list, hook)(lambda *a: self.rebuild())
            except Exception:  # noqa: BLE001
                pass
        try:
            mod_list.onModInstalled(lambda *a: self._contents_cache.clear())   # a reinstall changes what a mod contains
        except Exception:  # noqa: BLE001
            pass
        # 1.0.2 (the owner, 2026-09-22, after MO2 Patch Tagger renamed 242 mods and the Keywords tab did not show
        # [Patch]: "just set it to reread on a refresh"): every MO2 refresh re-reads the mod names and rebuilds the
        # tabs. MO2 refreshes its plugin list as part of every refresh, and that is the callback the API offers.
        try:
            plugin._organizer.pluginList().onRefreshed(lambda *a: self.rebuild())
        except Exception as e:  # noqa: BLE001
            self._p._log(f"refresh hook not available: {e!r}")
        # MO2 rebuilds its filter tree (FilterList::refresh) on category edits and list refreshes, which drops our
        # counts - a short timer after rows appear puts them back
        self._mo2_timer = QTimer(group)
        self._mo2_timer.setSingleShot(True)
        self._mo2_timer.setInterval(750)      # coalesces MO2's dataChanged storms (start-up, refresh) into one recount
        self._mo2_timer.timeout.connect(self._count_mo2_filters)
        if self._mo2_tree is not None:
            try:
                self._mo2_tree.model().rowsInserted.connect(lambda *a: self._after_refresh(self._mo2_timer.start))
            except Exception as e:  # noqa: BLE001
                self._p._log(f"MO2 filter tree not hooked: {e!r}")
        self.rebuild()

    # ---- lists --------------------------------------------------------------------------------
    def rebuild(self):
        names = self._p.mod_names()
        self._seps, order = self._p.separators_of(names)
        self._kws = self._p.keywords_of(names)
        has_none = any(v == NO_SEPARATOR for v in self._seps.values())
        self._sep_order = ([NO_SEPARATOR] if has_none else []) + order
        kw_names = sorted({k for ks in self._kws.values() for k in ks} | set(self._p.words()), key=str.lower)
        for kind, entries in (("sep", self._sep_order), ("kw", kw_names)):
            lst = self._lists[kind]
            lst.clear()
            known = set(entries)
            self._state[kind] = {k: v for k, v in self._state[kind].items() if k in known}
            for name in entries:
                it = QTreeWidgetItem(["", name])
                it.setData(0, _USER, name)
                it.setFlags(_ENABLED_FLAGS)       # no Qt auto-toggle: a click is cycled by _cycle
                lst.addTopLevelItem(it)
                self._paint(kind, it)
            self._apply_search(kind)
        self._schedule()
        self._mo2_timer.start()

    def _apply_search(self, kind):
        """show only the entries whose name contains the tab's search text (any case); ticks are untouched"""
        edit, lst = self._search.get(kind), self._lists[kind]
        text = edit.text().strip().lower() if edit is not None else ""
        for i in range(lst.topLevelItemCount()):
            it = lst.topLevelItem(i)
            it.setHidden(bool(text) and text not in str(it.data(0, _USER)).lower())

    # ---- a search box on MO2's own Filters tab ------------------------------------------------
    def _add_mo2_search(self, window, own_lay):
        """1.0.1 (the owner, 2026-09-22: "can you make that dropdown a searchbar then to match the other 2 tabs"):
        the bottom row of MO2's Filters tab (And / Or / the "Filter separators" combo) gets a search box where the
        combo was; the combo keeps its job and moves up beside Clear / Edit...."""
        try:
            combo = window.findChild(QComboBox, "filtersSeparators")
            edit_btn = window.findChild(QPushButton, "filtersEdit")
            if combo is None or edit_btn is None:
                self._p._log("MO2 Filters tab search box not added: combo or Edit button not found")
                return
            # the row layouts sit inside plain QWidgets in MO2's .ui (the combo's parent is "widget"), so look
            # for the layout that directly holds each widget, from its parent widget's layout downwards
            def holding(lay, w):
                if lay is None:
                    return None
                if lay.indexOf(w) != -1:
                    return lay
                for i in range(lay.count()):
                    found = holding(lay.itemAt(i).layout(), w)
                    if found is not None:
                        return found
                return None
            bottom = holding(combo.parentWidget().layout() if combo.parentWidget() else None, combo)
            button_row = holding(edit_btn.parentWidget().layout() if edit_btn.parentWidget() else None, edit_btn)
            if bottom is None or button_row is None:
                self._p._log(f"MO2 Filters tab search box not added: rows not found (bottom={bottom is not None}, buttons={button_row is not None})")
                return
            pos = bottom.indexOf(combo)
            bottom.removeWidget(combo)
            button_row.addWidget(combo, 1)
            search = QLineEdit()
            search.setPlaceholderText("Search filters")
            search.setClearButtonEnabled(True)
            search.textChanged.connect(lambda _t: self._apply_mo2_search())
            bottom.insertWidget(pos, search, 2)
            self._mo2_search = search
        except Exception as e:  # noqa: BLE001
            self._p._log(f"MO2 Filters tab search box failed: {e!r}")

    def _apply_mo2_search(self):
        tree, edit = self._mo2_tree, self._mo2_search
        if tree is None or edit is None:
            return
        text = edit.text().strip().lower()
        for i in range(tree.topLevelItemCount()):
            it = tree.topLevelItem(i)
            base = it.data(0, _BASE_ROLE)
            label = str(base if base is not None else it.text(1)).lower()
            it.setHidden(bool(text) and text not in label)

    # ---- counts on MO2's own filters ----------------------------------------------------------
    # One tally per criterion over the whole profile (every mod, separators left out), computed the way
    # ModListSortProxy::categoryMatchesMod / contentMatchesMod decide them (src/modlistsortproxy.cpp, 2.5.2):
    #   Checked            enabled, or a mod that is always enabled          -> IModList state ACTIVE | ESSENTIAL
    #   Update available   a newer (or older) version is known               -> newestVersion vs version, ignoredVersion
    #   Backup / Managed   isBackup / not isForeign
    #   Has category       at least one category
    #   Conflict           any conflict flag                                  -> the Conflicts column's tooltip is non-empty
    #                                                                            (getConflictFlagText names exactly the
    #                                                                            flags hasConflictFlag counts)
    #   Has hidden files   FLAG_HIDDEN_FILES                                  -> "Contains hidden files" in the Flags tooltip
    #   Endorsed / Tracked endorsedState / trackedState
    #   Has Nexus ID       nexusId > 0, never for foreign / backup / Overwrite
    #   Has game data      not FLAG_INVALID                                   -> IModList state VALID
    #   <Contains X>       ModDataContent.getContentsFor(fileTree)           (cached per mod)
    #   a category         the category is set on the mod                    -> its name is in mod.categories()
    _SPECIAL_FIRST = 10000
    (_CHECKED_ID, _UPDATE_ID, _HASCAT_ID, _CONFLICT_ID, _HIDDEN_ID, _ENDORSED_ID, _BACKUP_ID, _MANAGED_ID,
     _GAMEDATA_ID, _NEXUS_ID, _TRACKED_ID) = range(10000, 10011)
    _TYPE_SPECIAL, _TYPE_CATEGORY, _TYPE_CONTENT = 0, 1, 2

    def _source_model(self):
        m = self._view.model()
        seen = 0
        while m is not None and hasattr(m, "sourceModel") and seen < 8:
            src = m.sourceModel()
            if src is None:
                break
            m, seen = src, seen + 1
        return m

    def _tooltip_facts(self):
        """{mod name: (has conflict, has hidden files)} read off the mod list's own model, filters or not"""
        out = {}
        try:
            model = self._source_model()
            all_mods = list(self._p._organizer.modList().allMods())     # ModInfo index order
            cols = {}
            for c in range(model.columnCount()):
                h = str(model.headerData(c, _HORIZONTAL, _DISPLAY) or "").strip().lower()
                if h in ("conflicts", "flags"):
                    cols[h] = c
            if "conflicts" not in cols or "flags" not in cols:
                return out
            def walk(parent):
                for r in range(model.rowCount(parent)):
                    idx0 = model.index(r, 0, parent)
                    i = idx0.data(_INDEX_ROLE)
                    i = r if i is None else int(i)
                    if 0 <= i < len(all_mods):
                        conflict = bool(str(model.index(r, cols["conflicts"], parent).data(_TOOLTIP) or "").strip())
                        hidden = "contains hidden files" in str(model.index(r, cols["flags"], parent).data(_TOOLTIP) or "").lower()
                        out[all_mods[i]] = (conflict, hidden)
                    if model.hasChildren(idx0):
                        walk(idx0)
            walk(QModelIndex())
        except Exception as e:  # noqa: BLE001
            self._p._log(f"conflict / hidden-file facts unavailable: {e!r}")
        return out

    def _contents_of(self, name, mod):
        if name in self._contents_cache:
            return self._contents_cache[name]
        ids = set()
        try:
            if self._content_feature is None:
                org = self._p._organizer
                try:
                    self._content_feature = org.gameFeatures().gameFeature(mobase.ModDataContent)
                except Exception:  # noqa: BLE001
                    self._content_feature = org.managedGame().feature(mobase.ModDataContent)
            if self._content_feature:
                ids = set(self._content_feature.getContentsFor(mod.fileTree()))
        except Exception:  # noqa: BLE001
            pass
        self._contents_cache[name] = ids
        return ids

    @staticmethod
    def _update_available(mod):
        try:
            newest, current, ignored = mod.newestVersion(), mod.version(), mod.ignoredVersion()
            if not newest.isValid():
                return False
            if ignored.isValid() and ignored.displayString() == newest.displayString():
                return False
            return newest.displayString() != current.displayString()
        except Exception:  # noqa: BLE001
            return False

    def _mod_facts(self):
        """{mod name: dict of facts} for every mod of the profile that is not a separator"""
        org = self._p._organizer
        ml = org.modList()
        tips = self._tooltip_facts()
        facts = {}
        for name in self._p.mod_names():
            if name.endswith("_separator"):
                continue
            mod = ml.getMod(name)
            if mod is None or mod.isSeparator():
                continue
            st = int(ml.state(name))
            foreign, backup, overwrite = bool(mod.isForeign()), bool(mod.isBackup()), bool(mod.isOverwrite())
            conflict, hidden = tips.get(name, (False, False))
            facts[name] = {
                self._CHECKED_ID: bool(st & _STATE_ACTIVE) or bool(st & _STATE_ESSENTIAL),
                self._UPDATE_ID: self._update_available(mod),
                self._HASCAT_ID: bool(mod.categories()),
                self._CONFLICT_ID: conflict,
                self._HIDDEN_ID: hidden,
                self._ENDORSED_ID: mod.endorsedState() == mobase.EndorsedState.ENDORSED_TRUE,
                self._BACKUP_ID: backup,
                self._MANAGED_ID: not foreign,
                self._GAMEDATA_ID: bool(st & _STATE_VALID),
                self._NEXUS_ID: (not (foreign or backup or overwrite)) and mod.nexusId() > 0,
                self._TRACKED_ID: mod.trackedState() == mobase.TrackedState.TRACKED_TRUE,
                "categories": set(mod.categories()),
                "contents": self._contents_of(name, mod),
            }
        return facts

    def _count_mo2_filters(self):
        tree = self._mo2_tree
        if tree is None:
            return
        try:
            t0 = time.time()
            facts = self._mod_facts()
            done = 0
            for i in range(tree.topLevelItemCount()):
                it = tree.topLevelItem(i)
                base = it.data(0, _BASE_ROLE)
                if base is None:
                    base = re.sub(r"\s{4}\(\d+\)$", "", it.text(1))
                    it.setData(0, _BASE_ROLE, base)
                ctype, cid = it.data(0, _TYPE_ROLE), it.data(0, _ID_ROLE)
                ctype = -1 if ctype is None else int(ctype)
                cid = -1 if cid is None else int(cid)
                if ctype == self._TYPE_SPECIAL:
                    count = sum(1 for f in facts.values() if f.get(cid, False))
                elif ctype == self._TYPE_CATEGORY:
                    count = sum(1 for f in facts.values() if base in f["categories"])
                elif ctype == self._TYPE_CONTENT:
                    count = sum(1 for f in facts.values() if cid in f["contents"])
                else:
                    continue
                it.setText(1, f"{base}    ({count})")
                state = it.data(0, _STATE_ROLE)
                inactive = state is None or int(state) == 0
                it.setForeground(1, _GREY if count == 0 and inactive else _NORMAL)
                done += 1
            self._p._log(f"MO2 filter counts: {done} entries over {len(facts)} mods in {time.time() - t0:.2f}s")
            self._apply_mo2_search()      # MO2 rebuilt its tree: the search narrows the new items too
        except Exception as e:  # noqa: BLE001
            self._p._log(f"MO2 filter counts failed: {e!r}")

    def _paint(self, kind, it, count=None):
        name = it.data(0, _USER)
        st = self._state[kind].get(name)
        it.setIcon(0, _state_icon(st))
        label = name if count is None else f"{name}    ({count})"
        it.setText(1, label)
        tip = "Click to include, again to exclude (invert), again to clear"
        it.setToolTip(0, tip)
        it.setToolTip(1, tip)
        if count is not None:
            it.setForeground(1, _GREY if count == 0 and st is None else _NORMAL)

    def _cycle(self, kind, it):
        name = it.data(0, _USER)
        st = self._state[kind].get(name)
        new = self.INCLUDE if st is None else (self.EXCLUDE if st == self.INCLUDE else None)
        if new is None:
            self._state[kind].pop(name, None)
        else:
            self._state[kind][name] = new
        self._p._log(f"filter: {kind} {name!r} -> {'include' if new == self.INCLUDE else 'exclude' if new == self.EXCLUDE else 'off'}")
        self._schedule()

    def clear(self, kind):
        kinds = ("sep", "kw") if kind is None else (kind,)
        if any(self._state[k] for k in kinds):
            self._p._log(f"filter: cleared {', '.join(kinds)}")
        for k in kinds:
            self._state[k] = {}
        self._schedule()

    def _origin(self, name):
        """'word' (added by you), 'prefix' (a leading word such as test / unpublished) or 'tag' (a [Tag] in mod names)"""
        if name.lower() in {w.lower() for w in self._p.words()}:
            return "word"
        if name.lower() in self._p.prefixes():
            return "prefix"
        return "tag"

    def _keyword_menu(self, pos):
        lst = self._lists["kw"]
        item = lst.itemAt(pos)
        menu = QMenu(lst)
        if item is None:
            menu.addAction("Add keyword...").triggered.connect(lambda _=False: self._add_keyword())
        else:
            name = item.data(0, _USER)
            origin = self._origin(name)
            if origin == "tag":
                note = menu.addAction(f"{name} comes from mod names - nothing to edit")
                note.setEnabled(False)
                menu.addSeparator()
                menu.addAction("Add keyword...").triggered.connect(lambda _=False: self._add_keyword())
            else:
                menu.addAction(f"Edit '{name}'...").triggered.connect(lambda _=False, n=name, o=origin: self._edit_keyword(n, o))
                menu.addAction(f"Remove '{name}'").triggered.connect(lambda _=False, n=name, o=origin: self._remove_keyword(n, o))
        menu.exec(lst.viewport().mapToGlobal(pos))

    def _ask(self, title, label, text=""):
        value, ok = QInputDialog.getText(self._lists["kw"], title, label, text=text)
        value = str(value).replace(",", " ").strip() if ok else ""
        return value or None

    def _add_keyword(self):
        w = self._ask("Add keyword", "A word to find anywhere in a mod name (whole word, any case):")
        if not w:
            return
        words = self._p.words()
        if w.lower() not in {x.lower() for x in words}:
            words.append(w)
            self._p.set_words(words)

    def _edit_keyword(self, name, origin):
        new = self._ask("Edit keyword", "Keyword:", name)
        if not new or new == name:
            return
        if name in self._state["kw"]:
            self._state["kw"][new] = self._state["kw"].pop(name)
        if origin == "prefix":
            self._p.set_prefixes([new.lower() if p == name.lower() else p for p in self._p.prefixes()])
        else:
            self._p.set_words([new if w.lower() == name.lower() else w for w in self._p.words()])

    def _remove_keyword(self, name, origin):
        self._state["kw"].pop(name, None)
        if origin == "prefix":
            self._p.set_prefixes([p for p in self._p.prefixes() if p != name.lower()])
        else:
            self._p.set_words([w for w in self._p.words() if w.lower() != name.lower()])

    # ---- the view -----------------------------------------------------------------------------
    def _schedule(self, *args):
        self._after_refresh(self._timer.start)

    def _after_refresh(self, fn):
        """Run fn now if MO2 is idle, else once its current refresh has finished. A rename or a refresh resets the mod
        list's model while MO2 is still rebuilding its mod and profile tables; a slot that then asks mobase for every
        mod's state took MO2 down (2026-09-23, "MO2 keeps closing after renaming a separator or mod"). IOrganizer's
        onNextRefresh(fn, immediate_if_possible=True) is MO2's own way of waiting that out."""
        try:
            self._p._organizer.onNextRefresh(fn, True)
        except Exception:  # noqa: BLE001
            fn()

    def _hook(self, model):
        if model is self._model:
            return
        self._model = model
        for sig in ("modelReset", "layoutChanged", "rowsInserted", "rowsRemoved"):
            try:
                getattr(model, sig).connect(self._schedule)
            except Exception:  # noqa: BLE001
                pass
        # conflict and hidden-file flags are worked out a few seconds after start-up, once MO2 has built its
        # directory structure, and announced by ModList::notifyChange -> dataChanged over every row (also after a
        # refresh); recount MO2's filters then, else Conflicted / Has hidden files read 0
        try:
            self._source_model().dataChanged.connect(lambda *a: self._after_refresh(self._mo2_timer.start))
        except Exception as e:  # noqa: BLE001
            self._p._log(f"mod list dataChanged not hooked: {e!r}")

    def _name_column(self, model):
        for c in range(model.columnCount()):
            h = model.headerData(c, _HORIZONTAL, _DISPLAY)
            if h and str(h).strip().lower() in ("mod name", "name"):
                return c
        return 0

    def _rows(self, model, col):
        """every row MO2 currently shows (after its own filters and search): (parent, row, text, has_children)"""
        out = []
        def walk(parent):
            for r in range(model.rowCount(parent)):
                idx0 = model.index(r, 0, parent)
                text = str(model.index(r, col, parent).data(_DISPLAY) or "")
                kids = model.hasChildren(idx0)
                out.append((parent, r, text, kids))
                if kids:
                    walk(idx0)
        walk(QModelIndex())
        return out

    def _apply(self):
        t0 = time.time()
        try:
            self._apply_inner()
        finally:
            dt = time.time() - t0
            if dt > 0.15:
                self._p._log(f"apply took {dt:.2f}s")

    def _apply_inner(self):
        view = self._view
        model = view.model()
        if model is None:
            return
        self._hook(model)
        col = self._name_column(model)
        rows = self._rows(model, col)
        seps, kws = self._seps, self._kws
        sep_labels = set(self._sep_order)
        is_sep = lambda t: t in sep_labels and t not in seps
        present = [t for (_, _, t, _) in rows if not is_sep(t)]

        # counts: what MO2's own filters and search leave visible
        for kind, lst in self._lists.items():
            counts = {}
            for t in present:
                if kind == "sep":
                    s = seps.get(t)
                    if s is not None:
                        counts[s] = counts.get(s, 0) + 1
                else:
                    for k in kws.get(t, ()):
                        counts[k] = counts.get(k, 0) + 1
            for i in range(lst.topLevelItemCount()):
                it = lst.topLevelItem(i)
                self._paint(kind, it, counts.get(it.data(0, _USER), 0))
            active = bool(self._state[kind])
            self._tabs.setTabText(1 if kind == "sep" else 2, ("Separators" if kind == "sep" else "Keywords") + (" *" if active else ""))

        inc = [(k, n) for k in ("sep", "kw") for n, v in self._state[k].items() if v == self.INCLUDE]
        exc = [(k, n) for k in ("sep", "kw") for n, v in self._state[k].items() if v == self.EXCLUDE]
        and_mode = bool(self._and is not None and self._and.isChecked())

        def matches(mod, kind, name):
            return seps.get(mod) == name if kind == "sep" else name in kws.get(mod, ())

        def mod_visible(mod):
            if any(matches(mod, k, n) for k, n in exc):
                return False
            if not inc:
                return True
            hits = [matches(mod, k, n) for k, n in inc]
            return all(hits) if and_mode else any(hits)

        filtering = bool(inc or exc)
        visible = {t for t in present if mod_visible(t)} if filtering else set(present)
        # a separator row stays when any of its mods is shown, or when it is itself ticked
        sep_shown = {seps[t] for t in visible if t in seps}
        sep_shown |= {n for n, v in self._state["sep"].items() if v == self.INCLUDE}
        sep_shown -= {n for n, v in self._state["sep"].items() if v == self.EXCLUDE}
        # 1.0.3 (ProteusBlack on the mod page, 2026-09-22: "I was hoping the Separators filter results in the main window
        # would include all the mods under the filter search. Is there a reason it doesn't show them?"): a row that has
        # CHILDREN is a container - a separator with MO2's collapsible separators on, or a group row when the list is
        # grouped by category / Nexus ID / priority. Those were judged as if they were mods, so they and everything under
        # them were hidden. A container now shows when any row under it shows, and is expanded so its mods are actually
        # in view; a ticked separator still shows even when nothing under it survives the other ticks.
        def apply_to(parent):
            any_shown = False
            for r in range(model.rowCount(parent)):
                idx0 = model.index(r, 0, parent)
                text = str(model.index(r, col, parent).data(_DISPLAY) or "")
                has_kids = model.hasChildren(idx0)
                child_shown = apply_to(idx0) if has_kids else False
                if not filtering:
                    show = True
                elif is_sep(text):
                    show = child_shown or text in sep_shown
                elif has_kids:
                    show = child_shown
                else:
                    show = text in visible
                view.setRowHidden(r, parent, not show)
                if filtering and show and child_shown:
                    view.expand(idx0)
                any_shown = any_shown or show
            return any_shown

        apply_to(QModelIndex())


def createPlugin():
    return MO2CustomFilters()


# --- fault handling (standing rule, 2026-09-23: every MO2 plugin of ours logs and arms faulthandler) ---------------
def _arm_faulthandler():
    """Arm Python's faulthandler once per process, into plugins\\data\\faults.log. When MO2 dies inside C++ with a
    Python slot on the stack, the minidump names only modules; faulthandler writes the Python frames of every
    thread first, so the log names the plugin and the line. Whichever of our plugins loads first arms it."""
    try:
        import faulthandler
        import os
        import time
        if faulthandler.is_enabled():
            return
        here = os.path.abspath(__file__)
        while os.path.basename(here).lower() != "plugins":
            parent = os.path.dirname(here)
            if parent == here:
                return
            here = parent
        path = os.path.join(here, "data", "faults.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fh = open(path, "a", encoding="utf-8")
        who = os.path.basename(os.path.dirname(__file__)) if os.path.basename(__file__) == "__init__.py" else os.path.basename(__file__)
        fh.write(time.strftime("%Y-%m-%d %H:%M:%S") + " faulthandler armed by " + who + chr(10))
        fh.flush()
        globals()["_FAULT_LOG_HANDLE"] = fh          # kept open for the life of the process
        faulthandler.enable(file=fh, all_threads=True)
    except Exception:  # noqa: BLE001
        pass


_arm_faulthandler()
