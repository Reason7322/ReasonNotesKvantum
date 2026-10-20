# Qwen → Forge Handoff — Mission 03 Editor UI Cleanup Checkpoint (2026-10-20)

**Overall product: INCOMPLETE.** Unchanged goal: complete, functional, owner-visually-approved native Qt Widgets/Kvantum ReasonNotes replacement preserving editing, autosave/recovery, history, KDE Connect/Android sync, conflict/deletion handling, and EN/PL localization. The owner-approved Kitty-mode glass rim is preserved (rim tests green this shift). Outstanding gates remain: visual acceptance of the Mission 03 changes, physical Android validation, authorized production cutover. Nothing was deployed; no live configuration or production state changed.

## Transfer state

- Worktree: `/home/reason/Temporary/QwenProjects/ReasonNotesKvantum-kitty-glass-refinement`
- Branch: `qwen/kitty-glass-refinement`; incoming checkpoint of this work: `f11df11572108e01c68274b4326d45af34fab15d`.
- This commit adds the Mission 03 source/test changes below plus status docs. It is a checkpoint, not product completion.

## What can be safely reused (done and tested)

- `src/reasonnotes_widgets/editor_page.py` — writing card now `title_editor → title_rule → body_editor` contiguous; no status bar objects exist anymore.
- `src/reasonnotes_widgets/visuals.py::integrate_solid_surface(view, color)` — opaque exact-color writing surface (used for the note body only).
- `src/reasonnotes_widgets/i18n.py` — `title_placeholder` key (`Title` / `Tytuł`); `untitled` and `start_writing` removed from both catalogs.
- `src/reasonnotes_widgets/main_window.py::retranslate()` (placeholders) and `_refresh_status()` (sidebar-only status updates; controller events untouched).
- Tests: new/updated regressions in `tests/test_widgets_visual_polish.py`, `tests/test_widgets_main_window.py`, `tests/test_widgets_i18n.py`.

Valid test environment (established this shift): disposable qt6ct + LiquidGlass copies in a Qwen-owned isolated HOME/XDG, e.g. copy live `~/.config/qt6ct/qt6ct.conf` (strip the `color_scheme_path=` line — that data-home file is outside Qwen's read set; set `custom_palette=false`) and `~/.config/Kvantum/kvantum.kvconfig` + `LiquidGlass/{LiquidGlass.kvconfig,LiquidGlass.svg}` into `$E/home/.config/...`, then:

    QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME=qt6ct PYTHONPATH=src \
    HOME=$E/home XDG_CONFIG_HOME=$E/home/.config XDG_DATA_HOME=$E/home/.local/share \
    python3 -m unittest tests.test_widgets_main_window tests.test_widgets_visual_polish \
      tests.test_widgets_i18n tests.test_widgets_native_material

Bare offscreen without qt6ct is NOT a valid recipe (fails unrelated palette/frame assertions).

## This checkpoint's test evidence

Four suites, isolated env above: **33 ran, 9 failures**. All 9 are splitter-change fallout; everything else passed — including autosave/persistence/shortcuts, EN↔PL placeholder switching with saved titles intact, exact-`#2C3539` body-surface pixel grid, and all Kitty sheet/rim/native-material pixel tests.

Failures:
1. `test_sidebar_splitter_handle_is_hover_only_and_still_resizable` — handle-count assertion `2 != 1`: QSplitter creates multiple `QSplitterHandle` children (a boundary one at the sidebar edge plus others); selection must target the one whose geometry abuts `sidebar.geometry().right()`.
2–9. Four `hasFrame()` subtests and four proxy-chain assertions in `test_writing_search_and_list_surfaces_reveal_kvantum_window_material` / `test_line_edit_proxy_suppresses_only_the_forced_kvantum_panel`: the scoped stylesheet on `main_splitter` (the currently committed hover approach) wraps the subtree style — `field.style()` becomes a bare `QCommonStyle`, Kvantum re-polish re-enables line-edit frames.

## Blocker: splitter hover-only mechanism (evidenced, not yet implemented)

The coordinator-prescribed scoped QSS on `main_splitter` cannot work on this stack for the reasons above. Additional evidenced facts so the next engineer does not re-derive them:

- A `QSplitterHandle` child paints itself opaque with its own palette (isolated render = `(28,33,33,255)` window color); setting Base/Window/AlternateBase/Button roles transparent for all groups makes it paint nothing. No autoFill flag is involved.
- Any non-empty stylesheet on `main_splitter` corrupts every descendant's style chain; stylesheets scoped to the handle widget itself do NOT self-match `QSplitter::handle`.
- Subclassing `QSplitterHandle`/overriding `createHandle()` segfaults in this PySide6 build — avoid.
- The splitter does call `style()->drawControl(CE_Splitter, opt, painter, widget)` per handle through the SPLITTER's style (interceptable by a narrowly scoped QProxyStyle on `main_splitter`, mirroring the existing `IntegratedLineEditStyle` pattern); the enum member is `QStyle.ControlElement.CE_Splitter`. Observed: `widget` arg is the splitter itself, `opt.rect` is handle-local `(0,0,w,h)`, painter transform dx/dy = 0 during offscreen render (no per-handle translation), and no `State_Hovered` was set in unhovered renders. Per-handle identity/positioning inside `drawControl` therefore needs a small verification before the hover-grip paint is trusted; drag hit target and width persistence must be re-verified with the same synthetic-drag test already in place (press at `sidebar.right() + handle.width()/2`, move +40 px).

## ONE next action

Replace the splitter QSS in `main_window.py` with: (a) transparent Base/Window-family palette on each real boundary `QSplitterHandle` child, and (b) a small `QProxyStyle` installed only on `main_splitter` that suppresses `CE_Splitter` art normally and paints the hover grip when its handle is hovered — then rerun the four suites in the isolated qt6ct/LiquidGlass environment until 33/33 pass, keeping the existing drag/persistence assertions as the hit-target proof. Afterward only the owner's Workspace 10 screenshot review (established Hyprland Lua dispatcher + `grim -o DP-2` into `docs/evidence/editor-ui-cleanup/`) remains for this mission, then physical Android acceptance and separately authorized cutover.

## Mission 04 — Kvantum styling regression restore checkpoint (2026-10-20)

Source-only repair of the Mission 03 splitter-QSS regression, per mission instruction. The scoped `QSplitter::handle:horizontal` stylesheet on `main_splitter` was removed entirely from `src/reasonnotes_widgets/main_window.py`, together with its comment and the grip/hover-color assignments (and their dedicated `QPalette` import). Nothing else in that file changed: splitter creation, widget order, stretch factors, `setChildrenCollapsible(False)`, sidebar width persistence, and all other styling are untouched. No hover-only handle behavior was implemented in this mission; the Mission 03 evidence above (transparent-palette boundary handle + narrow `QProxyStyle` overriding only `CE_Splitter`) remains the identified replacement mechanism, with its open verification items unchanged.

Test evidence (this shift): the two focused methods holding the eight previously failing frame/proxy assertions pass under the established isolated offscreen/qt6ct recipe: `tests.test_widgets_visual_polish.WidgetsVisualPolishTests.test_writing_search_and_list_surfaces_reveal_kvantum_window_material` and `.test_line_edit_proxy_suppresses_only_the_forced_kvantum_panel` → Ran 2 tests, OK. `git diff --check` clean. The three other Mission 03 improvements (header status removal, `Title`/`Tytuł` placeholders, opaque `#2C3539` body surface) are untouched by this diff.

Still open: the hover-only splitter handle (`test_sidebar_splitter_handle_is_hover_only_and_still_resizable`) remains unimplemented and may fail; it must not be attempted in a styling-restore mission. **PRODUCT INCOMPLETE.** No deployment, live configuration, production, or Android changes this shift.
