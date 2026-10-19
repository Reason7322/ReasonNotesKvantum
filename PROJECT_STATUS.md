# ReasonNotesKvantum - Project Status

## Current milestone

UI-parity engineering candidate implemented on `forge/qtwidgets-rewrite`;
owner visual acceptance and authorization for production replacement remain
pending.

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
- The reviewed candidate is installed at candidate-only paths with launcher
  `~/.local/bin/reasonnotes-kvantum-candidate`; production remains selected.

## Validation state

- Complete automated suite: 226 tests passed in an isolated offscreen run;
  localhost purge-relay tests were run with socket access enabled.
- Native helper: compiled successfully from the system Wayland protocol.
- Actual Hyprland session: Qt platform `wayland`, style `qt6ct-style` over
  Kvantum, compositor blur active with no helper error, using disposable
  `/tmp` data and configuration copies.
- Composited screenshot inspected after correcting the responsive writing
  column. It is evidence of the observed candidate, not owner visual approval
  or a claim of identity with Dolphin.
- Android/device mutation was not performed; protocol and KDE Connect behavior
  are covered by imported regression/integration tests. Owner device acceptance
  remains pending.

See `docs/VALIDATION.md` for commands, hashes, and separated evidence classes.

## Production state

The installed launcher, release, desktop entry, settings, Android app, and
`~/.local/share/ReasonNotes` data have not been replaced or migrated. The
candidate rejects production data paths.

## Current owner and next action

Forge owns the branch. The whole-branch review's six Important findings were
fixed through interaction-level RED/GREEN tests and the full suite is green.
The next action is owner visual/device acceptance through the candidate
launcher. Do not modify `main` or the production launcher without explicit
owner authorization.

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
