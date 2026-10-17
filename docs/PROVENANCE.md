# Source provenance

The ReasonNotes domain, storage, synchronization, and application-service baseline
was imported without modification from:

- Repository: `/home/reason/Temporary/ChatGPTProjects/ReasonNotes`
- Source worktree: `worktrees/UnifiedGlassMaterial`
- Branch: `sol/unified-native-glass-material`
- Commit: `873dcd524179abc39ae708b055c76f2798af1e48`
- Import date: 2026-10-18

Imported tracked material:

- `src/reasonnotes_sync/`
- `src/reasonnotes_app/{__init__,note_document,preferences,presenter,service}.py`
- backend, presenter, preferences, and note-document tests under `tests/`
- `linux-app/icons/`
- `linux-app/native/reasonnotes_wayland_blur.c`
- `scripts/build-wayland-blur.py`
- `pyproject.toml`

Deliberately excluded:

- `android-probe/` because this project does not change the Android application;
- `linux-app/qml/`, `src/reasonnotes_app/qt_bridge.py`, and QML-only tests because
  the approved product replaces that presentation implementation;
- `src/reasonnotes_app/liquid_glass_palette.py` because the candidate inherits the
  system Kvantum theme and maintains no application-owned theme palette;
- the old Qt Quick entry point, old desktop installer, and old Qt Quick Wayland
  controller because Widgets-specific replacements are implemented here;
- build products, generated caches, linked-worktree metadata, acceptance captures,
  production data, and user configuration.

The imported data formats and protocol implementation remain compatible with the
existing Fedora and Android ReasonNotes applications. Later project commits record
all Widgets-specific changes relative to this exact baseline.
