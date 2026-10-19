# ReasonNotes vertical glass artifact diagnosis — 2026-10-19

## Status

Owner testing of commit `81505699229c8930e5b7b540d234b8f5afd79687`
confirmed that the earlier horizontal quantization bands changed, but large
vertical patches remained. This is **NOT VISUALLY ACCEPTED**.

No product rendering code was changed in this investigation. The remaining
pattern was isolated to final desktop composition, and every available
application-side correction would cross an explicit visual or compositor
boundary. Making another speculative opacity or gradient change would not be
a root-cause fix.

## Controlled matrix

All captures used:

- the current Forge source and synthetic notes;
- disposable copies of the selected qt6ct and LiquidGlass configuration;
- native Wayland at the active 1.25 display scale;
- an exact 1280x820 logical window at `(384, 166)` unless noted;
- the same workspace, wallpaper, content, and `grim` capture path; and
- a raw `QWidget.render()` image from the same process.

The editor matrix changed one factor at a time:

1. current materials;
2. uniform GlassCard material;
3. uniform navigation-rail material;
4. both child gradients uniform;
5. each of the above with the application-specific background-effect request
   omitted while retaining the translucent Wayland surface.

Settings was captured with current and both-uniform child materials, with and
without the application blur request.

## Findings

### Qt child materials are not the source

The vertical regions remained in final editor and Settings captures when the
GlassCard gradient, navigation-rail gradient, or both were replaced by
uniform materials. The raw Qt images did not contain the reported pattern.
Across a blank lower section of the editor card, the raw framebuffer's
horizontal luminance delta was exactly zero.

### The application blur request is not the source

The Settings captures were pixel-identical with and without the application's
`ext-background-effect-v1` request for both current and both-uniform
materials. The both-uniform editor pair was also pixel-identical. Other editor
pairs differed only at transient cursor/caret pixels, not in material regions.

Every launch still used `qt6ct-style`, native `wayland`, an alpha-bearing
surface, and clean process shutdown. Blur-requested runs reported active blur
with no helper error; request-omitted runs remained translucent without
triggering the opaque fallback.

### The pattern follows screen/background coordinates

The current window was recaptured at logical x=100 instead of x=384, with all
other inputs unchanged. In the centered capture, strong vertical transitions
occurred at local physical x=612 and x=998. In the shifted capture, the same
transitions occurred at local x=967 and x=1353. Adding each capture's physical
screen origin places both pairs at the same global x=1092 and x=1478.

The window therefore moved across the pattern; the pattern did not move with
the Qt widgets. A wallpaper-only capture confirms the detailed background is
being transformed into broad low-frequency regions beneath the translucent
surface. This is final background/compositor presentation, not Qt gradient
quantization, backing-store damage, or overlap between translucent children.

The installed `ext-background-effect-v1` protocol permits the client to set a
surface-local blur region. It explicitly leaves the blur algorithm to
compositor policy. It provides no client control over sampling, tiling, blur
radius, passes, or background reconstruction.

## Evidence files

The captures remain in isolated `/tmp` roots and do not contain production
notes:

- `/tmp/reasonnotes-material-ab.OcdmkI/screen-editor-current.png`
  (`f03af2b8eb33fca06a118ec069f36e08d1f403f1b3de4f969667b7338a854c98`)
- `/tmp/reasonnotes-material-ab.OcdmkI/raw-editor-current.png`
  (`6295de5607f8b61646dbab7b834f33793cd2dff06b964486bf314f3777b34bd5`)
- `/tmp/reasonnotes-material-ab.OcdmkI/screen-editor-both-uniform.png`
  (`0fde063fae0c03bea9be14da3fdb34528843440b2819e04abb8341880b9de6e2`)
- `/tmp/reasonnotes-material-ab.OcdmkI/screen-settings-current.png`
  (`8f568c77c2463c14b1742a05cfafabaf9b6250a5bfb6ae0c73a5fa308d989c5a`)
- `/tmp/reasonnotes-material-ab.OcdmkI/wallpaper-centered.png`
  (`60c37d494c6d8bcc80197e2225fb275825a46cdd1a60bee83ecf9e18a9b9b53a`)
- `/tmp/reasonnotes-material-shifted.lwgpYG/screen-editor-current.png`
  (`99918224a29ca34ce4a08bea9044c5385fb1ea363e7a9649513e6256899b7cc5`)

## Decision required

Removing the visible background regions requires accepting one of these
tradeoffs:

1. Increase the top-level material density, reducing real background depth.
2. Reduce or disable compositor blur for this window, changing the accepted
   LiquidGlass behavior and requiring compositor policy outside the app.
3. Add an application-owned grain/texture mask. This may make the regions less
   noticeable but does not correct their source and departs from pure
   system-material rendering.
4. Accept the system compositor's background variation as part of genuine
   translucency.

The first three materially change the accepted appearance or a protected
system responsibility. Reason must select the tradeoff before implementation.

**INCOMPLETE — OWNER VISUAL DECISION REQUIRED.** Physical Android
interoperability and authorized production cutover also remain outstanding.
