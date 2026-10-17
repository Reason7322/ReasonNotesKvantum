# ReasonNotes Qt Widgets and System Kvantum Rewrite Design

## Purpose

ReasonNotesKvantum replaces the Fedora Qt Quick interface with a production-ready
native Qt Widgets application while retaining the existing immutable repository,
note service, presenter, KDE Connect transport, receipt lifecycle, deletion
semantics, conflict handling, and Android protocol compatibility.

The existing installed ReasonNotes remains the production application until the
owner explicitly authorizes cutover. Development and acceptance use a separate
candidate launcher, data root, configuration root, and desktop identity.

## System theme ownership

ReasonNotes uses the installed Qt 6 `kvantum` QStyle and inherits the theme selected
by the user's existing Kvantum configuration. It does not bundle, copy, generate,
fork, select, or modify any Kvantum theme. It does not provide application-owned
White, Dark, or LiquidGlass modes. A system theme change is picked up on the next
application launch.

The application uses ordinary widgets and layouts with no broad QSS skin. Small
application-specific adjustments are permitted only for layout, typography,
semantic status, and transparent-window fallback behavior; Kvantum remains
responsible for material rendering, hover, selection, focus, controls, frames,
scrollbars, and splitters.

## Application architecture

The executable constructs a `QApplication`, verifies that the installed `kvantum`
style can be activated, then creates a `ReasonNotesMainWindow`. `NoteService` and
`NotePresenter` remain the presentation-independent application core. A new
`WidgetsController` exposes typed Qt signals and methods to Widgets without QML
properties or QML-specific list models.

The window contains:

- a `QMainWindow` shell and persisted native window geometry;
- a horizontal `QSplitter` with a permanent sidebar initially 300 pixels wide;
- a sidebar toolbar, Unicode search field, and `QListView` note catalogue;
- a central `QStackedWidget` for empty, editor, settings, and conflict pages;
- an editable `QLineEdit` title and `QPlainTextEdit` Markdown body;
- an approximately 920-pixel preferred writing column centered when space allows;
- a native, edge-attached synchronization panel with all/selected modes;
- native confirmation and error dialogs.

The note model provides display text, plain-text preview, note identity, conflict,
delivery, and bulk-selection roles. The model and controller use targeted updates;
typing never traverses immutable history or rebuilds note catalogues.

## Draft and note behavior

Editing restarts a 500 ms single-shot autosave timer. Save, note switching, sync,
and window close flush the active draft. Failed or stale saves retain the exact
draft and block the action that required the flush. Clean saves do not create
revisions. A blank initial editor remains unpersisted until non-empty user content
exists.

Normal click selects a note and clears bulk selection. Ctrl-click and Shift-click
support bulk selection without changing durable state. Deletion snapshots exact
note IDs before confirmation, creates the established local tombstones/purge state,
and never expands because the view changes while the dialog is open.

Search remains Unicode-normalized and case-insensitive through `NoteService`.
F5 scans incoming files asynchronously without initiating outgoing transfers and
does not replace a dirty draft.

## Synchronization and conflicts

The synchronization panel uses the existing independent sync catalogue and lets
the user choose all notes or explicit note IDs. Opening it has no transport side
effects. Transfer requested, durable import, receipt queued, and confirmed states
remain distinct. All network and inbox work runs outside the GUI thread.

Conflicted notes open a dedicated page showing full immutable candidates with
origin, revision identity, deletion state, and complete body. Resolution uses the
existing stale-head check. Skip writes nothing, and stale choices refresh rather
than overwriting concurrent history.

## Language and accessibility

English and Polish chrome remain supported through a Python translation catalogue.
The language preference is stored in candidate-specific `QSettings`; user-authored
Markdown is never translated. Controls use labels, buddies, shortcuts, accessible
names, visible focus, and standard keyboard navigation.

## Candidate isolation and packaging

The candidate defaults to `~/.local/share/ReasonNotesKvantum-candidate`, never
`~/.local/share/ReasonNotes`. Tests always supply temporary data, configuration,
inbox, and received-file roots. The candidate executable and desktop entry use a
distinct name and application ID. Explicit command-line roots remain available for
fixtures and a future owner-authorized cutover.

The source installer creates versioned candidate releases and refuses to overwrite
existing releases. It does not alter the production executable, desktop entry,
settings, release directory, or note store.

## Transparency and Wayland blur

Before constructing the top-level widget, the application requests a translucent
native surface when the active Kvantum theme requires it. The existing
`ext-background-effect-v1` helper is adapted to the QWidget's top-level
`wl_surface`, using Qt's own Wayland connection and an explicit initial surface
commit. Blur is optional and reversible. Unsupported platforms or helper failures
use an opaque, readable palette fallback without changing compositor settings.

Headless tests establish surface flags, helper lifecycle, and fallback. A real
Hyprland launch against disposable data establishes QStyle activation, surface
creation, and blur-helper state. Screenshots and owner observation remain the
authority for subjective appearance.

## Validation and completion

Existing backend regression tests are retained. New tests exercise actual widgets
offscreen: system-style activation, isolation, splitter persistence, editor and
autosave behavior, search, keyboard navigation, bulk deletion, F5, language,
sync selection, conflicts, focus, error retention, and packaging. Runtime evidence
distinguishes source tests, headless widget tests, Wayland launch, observed blur,
and owner visual acceptance.

Engineering completion requires a runnable candidate, full functional parity,
passing regression coverage, real Kvantum style activation, correct fallback,
safe candidate packaging, and cutover/rollback documentation. Until owner visual
acceptance and production authorization, status is `ENGINEERING CANDIDATE READY —
FINAL ACCEPTANCE PENDING`.
