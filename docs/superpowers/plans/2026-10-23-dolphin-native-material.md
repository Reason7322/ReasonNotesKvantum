# Dolphin-Native Material Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an independently staged Qt Widgets ReasonNotes candidate whose default surfaces are owned by the active qt6ct/Kvantum style and visually target Dolphin without hardcoded colors or opacity.

**Architecture:** Promote the existing `PE_Widget` native top-level renderer to the default, add an explicit native-style mode to the custom material widgets so the default bypasses application-painted fills, and return the note editor to its unmodified native palette/style surface. Keep legacy material variants diagnostic-only and preserve every behavioral interface.

**Tech Stack:** Python 3.14, PySide6/Qt 6 Widgets, qt6ct-style, Kvantum, unittest, native Wayland helper.

**Spec:** `docs/superpowers/specs/2026-10-23-dolphin-native-material-design.md`

## Global Constraints

- Dolphin is the authoritative visual reference; preserve ReasonNotes layout and behavior.
- No literal HEX/RGB/RGBA/HSL colors, fixed background opacity, invented tints, or custom fallback palettes in the new default rendering path.
- Default window, sidebar, card, search, and editor surfaces must derive from active `QStyle`/`QPalette` and adapt to theme changes.
- Do not replace the installed candidate or touch either personal notes repository, Android, synchronization, or global desktop/theme configuration.
- Do not launch interactively without separate Reason authorization; keep deliberate artifacts out of `/tmp`.
- Resolve or safely account for the earlier production generated-view writes before requesting any live test.

## Review Focus

- A valid `qt6ct-style -> Kvantum` proxy chain must be retained; a chain with no
  Kvantum leaf must fail clearly if Kvantum cannot be loaded, without installing
  an application fallback palette; test in Task 1.
- Active/inactive/disabled palette groups must remain style-owned without custom color overrides; test in Task 2.
- Native mode must cover sidebar, cards, and search surround, not only the exposed top-level pixels; test in Task 1.
- The editor must remain readable/editable and retain title/body geometry after removing the fixed surface; test in Task 2.
- Diagnostic legacy modes must not become the packaged default or leak custom constants into native mode; test in Task 1.

---

### Task 1: Make native Qt/Kvantum material the complete default

**Files:**
- Modify: `tests/test_widgets_native_material.py`
- Modify: `src/reasonnotes_widgets/main_window.py`
- Modify: `src/reasonnotes_widgets/material.py`
- Modify: `linux-app/reasonnotes_widgets.py`

**Interfaces:**
- Consumes: `ReasonNotesMainWindow(..., native_window_material: bool, kitty_window_material: bool)`, existing `PE_Widget` renderer, and the real `qt6ct-style` `QProxyStyle` whose base/leaf style is Kvantum.
- Produces: default `window_material_mode == "native-kvantum"`; `set_native_style_enabled(enabled: bool)` on `NavigationRail`, `GlassCard`, and `SearchWell`; verified preservation of the `qt6ct-style -> Kvantum` chain; parser diagnostics that cannot change the native packaged default accidentally.

- [ ] **Step 1: Write failing default/native-coverage tests**

Add tests asserting that a default window selects `native-kvantum`, every large material widget reports native-style mode, and native-mode rendering delegates to the active style instead of invoking its custom gradient/rim/search paint paths. Under the actual disposable qt6ct/Kvantum environment, assert the application style remains the `qt6ct-style` wrapper and its base/leaf is Kvantum; do not require the top-level `objectName()` to equal `kvantum`. Add an explicit missing-Kvantum test that raises a clear runtime error and never installs a fallback palette. Assert mutually exclusive diagnostic switches cannot make a custom fallback implicit.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src /usr/bin/python3 -m unittest tests.test_widgets_native_material -v`

Expected: failures showing the current default is `reasonnotes-custom` and material widgets lack native-style mode.

- [ ] **Step 3: Implement native-style default delegation**

Make `native-kvantum` the default in `ReasonNotesMainWindow`. In native mode, configure `NavigationRail`, all `GlassCard` instances, and `SearchWell` instances to delegate their surfaces to the active style/palette without applying custom colors, alpha, gradients, rims, or fallback palettes. Preserve and validate a real `qt6ct-style` wrapper over Kvantum; missing-style handling may select the installed Kvantum style explicitly or fail clearly, but may not reject the valid wrapper or invent palette colors. Keep behavioral/layout code unchanged.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Step 2 command; expected: all tests pass with no crashes or Qt warnings attributable to the change.

- [ ] **Step 5: Commit the native foundation**

Commit the spec, plan, tests, and implementation with message `feat(ui): use native Kvantum material by default`.

### Task 2: Remove the fixed editor color and retain native editing behavior

**Files:**
- Modify: `tests/test_widgets_visual_polish.py`
- Modify: `tests/test_widgets_main_window.py`
- Modify: `src/reasonnotes_widgets/editor_page.py`
- Modify: `src/reasonnotes_widgets/visuals.py`

**Interfaces:**
- Consumes: the default native material state from Task 1 and `QPlainTextEdit` native style/palette behavior.
- Produces: editor body with no application-assigned Base/AlternateBase color and unchanged title/body editing, focus, wrapping, document margin, and geometry.

- [ ] **Step 1: Replace the fixed-color regression with native-palette assertions**

Write tests asserting the body editor retains the active application/style Base brushes for active, inactive, and disabled groups; the source default path contains no call assigning a literal editor color; and existing editor geometry/editability tests remain unchanged.

- [ ] **Step 2: Run affected tests and verify RED**

Run: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src /usr/bin/python3 -m unittest tests.test_widgets_visual_polish tests.test_widgets_main_window -v`

Expected: the native-palette assertions fail because `#2C3539` is assigned.

- [ ] **Step 3: Remove `integrate_solid_surface` from the editor default**

Remove the literal `QColor` construction and solid-surface call. Use unmodified native `QPlainTextEdit` style/palette behavior; retain frame and geometry behavior only where it does not assign colors or opacity. Remove the obsolete helper if no non-test production caller remains.

- [ ] **Step 4: Run affected and native-material tests**

Run: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src /usr/bin/python3 -m unittest tests.test_widgets_visual_polish tests.test_widgets_main_window tests.test_widgets_native_material -v`

Expected: all tests pass; editor behavior and default native-material assertions remain green.

- [ ] **Step 5: Commit the editor correction**

Commit with message `fix(ui): return editor surface to native palette`.

### Task 3: Prove isolation and stage the review candidate

**Files:**
- Modify: `tests/test_candidate_install.py`
- Modify: `tests/test_widgets_bootstrap.py`
- Create: `scripts/verify-candidate-isolation.py`
- Modify: `PROJECT_STATUS.md`
- Create: `docs/DOLPHIN_NATIVE_MATERIAL_VALIDATION_2026-10-23.md`
- Generated artifact: `/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/`

**Interfaces:**
- Consumes: candidate installer, `resolve_launch_paths()`, explicit `--root`/`--inbox`/`--received-dir`, inherited HOME/XDG environment, `/proc` process command lines, and the native default from Tasks 1-2.
- Produces: `verify_candidate_isolation(...)` reporting canonical resolved paths, aliases, protected-path overlap, inherited environment, and conflicting ReasonNotes processes; immutable staged release and launcher under a new persistent root; hashes, offline render evidence, and a blocked-or-safe future launch recipe.

- [ ] **Step 1: Write real unsafe/safe isolation regressions**

Add tests that call the isolation verifier with canonical and symlink-aliased paths. The unsafe cases must reject: the production repository directly; a symlink resolving into production; an inherited `XDG_DATA_HOME` that makes a nominal default overlap production; a broad parent path containing a protected tree; and command lines for a concurrently running production or installed-candidate ReasonNotes process. The safe case must accept fully resolved candidate-only HOME/XDG/repository/inbox/received roots and no conflicting process. Also launch the packaged `--check-launch` path against safe explicit roots with sentinel production and installed-candidate trees, asserting only the explicit disposable repository receives generated index/view files and every sentinel content hash remains unchanged.

- [ ] **Step 2: Run isolation tests and verify RED for actual unsafe gaps**

Run: `PYTHONPATH=src /usr/bin/python3 -m unittest tests.test_candidate_install tests.test_widgets_bootstrap -v`

Expected: the new verifier tests fail because concurrent-process and complete inherited-environment checks do not yet exist. Existing unsafe direct/symlink path cases that already pass are characterization evidence, not RED evidence. After implementation, every unsafe case must fail closed and the isolated case must pass. Any write to either sentinel tree blocks the milestone.

- [ ] **Step 3: Implement the focused isolation verifier**

Implement `verify_candidate_isolation(...)` in the new script using canonical `Path.resolve()` results, explicit protected production and installed-candidate roots, the effective inherited HOME/XDG environment, and exact process command-line matching for ReasonNotes executables. Its report must print the requested and resolved repository/inbox/received paths and each relevant environment root without exposing note contents. Return nonzero on any overlap, alias, unresolved path, or conflicting process. Do not stop processes or change configuration.

- [ ] **Step 4: Run focused integrated verification**

Run the three affected suites plus candidate-install coverage in an isolated persistent qt6ct/Kvantum environment. Expected: all pass, with no unrelated full-suite rerun unless failures or broad changes justify it.

- [ ] **Step 5: Build an immutable candidate without activation**

Use `scripts/install-candidate.py` with install root, launcher, desktop entry, HOME, XDG roots, and test repository all beneath `/home/reason/Temporary/ReasonNotes-Dolphin-Native-Candidate/`. Copy the current qt6ct/Kvantum configuration read-only into the disposable config root. Do not invoke the launcher interactively.

- [ ] **Step 6: Capture offline evidence and document the visual gate**

Render offscreen with synthetic notes, record the real `qt6ct-style -> Kvantum` chain and native material ownership, artifact hashes, installed-candidate/personal-note hashes before and after, and the exact controlled live command requiring separate authorization. Run the isolation verifier immediately before any future requested launch; a concurrent process or canonical-path overlap blocks it. State that only matched real Wayland screenshots beside Dolphin can establish visual acceptance.

- [ ] **Step 7: Commit and dual-remote checkpoint**

Update status/validation docs, run `git diff --check`, commit on `forge/reasonnotes-completion`, push the exact commit to `handoff` and `github`, independently verify both full SHAs equal local HEAD, and stop without deployment or live launch.
