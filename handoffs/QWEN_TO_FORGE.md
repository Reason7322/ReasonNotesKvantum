# Qwen → Forge Handoff — Kitty Glass Card-Rim Checkpoint (2026-10-19)

**Overall product: INCOMPLETE.** Deliver a fully functional, owner-visually-approved native Qt Widgets/Kvantum ReasonNotes replacement preserving familiar UI, editing, autosave/recovery, history, KDE Connect/Android sync, conflict/deletion handling, and English/Polish localization. Production replacement remains separately owner-authorized; physical Android acceptance and final visual approval are outstanding.

## Exact transfer state

- Qwen-owned worktree: `/home/reason/Temporary/QwenProjects/ReasonNotesKvantum-kitty-glass-refinement`
- Sender branch: `qwen/kitty-glass-refinement`
- Source/base SHA: `30bc0fe7ccd9bce6e0844876295f3e073fe9807f` (`forge/qtwidgets-rewrite` source state).
- Transfer commit: use the verified tip of this branch; the coordinator reports the identical full SHA of local HEAD, `handoff`, and `github` after both pushes. Do not treat this source/base SHA as the new handoff SHA.
- This handoff was recorded by ChatGPT at the owner's request, using Qwen's uncommitted implementation and the saved `Vision Sidequest v2` transcript/checkpoint; it is **not** a claim that Qwen itself executed the handoff.

## Implemented in this checkpoint

- `src/reasonnotes_widgets/material.py`: for `GlassCard` with material fill disabled, paint nine translucent rounded, clipped strokes that fade inward; keep card interiors fill-free and retain the existing top reflection.
- `tests/test_widgets_native_material.py`: four additional regression tests for exact unobstructed Kitty sheet RGBA `(28,33,33,209)`, transparent card interiors, localized visible rims, and preservation of default gradient cards.
- The experimental `--kitty-window-material` variant remains opt-in. Preserve the unchanged RGBA sheet and the custom default and `--native-window-material` variants.
- Prior Forge source-only Kitty equivalence work, screenshot evidence, and the original UI/behavior remain as established in `docs/KITTY_MATERIAL_REASONNOTES_VALIDATION_2026-10-19.md`.

## Evidence and limits

- ChatGPT verified the two-file implementation diff on 2026-10-19 and `git diff --check` reported no errors before this checkpoint.
- Saved Qwen chat reports focused 10/10 PASS and full unittest 237/237 OK, using `QT_QPA_PLATFORM=offscreen HOME=/home/reason XDG_CONFIG_HOME=/home/reason/.config PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests -q 2>&1 | tail -4`. These were **not rerun by ChatGPT**. Pipeline status can reflect `tail` unless `pipefail` is active; the recorded unittest text says OK. Nonfatal GC ResourceWarning at shutdown.
- LM Studio tool command environment omitted `HOME`, `XDG_CONFIG_HOME`, and `WAYLAND_DISPLAY`; missing Qt configuration caused an opaque fallback Kvantum palette `(46,46,46,255)` instead of the actual LiquidGlass base `(42,50,50,184)`. Supply the correct theme/session environment and isolate XDG *writes* when previewing.
- **No native Wayland A/B screenshots of this rim change, no owner visual approval, no new helper build, no new distributable build, no deployment, and no Android physical-device validation were verified.** Tests establish pixel-level constraints, not appearance acceptance.

## Exactly what remains

1. Check Hyprland Workspace 10 is unoccupied, then produce native Wayland, matched-geometry A/B captures from isolated source previews with disposable notes/settings and correct LiquidGlass theme. Build the native blur helper only if needed.
2. Assess card-rim depth and wallpaper-derived patches from actual captures; owner performs subjective visual approval. Do not claim wallpaper patches or visual depth are fixed on the basis of offscreen tests.
3. Continue the **same** full ReasonNotes product goal: owner visual acceptance, physical KDE Connect/Android interoperability, and separately authorized production cutover with rollback remain outstanding.

**Do not redo:** prior Forge Kitty pixel-equivalence research, source implementation, Qwen's reported green test run, or diagnosed Qt environment issue absent a concrete changed prerequisite or contradiction. No live production data, user notes, global Qt/Kvantum/Hyprland/Kitty settings, or installation may be changed under this handoff. This checkpoint is a transfer, not authorization to launch the app or load Qwen.
