# ReasonNotesKvantum - Project Status

## Current milestone

Integrated release candidate on `forge/reasonnotes-completion`, based on
Qwen checkpoint `9374dce9d75b3c87002b3debe50a6eaf071bae62`. The sidebar
boundary/highlight corrections remain, and the rejected Sync UI has been
rebuilt as a focused right-side drawer with connected scope, inclusion,
status, and action hierarchy. The owner visually accepted the Sync redesign
on 2026-10-21. The left sidebar now has a fill-free New Note action, visible
palette-owned Save/Sync/Settings icons, Settings before the unchanged Delete
action, and a ReasonNotes stacked-page note glyph. Sidebar visual acceptance,
physical Android interoperability, and authorization for production
replacement remain pending.

## Implemented

- Native `QApplication`/`QMainWindow`/Qt Widgets shell with a resizable 300 px
  sidebar, responsive editor capped at a 920 px writing column, native search,
  selection, keyboard navigation, dialogs, Settings, Sync, and Conflict views.
- The system `qt6ct-style` proxy is preserved when it wraps the installed
  `kvantum` QStyle, matching Dolphin's native font, icon, palette, and style
  chain without changing or bundling system themes.
- Optional `ext-background-effect-v1` compositor blur on Qt's QWidget Wayland
  surface, including pre-show alpha preparation and an opaque fallback.
- Imported baseline application/sync logic with note CRUD, autosave/recovery,
  immutable history, Unicode search, F5 receive refresh, selective KDE Connect
  sync, receipts/retries, exact conflict resolution, and peer deletion purge.
- English and Polish native chrome, foreground purge pairing information, and
  application-scoped candidate settings.
- Versioned candidate packaging, immutable releases, candidate-only activation,
  and documented rollback. No production cutover has occurred.
- Deterministic offline physical-Android acceptance fixture with production
  path refusal, fixed Unicode/conflict/deletion notes, and zero transport
  attempts before the owner-authorized test.
- A current exact candidate was built and launched only under `/tmp`; any
  pre-existing user candidate installation was left unchanged and production
  remains selected.
- The Sync drawer keeps the existing all/selected semantics and asynchronous
  controller calls, while adding explicit scope controls, dense selectable
  note cards, contextual transfer/receipt wording, live status, and a
  prominent mode-aware action.
- The sidebar keeps its established note-list geometry and behavior while
  integrating New Note into the rail, making the Save/Sync/Settings glyphs
  deterministic and legible, moving Settings directly above Delete, and
  replacing the generic ordinary-note document icon with a branded stacked
  note glyph.

## Validation state

- Complete automated suite: 250 tests passed in an isolated offscreen run;
  localhost purge-relay tests were run with socket access enabled.
- Native helper: compiled successfully from the system Wayland protocol as
  part of a temporary immutable release.
- Actual Hyprland session: Qt platform `wayland`, style `qt6ct-style` over
  Kvantum, compositor blur active with no helper error, explicit
  Kitty-equivalent material, clean shutdown, and disposable `/tmp` data and
  configuration copies.
- The narrow correction package was launched again on Workspace 10. A selected
  Unicode note and hovered splitter were inspected at full resolution; an
  80×620 divider-region comparison found zero changed pixels between rest and
  hover. The dedicated title rule is absent. This remains evidence for—not a
  substitute for—owner visual acceptance.
- The packaged launcher reopened a byte-for-byte temporary copy of the current
  production-format repository: 187 immutable revisions, 6 live notes, and 16
  purge fences; the immutable-history hash was unchanged.
- Candidate-only rollback between two temporary immutable releases passed.
- Android/device mutation was not performed; protocol and KDE Connect behavior
  are covered by imported regression/integration tests. Owner device acceptance
  remains pending.
- The redesigned All-notes and Selected-notes states were rendered by the
  actual native Wayland source candidate on Workspace 10 with
  `qt6ct-style -> Kvantum`, active compositor blur, Kitty-equivalent
  material, and disposable synthetic data. Exact drawer surfaces are recorded
  in `docs/evidence/sync-redesign-2026-10-21/`.
- Reason visually accepted the redesigned Sync drawer on 2026-10-21.
- The refined sidebar was rendered in the actual native Wayland source
  candidate on Workspace 10 with `qt6ct-style -> Kvantum`, active compositor
  blur, Kitty-equivalent material, disposable synthetic notes, and the YAMIS
  icon theme exposed read-only. Exact captures are recorded in
  `docs/evidence/sidebar-refinement-2026-10-21/`; owner acceptance is pending.

See `docs/UI_CORRECTIONS_VALIDATION_2026-10-21.md`,
`docs/RELEASE_CANDIDATE_VALIDATION_2026-10-21.md`, and
`docs/SYNC_REDRAW_VALIDATION_2026-10-21.md`, and
`docs/SIDEBAR_REFINEMENT_VALIDATION_2026-10-21.md` for current hashes and
captures.
`docs/ANDROID_PHYSICAL_ACCEPTANCE.md` retains the later controlled device
sequence.

## Production state

The installed launcher, release, desktop entry, settings, Android app, and
`~/.local/share/ReasonNotes` data have not been replaced or migrated. The
candidate rejects production data paths.

## Current owner and next action

Forge owns the branch. The Sync redesign is visually accepted, and the sidebar
refinement is implemented and validated in the actual Wayland candidate. The
next action is owner visual review of the updated sidebar. Android testing and
production work remain stopped; do not begin either without explicit
direction. Production migration/cutover still requires physical device
acceptance and separate authorization.
Do not modify `main`, the installed candidate, production launcher/data, or the
phone without the applicable explicit authorization.

## ChatGPT-owned visual correction (2026-10-18)

Owner rejected the post-4665147 wallpaper-portal appearance. Separate branch
sol/qtwidgets-glass-balance adds a system-palette translucent backdrop and
removes the Settings back button. The sidebar Settings button toggles.
Full suite 222/222 passed; native Wayland/Kvantum/blur runtime verified.
No installed candidate or production files changed. Owner visual acceptance,
physical Android acceptance, and production cutover remain pending.
See docs/GLASS_BALANCE_VALIDATION.md.

## Second visual design iteration — 2026-10-18

Owner rejected the first flat-gray material pass. The current sol-owned
continuation adds real UI hierarchy using the active Kvantum palette:
NavigationRail, GlassCard editor/Settings, grouped action/search surfaces,
themed title rule, improved spacing, consistent iconography, and localized
Notes heading. It preserves the existing backend and removes all separate
Settings back navigation. Full suite 223/223 passed. Real Wayland/Kvantum
and compositor blur verified, with visual screenshots inspected using
disposable test notes and dummy pairing credentials.

**PRODUCT INCOMPLETE:** owner has not approved visuals; physical Android
interoperability and authorized production cutover are still pending. No
installed candidate or production files were changed during this iteration.
See docs/GLASS_BALANCE_VALIDATION.md and handoffs/SOL_TO_FORGE.md.

## Forge visual recovery — 2026-10-18

Forge selectively integrated Sol's preferred-direction layout composition and
the verified Dolphin-native qt6ct integration. The rejected editor-wide
`QPalette.Base` autofill and flat native-frame replacement were not imported.
The current source keeps the low-alpha writing/settings cards, grouped sidebar
commands, search surround, title rule, and system icons, while all colors are
derived from the active system palette. The Settings back bar and appearance
explanation remain absent.

The complete 224-test suite passes. Two unobstructed 2048x1106 Hyprland
captures (editor and Settings) were inspected from isolated source launches;
both reported `qt6ct-style`, native Wayland, active blur, and no blur error.
The editor capture visibly retained background depth and a distinct readable
writing panel; the Settings capture retained the sidebar and two translucent
cards without a back button.

An exact installed-candidate probe then exposed a pre-existing exit-time
SIGSEGV in the native blur helper. Coredump evidence traced it to a cleanup
commit on Qt's already-destroyed borrowed `wl_surface`. Cleanup no longer
commits that surface; activation still does. The corrected source Wayland
probe exits normally with status 0 while retaining active blur.

**ENGINEERING CANDIDATE — VISUAL ACCEPTANCE PENDING.** Physical Android
interoperability and production cutover remain pending. No production data,
launcher, theme, compositor configuration, or Android state was changed.
See `docs/VISUAL_RECOVERY_VALIDATION_2026-10-18.md`.

## Forge production-UI parity restoration — 2026-10-18

The native sidebar now restores the installed ReasonNotes hierarchy: split
branding, a full-width primary New Note action, vertical secondary actions,
prominent search, icon-bearing note rows, bottom Settings navigation, and
grouped status. The editor retains the recovered glass card while restoring
the original title/body scale and top-right Local/Phone status. Long titles
open at their beginning. No Settings back control exists.

Affected coverage passes 27/27 and the complete suite passes 226/226. Actual
isolated Hyprland captures at wide and 1280x820 sizes retained `qt6ct-style`,
native Wayland, active blur, and readable translucent material. The previous
installed candidate and all production state remain unchanged.

**ENGINEERING CANDIDATE — UI VISUAL ACCEPTANCE PENDING.** Physical Android
interoperability and production cutover remain pending. See
`docs/UI_PARITY_VALIDATION_2026-10-18.md`.

## Forge glass artifact correction — 2026-10-18

The alpha-floor attempt in commit `8eb91e1` **FAILED VISUAL ACCEPTANCE**. Its
test covered opacity, not the reported rectangular pattern.

A controlled blur/no-blur/raw-framebuffer A/B then located the pattern in the
Qt-painted surface before compositor processing. The shallow window-sized
gradient produced 44 long identical-color runs through 8-bit quantization.
The top-level material is now a uniform palette-derived translucent sheet at
the original alpha factor; local cards and the navigation rail still supply
depth, so the accepted UI hierarchy and compositor blur are unchanged.

The replacement rendering regression fails on the rejected gradient and
passes on the corrected material. Affected visual/main-window coverage passes
17/17 and the complete isolated suite passes 227/227. Matching 1280x820 editor
and Settings captures from the patched source retained `qt6ct-style`, native
Wayland, active blur, and no blur-helper error; the repeated bands were absent
in full-resolution inspection. Production and the installed candidate remain
unchanged. Owner validation is still required.

**ENGINEERING CANDIDATE — UI VISUAL ACCEPTANCE PENDING.** Physical Android
interoperability and production cutover remain pending. See
`docs/GLASS_ARTIFACT_VALIDATION_2026-10-18.md`.

## Remaining vertical glass artifacts — 2026-10-19

Owner testing of `8150569` found that the horizontal quantization changed but
large vertical patches remained. The candidate is **NOT VISUALLY ACCEPTED**.

A controlled multi-factor Wayland matrix compared current, uniform GlassCard,
uniform navigation rail, and both-uniform materials, each with and without the
application blur request. Raw Qt framebuffers and final compositor captures
were collected at identical 1280x820 geometry for editor and Settings views.

The vertical regions remained after both child gradients were removed and did
not exist in the raw Qt framebuffer. Blur-requested and request-omitted
Settings captures were pixel-identical. Moving the whole window by 284 logical
pixels moved the regions within the window while their strongest transitions
remained at physical screen x=1092 and x=1478. The remaining effect is the
desktop background/compositor result showing through the correctly
translucent surface, not a Qt paint layer or child overlap.

No product code was changed. The Wayland protocol exposes only a blur region
and leaves the algorithm to compositor policy. Removing the remaining regions
would require an owner decision to trade away material density, blur behavior,
or pure system-material rendering. Production, installed candidate, Android,
and global desktop configuration remain unchanged.

**INCOMPLETE — OWNER VISUAL DECISION REQUIRED.** The unchanged final goal is
a complete, functional, visually accepted native Qt Widgets/Kvantum
replacement. Physical Android interoperability and authorized production
cutover also remain outstanding. See
`docs/VERTICAL_GLASS_ARTIFACT_DIAGNOSIS_2026-10-19.md`.

## Original-renderer controlled comparison — 2026-10-19

The installed Qt Quick application and current Widgets source were captured on
empty Hyprland Workspace 10 with identical synthetic notes, theme copies,
window geometry, position, and screenshot method. The original ran with the
Fusion Qt Quick Controls style and its explicit Noctalia-derived material; the
candidate retained `qt6ct-style → Kvantum`. Both used native Wayland and active
compositor blur.

The original raw editor is one uniform alpha-184 sheet. The current Widgets
card is alpha 192–195 over its shared window material. In the same blank editor
region, current Widgets reduced broad horizontal luminance variation to 12.320
from the original's 14.143.

A temporary Widgets probe reproduced the original continuous sheet, sidebar
tint, and transparent card fill. Its raw alpha and final compositor variation
matched the original exactly, with only a one-level blue-channel rounding
difference. This proves that Qt Quick versus Widgets rendering is not the
source of the desktop-coordinate regions. Promoting the probe would strengthen
the reported variation and weaken the approved writing-surface depth, so no
product rendering code was changed.

Full-resolution matched, raw, and side-by-side evidence is committed under
`docs/evidence/original-glass-comparison-2026-10-19/`.

**INCOMPLETE — OWNER VISUAL DECISION REQUIRED.** The unchanged final goal is
a complete, functional, visually accepted native Qt Widgets/Kvantum
replacement. Owner visual acceptance, physical Android interoperability, and
authorized production cutover remain outstanding. See
`docs/ORIGINAL_GLASS_RENDERING_COMPARISON_2026-10-19.md`.

## Native Kvantum window-material experiment — 2026-10-19

A reversible source-only variant now explicitly delegates the complete
top-level window sheet to the active `qt6ct-style → Kvantum` chain. This was
necessary because removing the custom paint event does not itself make Qt draw
Kvantum's `PE_Widget` primitive. The accepted custom path remains the default;
the experimental path is available only through the hidden
`--native-window-material` switch.

Matched isolated Hyprland captures showed that the native path raises the
effective blank-editor alpha from mean `193.524` to `239.703`. Broad
composited column variation falls from range `10.461` to `2.668`, but the
result is an almost opaque charcoal surface with materially less LiquidGlass
depth. It hides the wallpaper-derived patches through density rather than
providing a smoother translucent material, and it is visibly flatter than the
existing Kitty optical reference.

Focused native-material tests pass 2/2, affected Widgets coverage passes
31/31, and the complete suite passes 229/229 with the localhost socket access
required by the purge-relay tests. Both source variants ran on native Wayland
with `qt6ct-style`, active blur, no blur-helper error, and clean exit. No
candidate installation, production data, Android state, or global desktop
configuration was changed.

**ENGINEERING EXPERIMENT COMPLETE — OWNER VISUAL ACCEPTANCE PENDING.** The
unchanged final goal remains a complete, functional, visually accepted native
Qt Widgets/Kvantum replacement. Physical Android interoperability and
authorized production cutover also remain outstanding. See
`docs/NATIVE_KVANTUM_MATERIAL_EXPERIMENT_2026-10-19.md`.

## Kitty / Qt glass equivalence experiment — 2026-10-19

A disposable plain `QWidget` submitted a uniform `#1C2121` framebuffer at
alpha 209, matching Kitty's active color and 0.82 opacity. At identical
Workspace 10 geometry, all 1,245,600 pixels in the common 80 px inset were
byte-for-byte identical between the final Kitty and Qt captures. Every Qt raw
framebuffer pixel was exactly `(28, 33, 33, 209)`.

The normal full-window residual is confined to Kitty's configured client-side
edge shader and cursor. Disabling that shader through a disposable config copy
removed the perimeter residual. Qt captures with and without the ReasonNotes
background-effect request were byte-identical, so the request is not the
source of the appearance difference under the active Hyprland blur policy.

The evidence supports a next, owner-gated ReasonNotes A/B variant: one
continuous `QColor(28, 33, 33, 209)` top-level sheet, no native Kvantum
`PE_Widget` background, and pane-sized translucent fills bypassed while the
accepted layout and controls remain unchanged. This mission did not apply that
change. No application source, production state, global configuration, build,
installation, or deployment changed.

**EXPERIMENT COMPLETE — OWNER DECISION REQUIRED BEFORE REASONNOTES CHANGES.**
The unchanged final goal remains a complete, functional, visually accepted
native Qt Widgets/Kvantum replacement. Physical Android interoperability and
authorized production cutover remain outstanding. See
`docs/KITTY_QT_GLASS_EQUIVALENCE_2026-10-19.md`.

## Kitty-equivalent ReasonNotes variant — 2026-10-19

A reversible source-only --kitty-window-material mode now uses the measured Kitty QColor(28,33,33,209) top-level sheet, suppressing pane-sized rail/card fills in that mode only while preserving the default UI, controls and existing native-material diagnostic. Six focused tests and the 233-test suite passed; both source variants ran and exited normally on actual Wayland/Kvantum with disposable Workspace 10 preview data. Full-resolution comparison is retained in docs/evidence/kitty-reasonnotes-material-2026-10-19, report docs/KITTY_MATERIAL_REASONNOTES_VALIDATION_2026-10-19.md.

The experimental variant is visibly darker/flatter and still shows broad underlying background regions. OWNER VISUAL ACCEPTANCE NOT GRANTED. No build, candidate or production deployment, Android activity, or global theme/Hyprland change occurred. PRODUCT INCOMPLETE; physical Android interoperability and separately authorized cutover remain pending. Next action is owner evaluation of the new A/B and a bounded visual refinement decision, not automatic promotion.

## Qwen Vision Sidequest v2 card-rim checkpoint — 2026-10-19

**PRODUCT INCOMPLETE.** The unchanged deliverable is a complete, visually accepted native Qt Widgets/Kvantum ReasonNotes replacement with editing, autosave/recovery, history, KDE Connect/Android sync, conflict/deletion handling, and English/Polish localization; authorized production cutover and physical Android verification remain pending.

On `qwen/kitty-glass-refinement` from base `30bc0fe7ccd9bce6e0844876295f3e073fe9807f`, Qwen implemented a localized, nine-stroke, inward-fading rim only when Kitty-mode cards have disabled fills, plus four pixel regression tests. The top-level sheet must remain `QColor(28,33,33,209)`; no card interior fill, UI redesign, default-mode change, global settings change, or production install was performed.

Recorded Qwen results: 10/10 focused tests PASS, 237/237 complete unittest `OK` under explicitly restored HOME/XDG configuration. These outputs were not rerun by the coordinator; the `... | tail -4` pipeline did not separately establish unittest exit status. LM Studio's absent HOME/XDG_CONFIG_HOME caused Kvantum's wrong opaque fallback palette; the actual LiquidGlass theme's base was `(42,50,50,184)`.

**Not yet verified:** native Wayland screenshot A/B for the new rim, subjective visual acceptance, wallpaper patch improvement, helper/distributable build for this iteration, physical Android runtime, and production cutover. Next action: check Workspace 10 vacancy, run isolated native Wayland A/B previews with correct Qt environment and disposable settings/data, capture matching screenshots and seek owner visual judgment. Preserve previous Forge Kitty-equivalence findings; do not repeat established tests without cause. See `handoffs/QWEN_TO_FORGE.md`. This is a source/Git checkpoint, not completion of the current visual mission or the overall product.

## Mission 02 — native Wayland A/B capture checkpoint — 2026-10-20

Both required A/B screenshots were captured on actual native Wayland (Hyprland 0.56.2, monitor DP-2, Workspace 10) and are preserved at original resolution in `docs/evidence/kitty-rim-wayland-ab/`:

- `reasonnotes-before.png` — version A, the original Kitty-material build from base checkpoint `30bc0fe7ccd9bce6e0844876295f3e073fe9807f`, exported to a separate Qwen-owned source tree (`/home/reason/Temporary/QwenProjects/rn-rim-ab-20261019/staging/srcA`), no rim code.
- `reasonnotes-after.png` — version B, the current rim checkpoint `459367402ee3c251e55660121d763d821b85233e` from this branch.

Matched conditions for both runs: native Wayland platform, `QT_QPA_PLATFORMTHEME=qt6ct` with byte-identical disposable copies of the live qt6ct/LiquidGlass configuration (Kvantum base palette `(42,50,50,184)` verified by offscreen probe), independent disposable XDG data/cache/repository/inbox/settings trees seeded through each tree's own `NoteService` API with one identical three-line synthetic note, `--kitty-window-material --no-auto-receive`, runtime-probe mode (foreground purge relay disabled, no device sync). Both windows settled at the full Workspace 10 area `[0,46]`, size `[2048,1106]` logical; both reported `RUNTIME_STYLE=qt6ct-style`, `RUNTIME_PLATFORM=wayland`, `RUNTIME_BLUR_ACTIVE=1` with no blur error, `RUNTIME_WINDOW_MATERIAL=kitty-equivalent`, and exited cleanly with status 0. Captures are full-resolution `grim -o DP-2` compositor screenshots (2560x1440 RGB) taken while the windows occupied Workspace 10 exclusively.

Supplementary raw-framebuffer grabs of both versions exist from in-process probes at `/home/reason/Temporary/QwenProjects/rn-rim-ab-20261019/staging/raw/raw-a.png` and `raw-b.png` (2560x1383, with per-card geometry logs `probe-a.log`, `probe-b.log`). They are outside this repository on purpose: this checkpoint commits only the two composited screenshots. No pixel comparison has been run in this shift; the measurable rim effect, card-interior fill-free status, and wallpaper-patch persistence remain to be assessed from these images.

**VISUAL MILESTONE EVIDENCE CAPTURED — NOT OWNER-ACCEPTED.** Product remains INCOMPLETE: owner visual judgment of the A/B, physical Android interoperability, and authorized production cutover are still outstanding. No candidate or production state was modified; nothing was deployed.

## Mission 03 — editor UI cleanup checkpoint — 2026-10-20 (INCOMPLETE)

Owner requested four corrections: (1) remove the top-right Local/Phone status block from the writing card, (2) sidebar splitter handle invisible until hovered while staying draggable with persisted width, (3) empty-title placeholder `Title` / Polish `Tytuł`, remove `Start writing…` entirely, separator immediately below the title, (4) editable note-body surface uniformly opaque `#2C3539` without touching surrounding glass, Kitty sheet `QColor(28,33,33,209)`, or the approved rim.

Status at this checkpoint:

1. **Editor header status block — DONE (source + test).** `EditorPage` no longer creates `status_bar`/`save_status`/`delivery_status`; `_refresh_status()` only updates the sidebar Local/Phone pair from the same controller events (autosave, sync message/error paths unchanged). Regression: `test_editor_title_rule_body_hierarchy_without_header_status` green.
2. **Splitter hover-only — PARTIAL / CURRENT STATE REGRESSES 8 ASSERTIONS.** The committed source uses a scoped `QSplitter::handle:horizontal` stylesheet on `main_splitter`, which demonstrably corrupts the subtree style integration under qt6ct/Kvantum (line-edit proxies replaced, frames re-enabled). See `handoffs/QWEN_TO_FORGE.md` for the evidenced root cause and the identified replacement mechanism. Not owner-visible; must not be accepted as-is.
3. **Title area — DONE (source + test).** i18n key `title_placeholder` (`Title`/`Tytuł`) replaces `untitled`; `start_writing` removed from both catalogs; body placeholder forced to `""` in `retranslate()`; title→rule→body are contiguous layout items. EN and PL assertions green in the isolated run.
4. **Solid writing surface — DONE (source + offscreen pixel test).** New `visuals.integrate_solid_surface()` sets opaque `QColor(0x2C,0x35,0x39)` Base on the body editor/viewport with NoFrame; `test_note_body_is_one_uniform_opaque_solid_surface` renders the widget and asserts an exact `#2C3539` grid. Kitty sheet pixel tests and rim tests unchanged and green.

Test evidence (this shift): four suites run under `QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME=qt6ct` with byte-identical disposable qt6ct/LiquidGlass copies in a Qwen-owned isolated HOME/XDG (`tests.test_widgets_main_window tests.test_widgets_visual_polish tests.test_widgets_i18n tests.test_widgets_native_material`) → **33 ran, 9 failures**, all inside the splitter-QSS fallout: my new handle-count assertion (two `QSplitterHandle` children exist; selection must target the sidebar-boundary one) plus the pre-existing proxy-chain and frame-state assertions broken by the stylesheet wrap. Everything else in those suites passed, including autosave/persistence/shortcuts, i18n EN↔PL placeholders with saved titles intact, native/Kitty material and rim pixel tests. A bare offscreen run without qt6ct additionally fails unrelated palette assertions (opaque Base) — that environment is not the valid recipe; the disposable qt6ct/LiquidGlass setup above is.

No build or packaging change, no Wayland runtime validation, no screenshot this shift, nothing installed or deployed, production and live configuration untouched. **PRODUCT INCOMPLETE.** Next action: replace the splitter QSS with the evidenced palette-clear + `CE_Splitter` proxy mechanism (details in the handoff) until all four suites are green in that environment; then the owner's Workspace 10 screenshot review.

## Mission 04 — splitter QSS regression restore checkpoint — 2026-10-20

Source-only fix on `qwen/kitty-glass-refinement` (this work built from base checkpoint `c2078f54`). Removed from `src/reasonnotes_widgets/main_window.py`: the scoped `QSplitter::handle:horizontal` stylesheet on `main_splitter`, its comment, and the grip/hover-color assignments added for it (plus their dedicated `QPalette` import). This reverts Mission 03 item 2's "regresses 8 assertions" state at source level. The splitter itself, widget order, stretch factors, collapsible flag, width persistence, and all other styling are unchanged. No hover-only handle behavior was implemented in this mission.

Test evidence (this shift): under the established isolated recipe (`QT_QPA_PLATFORM=offscreen`, `QT_QPA_PLATFORMTHEME=qt6ct`, Qwen-owned disposable qt6ct/LiquidGlass env), the two focused methods holding Mission 03's eight failing frame/proxy assertions pass: `WidgetsVisualPolishTests.test_writing_search_and_list_surfaces_reveal_kvantum_window_material` and `.test_line_edit_proxy_suppresses_only_the_forced_kvantum_panel` → Ran 2 tests, OK. `git diff --check` clean. The three already-passing editor improvements (header status removal, EN/PL `Title`/`Tytuł` placeholders, opaque `#2C3539` body surface) are untouched by this diff and their regression coverage remains in the suite.

Outstanding: Mission 03 item 2's hover-only handle is still unimplemented — `test_sidebar_splitter_handle_is_hover_only_and_still_resizable` may fail; its evidenced replacement mechanism (transparent-palette boundary `QSplitterHandle` plus a narrow `QProxyStyle` suppressing/painting only `CE_Splitter`) remains the next source change per handoff. **PRODUCT INCOMPLETE.** No deployment; no production, live configuration, or Android changes this shift.

## Mission 05 — transparent idle splitter handle checkpoint — 2026-10-20

One bounded behavior on `qwen/kitty-glass-refinement` (built from base checkpoint `4b32047`). The actual sidebar/content boundary handle `main_splitter.handle(1)` is now transparent at rest: its idle Base, Window, AlternateBase, and Button palette roles are cleared for all color groups in `src/reasonnotes_widgets/main_window.py`, exactly the previously evidenced mechanism. No stylesheet, no style proxy, no QSplitterHandle subclass; the handle stays fully draggable and persisted-width behavior is untouched.

Test update: `tests/test_widgets_main_window.py` now selects `main_splitter.handle(1)` directly (verified non-null with usable dimensions), drops the obsolete findChildren count and stylesheet-string assertions, keeps the idle alpha pixel grid, and delivers synthetic press/move/release to the handle in handle-local coordinates. Method renamed to `test_sidebar_splitter_handle_is_transparent_at_rest_and_still_resizable`; the hover appearance deliberately has no assertion here and must receive its own test in a later mission.

Test evidence (this shift): isolated offscreen/qt6ct recipe, three selected methods → Ran 3 tests, OK — unhovered handle renders alpha 0 across its width, synthetic drag still grows the sidebar by ~42 px (asserted ≥ +30), and both repaired Kvantum styling methods remain green. `git diff --check` clean; only the two named files changed.

Outstanding: hover artwork for the boundary handle is not implemented in this mission — the evidenced narrow `QProxyStyle` `CE_Splitter` path (plus its open per-handle identity verification and a dedicated hover test) remains the next source change. **PRODUCT INCOMPLETE.** No deployment; no production, live configuration, or Android changes this shift.

## Mission 06 — sidebar handle hover grip checkpoint — 2026-10-20

One behavior on `qwen/kitty-glass-refinement` (built from base checkpoint `c8fe33c`). The sidebar/content divider now shows a small three-dot grip when the pointer is over `main_splitter.handle(1)` and is completely transparent again after leave. Implemented with a narrowly scoped `_BoundaryGripStyle(QProxyStyle)` installed only on `main_splitter`: it intercepts `CE_Splitter` solely while the boundary handle's paint dispatch is in progress (per-call identity via an eventFilter tracking which splitter handle's QPaintEvent is being dispatched), paints three palette-derived dots when `handle.underMouse()`, and nothing otherwise; every other control element/primitive delegates to the base chain unchanged. No stylesheet, no QSplitterHandle subclass; Mission 05's palette clear retained; dragging and width persistence untouched.

Hover-signal evidence (isolated offscreen probe): `CE_Splitter` opt.state never carries per-handle MouseOver in this stack; `painter.window()` is unreliable in this PySide6 build; synthetic mouse moves toggle the handle's `underMouse()` correctly and clear it on leave — so grip visibility reads `handle.underMouse()`, with live input additionally triggering immediate repaint via mouse tracking + Enter/Leave → update().

Test: new `test_sidebar_splitter_grip_appears_on_hover_and_disappears_on_leave` drives synthetic enter/leave on the real boundary handle, renders it, and asserts visible non-transparent grip pixels only when hovered (small, centered; edges transparent) and full transparency after leave. The Mission 05 idle/drag test is unchanged and still passes.

Test evidence (this shift): isolated offscreen/qt6ct recipe, four selected methods → Ran 4 tests, OK, process exit 0. Ad-hoc chain check: `main_splitter.style()` = `_BoundaryGripStyle` → `QProxyStyle(qt6ct-style)` → Kvantum leaf, i.e., the same Kvantum-terminating chain as before; rendered hovered state shows three ~4px dots centered vertically on the 7×850 divider.

Defect found and fixed during verification: constructing a QProxyStyle subclass with an actual QStyle *instance* base (instead of by style name, as `visuals.integrate_line_edit` does) segfaulted this PySide6/Python 3.14 build at interpreter exit (exit 139 after all tests OK; baseline c8fe33c control exited 0). Switching the base to resolve via `style().objectName()` — mirroring `integrate_line_edit` exactly (name-based base, `setParent(owner)`, retained attribute) — restored clean termination. Four tests plus construction probes then exit 0.

Outstanding: owner's Workspace 10 screenshot review of the combined Mission 03+05+06 state, physical Android validation, and separately authorized production cutover. **PRODUCT INCOMPLETE.** No deployment this shift; no production or live configuration change, no Android activity.

## Forge integrated completion-readiness checkpoint — 2026-10-21

Forge received Qwen's clean checkpoint `9374dce9d75b3c87002b3debe50a6eaf071bae62`
into `forge/reasonnotes-completion` and preserved all Mission 03/05/06 UI work.
The integrated suite passes 243/243 with localhost access for the isolated
foreground-purge tests.

A new offline-only Android acceptance utility creates deterministic Unicode,
conflict, and deletion notes under an explicit disposable root. It refuses
production and non-empty targets and records pending delivery intent with zero
attempts; it never contacts KDE Connect or Android. The remaining physical
sequence is documented in `docs/ANDROID_PHYSICAL_ACCEPTANCE.md`.

The exact Forge source was compiled and installed under `/tmp` as an immutable
candidate. Packaged `--check-launch`, two-release rollback, and existing-format
compatibility on a byte-for-byte temporary production-data copy all passed.
The copied immutable history was unchanged after candidate startup.

On actual Hyprland Workspace 10, the temporary package reported native
Wayland, `qt6ct-style -> kvantum`, blur active, no helper error, explicit
Kitty-equivalent material, and clean exit. Full-resolution captures of the
empty editor, selected Unicode note, Settings, and splitter hover are committed
under `docs/evidence/release-candidate-2026-10-21/` and were inspected at
original resolution. Workspace 1 was restored and Workspace 10 left empty.

No installed candidate, production launcher/release/data, Android state,
KDE Connect state, or global desktop/theme configuration changed. Production
launcher and data hashes remained stable.

**ENGINEERING CANDIDATE READY — FINAL ACCEPTANCE PENDING.** Product completion
still requires Reason's visual acceptance and renderer-default decision,
physical Android interoperability using the disposable fixture, and separately
authorized production migration/cutover/rollback verification.

## Forge narrow UI correction — 2026-10-21

Starting from verified Forge checkpoint
`eea23049762fb54ddd53c5f2479473bf7344308b`, only the two owner-requested UI
changes were made. The real sidebar splitter handle and its drag/persistence
behavior remain, but its scoped style now paints no `CE_Splitter` artwork at
rest or on hover. The editor no longer constructs or inserts `TitleRule`, so
there is no dedicated horizontal separator below the title. Fonts, Settings,
backend behavior, and material composition were not changed.

The two focused regressions pass, the four affected Widgets suites pass 34/34,
and the complete isolated suite passes 243/243. A SHA-named package was built
only under `/tmp` and ran on native Wayland with `qt6ct-style -> Kvantum`, blur
active, no helper error, Kitty-equivalent material, and clean shutdown. The
rest/hover divider crops have zero differing pixels, and the title-rule crop
shows the requested removal. See
`docs/UI_CORRECTIONS_VALIDATION_2026-10-21.md` and
`docs/evidence/ui-corrections-2026-10-21/`.

Nothing was deployed. Production, the installed candidate, Android, KDE
Connect state, and global desktop/theme configuration remain untouched.
**ENGINEERING CANDIDATE — UI VISUAL ACCEPTANCE PENDING.** Android testing and
production cutover remain explicitly unauthorized at this checkpoint.
