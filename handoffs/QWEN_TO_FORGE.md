# Qwen → Forge Handoff — Mission 02 Native Wayland A/B Capture (2026-10-20)

**Overall product: INCOMPLETE.** The unchanged goal is a complete, functional, owner-visually-approved native Qt Widgets/Kvantum ReasonNotes replacement preserving the existing layout, editing, autosave/recovery, immutable history, KDE Connect/Android synchronization, conflict/deletion handling, and English/Polish localization. Outstanding acceptance criteria: (1) owner visual judgment of this A/B evidence, (2) physical Android interoperability validation, (3) separately authorized production cutover with rollback. **Nothing was deployed.** No candidate or production state was modified in this shift.

## Exact transfer state

- Qwen-owned worktree: `/home/reason/Temporary/QwenProjects/ReasonNotesKvantum-kitty-glass-refinement`
- Branch: `qwen/kitty-glass-refinement`
- Incoming checkpoint (rim implementation): `459367402ee3c251e55660121d763d821b85233e` — verified identical on local HEAD, `handoff`, and `github` before this shift started.
- Base/source material checkpoint (version A origin): `30bc0fe7ccd9bce6e0844876295f3e073fe9807f`.
- This transfer commit adds exactly four files/changes: the two composited screenshots below plus this document and `PROJECT_STATUS.md`. It is a checkpoint, not product completion.

## Implemented in the previous checkpoint (unchanged here)

A nine-stroke inward-fading glass rim painted only for `GlassCard`s with material fill disabled (Kitty mode), keeping card interiors fill-free; four pixel regression tests added to `tests/test_widgets_native_material.py`; top-level sheet preserved at exactly `QColor(28,33,33,209)`; default and native-material variants untouched. The only functional A→B source delta is the rim block in `src/reasonnotes_widgets/material.py` (plus those tests).

## This shift's captured evidence

Two full-resolution native Wayland compositor screenshots (`grim -o DP-2`, 2560x1440 RGB, original resolution preserved):

- Version A (before rim, base `30bc0fe7` source export run from a separate Qwen-owned tree): `docs/evidence/kitty-rim-wayland-ab/reasonnotes-before.png`
- Version B (after rim, checkpoint `45936740…`): `docs/evidence/kitty-rim-wayland-ab/reasonnotes-after.png`

Both ran on Hyprland 0.56.2, monitor DP-2, exclusively occupying empty Workspace 10 at settled geometry `[0,46]`, size `[2048,1106]` logical (dwindle full-workspace tiling), with: native Wayland platform; `QT_QPA_PLATFORMTHEME=qt6ct` over byte-identical disposable copies of the live qt6ct/LiquidGlass configuration (offscreen probe confirmed style chain `qt6ct-style → kvantum` and LiquidGlass base palette `(42,50,50,184)` before launch); independent disposable XDG data/cache roots, repositories, inboxes, and settings; each repository seeded via its own source tree's `NoteService` API with one identical three-line synthetic note (`Wayland rim A-B synthetic fixture.` / `Second line of the shared note body.` / `Third and final line for both versions.`); launch flags `--kitty-window-material --no-auto-receive --runtime-probe-ms 12000`.

### Actual runtime results observed

Both processes exited with status **0**. Both printed:
`RUNTIME_STYLE=qt6ct-style`, `RUNTIME_PLATFORM=wayland`, `RUNTIME_BLUR_ACTIVE=1`, empty `RUNTIME_BLUR_ERROR`, `RUNTIME_WINDOW_MATERIAL=kitty-equivalent`, `RUNTIME_PURGE_RELAY=disabled-for-probe`. Data roots were the per-version disposable directories under `/home/reason/Temporary/QwenProjects/rn-rim-ab-20261019/staging/run-A|B/`; no live notes, Android device, or global configuration was touched.

### Uncertainties and limits

- **No pixel comparison has been run in this shift.** Whether the rim is measurable at full resolution, whether card interiors show any pane-wide fill, whether broad wallpaper-derived patches persist/improve/worsen, and whether sidebar/editor controls remain visually intact are all open until someone inspects or measures these images. A screenshot is evidence, not owner visual approval.
- Supplementary raw-framebuffer grabs (in-process `QWidget::grab` of each version at 2560x1383 with identical settled geometry) exist **outside this repository** at `/home/reason/Temporary/QwenProjects/rn-rim-ab-20261019/staging/raw/raw-a.png` and `raw-b.png`, with geometry logs in the same directory's `probe-a.log` / `probe-b.log`. Both probes reported window size `[2048,1106]`, blur active without error, kitty-equivalent material, sidebar width 300, and one visible writing card at logical `(718,30)` size `920x1044` in both versions. These raw files are not committed here; they are referenced for the next reviewer's convenience only.
- The compositor screenshot path captures what Hyprland displayed on Workspace 10 (window plus top workspace label strip); wallpaper is present behind nothing because the window filled the entire workspace area, so A-vs-B pixel differences should be confined to renderer changes if the desktop background was static between captures (it was not independently verified).

## Previously reported tests (not rerun this shift)

From the rim implementation checkpoint: focused material tests **10/10 PASS**; complete unittest suite **237/237 OK** under explicitly restored `HOME`/`XDG_CONFIG_HOME`. Qualification preserved from that record: the full-suite command was piped through `... | tail -4`, so its standalone process exit code was never independently established (the recorded unittest output says OK). No tests were executed in this shift; no new code or tests were added.

## Remaining next action

1. Review and compare `reasonnotes-before.png` vs `reasonnotes-after.png` at original resolution (full-window diff plus close-ups around the writing-card boundary); optionally use the referenced raw grabs for compositor-independent isolation of the rim.
2. Obtain owner visual judgment on whether the rim improves depth without unwanted background artifacts. Then decide: keep, tune, or revert the rim; only after that do physical Android acceptance and separately authorized production cutover remain as final product gates.

## Prohibited-state confirmation

No production installation, no real notes or Android synchronization activity, no global Hyprland/Kitty/qt6ct/Kvantum modification, no writes in Forge's workspace, no default renderer change, no change to the proven `QColor(28,33,33,209)` sheet. The branch has not been merged into `main`.
