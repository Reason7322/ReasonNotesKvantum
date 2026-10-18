# Forge visual recovery validation — 2026-10-18

## Scope

Recover the softer intermediate LiquidGlass direction without adopting the
later flat-charcoal regression. Backend, repository, history, synchronization,
receipt, conflict, and deletion semantics were intentionally left unchanged.

Incoming references:

- Forge baseline: `4665147d0e0c8b236c5c01a4009a6426a9cf8187`
- Sol continuation: `b4d2e04fa40d34239f781a788eb687f6412584bd`
- Preferred-direction Sol commits selectively integrated: `883ab2d`,
  `33c3af7`

## Rendering decisions

- Preserve the platform-installed `qt6ct-style` proxy when its base style is
  the real Qt 6 Kvantum style. Fall back to bare Kvantum only where qt6ct is
  absent or does not wrap Kvantum.
- Keep the earlier palette-derived `NavigationRail`, `GlassCard`,
  `SearchWell`, and `TitleRule` composition. These are low-alpha layout
  surfaces, not a bundled theme or replacement control style.
- Do not apply `QPalette.Base` autofill to the whole editor page. That later
  change was the principal source of the rejected opaque charcoal slab.
- Keep a palette-derived alpha-preserving top-level sheet. In the real
  compositor capture this restores visible material depth without turning the
  window into an unbounded wallpaper portal.
- Keep the sidebar command buttons inside a `GlassCard`; use system theme icons
  and native Kvantum tool-button behavior.
- Keep line edits and scroll viewports transparent. Their small proxy style
  suppresses only Kvantum's forced `PE_PanelLineEdit` fill and retains the
  active qt6ct-to-Kvantum chain for every other primitive and metric.
- Remove the Settings appearance explanation. Language contains only language
  controls. No Settings back button or full-width back bar exists; the
  permanent sidebar Settings button toggles the page.

## Automated evidence

Focused affected tests:

```text
QT_QPA_PLATFORM=offscreen PYTHONPATH=src \
  /usr/bin/python3 -m unittest \
  tests.test_widgets_bootstrap \
  tests.test_widgets_main_window \
  tests.test_widgets_visual_polish

Ran 21 tests in 2.768s — OK
```

Complete suite (with localhost socket access for purge-relay tests):

```text
QT_QPA_PLATFORM=offscreen PYTHONPATH=src \
  /usr/bin/python3 -m unittest discover -v

Ran 224 tests in 7.514s — OK
```

The first restricted-sandbox full run correctly failed five purge-relay tests
at socket creation with `PermissionError`; it also exposed one stale test that
assumed the top-level style name must be bare `kvantum`. The assertion now
walks the proxy chain and requires Kvantum at its base. The socket-enabled full
rerun passed all 224 tests.

## Actual Hyprland / Wayland evidence

The repository-local `scripts/preview-dolphin-style.zsh` launcher:

- resolves the Forge worktree dynamically;
- copies the currently selected qt6ct and Kvantum configuration into a new
  `/tmp/reasonnotes-kvantum-preview.*` tree;
- uses isolated candidate data, cache, repository, inbox, and received paths;
- never points at production notes or settings.

Observed from the source launch:

```text
Using system qt6ct and selected Kvantum theme: LiquidGlass
RUNTIME_STYLE=qt6ct-style
RUNTIME_PLATFORM=wayland
RUNTIME_BLUR_ACTIVE=1
RUNTIME_BLUR_ERROR=
RUNTIME_PURGE_RELAY=disabled-for-probe
```

Two clean 2048x1106 compositor captures were inspected on a workspace that
contained only the isolated candidate:

1. Editor: translucent background depth remained visible; the writing region
   was distinct and readable; command buttons remained grouped; title/search
   controls did not render as heavy independent dark boxes.
2. Settings: permanent sidebar present; Language and deletion pairing shown as
   separate translucent cards; no back button or appearance prose; read-only
   pairing values integrated with the card surface.

The Settings-only probe separately reported:

```text
SETTINGS_STYLE=qt6ct-style
SETTINGS_BLUR_ACTIVE=1
SETTINGS_BACK_BUTTON=0
```

### Native blur teardown correction

The first exact installed-candidate timed probe rendered correctly but exited
with status 139. The same result reproduced from source with both qt6ct and
bare Kvantum, while a Wayland launch without the native blur controller exited
normally. `coredumpctl` identified the fault in `free_blur()` at the
`wl_surface_commit` performed after destroying the effect.

Qt owns the `wl_surface` pointer borrowed by the helper and can destroy it
before `QApplication.aboutToQuit`. Cleanup therefore must not dereference or
commit that pointer. The helper now commits only during effect activation;
teardown destroys the effect, manager, registry, and private event queue and
flushes the still-live display. Surface destruction already discards pending
effect state.

A regression test asserts that the activation path retains its required
commit and the cleanup path contains none. After rebuilding the helper, a new
isolated Wayland source probe reported the same active qt6ct/Kvantum blur state
and exited with status 0. The complete 224-test suite passed after this fix.

The normal Qt/Kvantum runtime still emits pre-existing `QColor::set*F: invalid
value nan` diagnostics and missing inherited icon-theme warnings for
`Papirus-Dark` and `Cosmic`. System-icon fallbacks rendered correctly in the
captured candidate. These warnings were not introduced by the visual recovery.

## Protection and remaining acceptance

- Production launcher, installation, data, settings, and running production
  process were not modified.
- Global qt6ct, Kvantum, Hyprland, Kitty, Dolphin, and Noctalia configuration
  was not modified.
- No Android device operation or production migration occurred.
- The clean captures establish actual compositor behavior, not owner taste
  approval or exact visual identity with Dolphin.

Status: **ENGINEERING CANDIDATE — VISUAL ACCEPTANCE PENDING**.
