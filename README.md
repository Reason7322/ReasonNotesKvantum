# ReasonNotes for Fedora

ReasonNotes is an offline-first notes application for Fedora and Android. This
repository contains the accepted native Fedora desktop application. The
[Android source](https://github.com/Reason7322/ReasonNotes) and the
[downloadable release](https://github.com/Reason7322/ReasonNotes/releases/latest)
are published as part of the same project.

The Fedora application uses Qt 6 Widgets and the system Kvantum style. Notes
stay in a local repository; there is no ReasonNotes account, cloud service, or
background synchronization server.

## Features

- Create, edit, search, select, and delete local notes.
- Native Qt Widgets interface with English and Polish UI support.
- Selective or all-note synchronization with the Android application.
- Explicit conflict choices when both devices edit the same note lineage.
- Durable acknowledgments: a sync is complete only after the peer imports the
  state and returns a receipt.
- Local-only deletion. A surviving copy on the other device can be restored by
  explicitly synchronizing that device.
- Local history and transport state retained on disk for recovery and retry.

## Manual KDE Connect synchronization

ReasonNotes deliberately synchronizes only when you ask it to.

1. Install and pair KDE Connect on Fedora and Android.
2. On Android, grant ReasonNotes **All files access** so it can use
   `/storage/emulated/0/ReasonNotes Exchange`.
3. Keep KDE Connect reachable on both devices and open ReasonNotes on Android.
4. In ReasonNotes, choose all notes or selected notes and start Sync.
5. KDE Connect carries a JSON bundle to the peer. The receiving app validates
   and imports it, then returns an acknowledgment. The sender reports completion
   only after that acknowledgment is imported.

There is no background Android service. If a transfer arrives after Android was
opened, keep the app visible briefly so its foreground receiver can import it.

## Install on Fedora

The public release provides the accepted Fedora 44 x86_64 RPM:
`reasonnotes-0.1.0-1.cdf6323.fc44.x86_64.rpm`.

```sh
sha256sum -c SHA256SUMS
sudo dnf5 --no-gpgchecks install ./reasonnotes-0.1.0-1.cdf6323.fc44.x86_64.rpm
```

The RPM is currently unsigned; verify the published SHA-256 before installing.
It installs `/usr/bin/reasonnotes` and one desktop entry. Runtime requirements
include Python 3.14, PySide6 6.11, Qt 6 Wayland, Kvantum, and KDE Connect.

Application data is stored below `$XDG_DATA_HOME/reasonnotes` (normally
`~/.local/share/reasonnotes`). Removing or upgrading the RPM does not remove
that data.

## Build the Fedora RPM

On Fedora, install the build and runtime dependencies:

```sh
sudo dnf5 install rpm-build gcc python3 python3-pyside6 wayland-devel \
  wayland-protocols-devel desktop-file-utils kvantum qt6-qtwayland kde-connect
```

Then build from the repository root. Use absolute build/output paths:

```sh
/usr/bin/python3 scripts/build-rpm.py \
  --topdir "$PWD/.build/rpm" \
  --output "$PWD/dist/rpm"
```

The build script intentionally archives the accepted desktop runtime revision
`cdf63233d2956718e5353ed58ad230dad07aad91`.

Run the source tests with:

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=src \
  /usr/bin/python3 -m unittest discover -s tests -v
```

## Requirements and limitations

- The published RPM targets Fedora 44 x86_64 and Wayland.
- KDE Connect pairing and reachability are required for cross-device sync.
- Android exchange access requires Android's special **All files access** grant.
- Synchronization is explicit and foreground-oriented, not continuous cloud
  sync.
- The first public APK is development-certificate signed and distributed
  directly through GitHub, not an app store.
- The accepted RPM predates the source project's MIT publication and still has
  the historical `LicenseRef-Private` RPM header. Its bytes are preserved for
  reproducibility; current source and future package metadata are MIT.

## License

ReasonNotes project-owned source is licensed under the [MIT License](LICENSE),
copyright 2026 Reason7322. Dependencies and retained third-party assets keep
their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.md).

Release provenance and exact hashes are recorded in
[docs/RELEASE_0.1.0.md](docs/RELEASE_0.1.0.md).
