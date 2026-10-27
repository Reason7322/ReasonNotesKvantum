# ReasonNotes Public Release and Cleanup Design

## Intent

Publish the accepted ReasonNotes 0.1 applications as one coherent open-source
project while retaining the existing Fedora and Android repositories. Remove
only established obsolete Fedora installations and redundant data copies,
without changing either accepted application, active notes, live sync state,
the verified recovery backup, or Git history.

## Goals

- Make `Reason7322/ReasonNotes` and `Reason7322/ReasonNotesKvantum` public.
- Fast-forward each repository's `main` branch to its accepted release branch;
  never rewrite or force-push history.
- License project-owned source under MIT with copyright attribution to
  Reason7322, while preserving third-party licenses and notices.
- Give both repositories public READMEs that explain the same product and link
  the platform-specific source repositories and one canonical release.
- Publish one `v0.1.0` GitHub Release from `Reason7322/ReasonNotes` containing
  the accepted RPM, accepted APK, and a SHA-256 checksum file.
- Remove verified legacy Fedora data roots, package-unowned ReasonNotes icons,
  obsolete manual app files already in Trash, and redundant physical-test data.
- Prove that the RPM install, six live notes, evolved synchronization state,
  verified backup, release artifacts, source refs, and public download URLs are
  intact after publication.

## Non-goals and anti-goals

- No application logic, synchronization behavior, live-note migration, Android
  install, new build, or replacement binary.
- No repository migration, history rewrite, force-push, or deletion of Git
  engineering history.
- No deletion of unrelated Trash content or unrelated applications.
- No promotional app launch or new screenshots. Existing captures are omitted
  from the README because they contain test notes and desktop chrome.
- No claim that the accepted debug-signed Android APK is a Play Store release.

## Established identities and preservation boundary

- Fedora installed NEVRA:
  `reasonnotes-0.1.0-1.cdf6323.fc44.x86_64`.
- Fedora runtime source:
  `cdf63233d2956718e5353ed58ad230dad07aad91`.
- Fedora accepted RPM SHA-256:
  `ef734264722788d6222312c9608bf6ab2866411942477fad871cc9ae9f26bb11`.
- Android accepted runtime source: `98b094f` on
  `forge/android-json-v1-integration`; final acceptance documentation is
  `d9c5dd4` before release-only changes.
- Android accepted APK SHA-256:
  `d0aef58c05567a928e4aad35ee2535988aeb01582458b64e7ee8cf1fce3d27d8`.
- Protected live data:
  `/home/reason/.local/share/reasonnotes/repository`. Its six current notes
  still match the accepted backup, but its processed-carrier and outbound
  synchronization state has advanced and must remain byte-for-byte untouched.
- Protected recovery baseline:
  `/ssd-storage/Backups/ReasonNotes/2026-10-27T173534+0100`.

## Publication safety

Before changing visibility, scan both repositories' reachable object databases
and filenames for private keys, common credential signatures, keystores,
private backup payloads, and literal active-note content. A match blocks
publication until resolved without history rewriting. Release assets are copied
from the accepted artifacts into ignored staging and verified by SHA-256 before
and after upload.

## Release structure

`Reason7322/ReasonNotes` is the umbrella landing page and release host because
its name is platform-neutral. Its README links the Fedora implementation at
`Reason7322/ReasonNotesKvantum`. The Fedora README links back to the Android
source and canonical release. Both default branches expose the release source.

The release contains:

- `reasonnotes-0.1.0-1.cdf6323.fc44.x86_64.rpm`
- `reasonnotes-android-0.1.apk` (byte-identical renamed copy of the accepted
  `app-debug.apk`)
- `SHA256SUMS`

The accepted RPM is not rebuilt. Its historical embedded license metadata says
`LicenseRef-Private`; the source spec is corrected to MIT for future builds,
and release notes disclose that the byte-identical accepted RPM predates the
public licensing metadata change.

## Cleanup strategy

All cleanup targets are resolved and verified before mutation. The two legacy
data roots are byte-identical to `production/` and `candidate/` in the protected
backup, so they may be moved to Trash and then selectively removed with their
own Trash metadata. The package-unowned legacy icon files may be removed.
The physical-test tree is redundant with the protected backup and may be moved
to Trash and selectively removed. Unrelated Trash entries are never touched.

## Verification

- Re-run artifact SHA-256 and signature/header checks.
- Verify the backup manifest, six live current notes, hashes of the protected
  live repository before/after cleanup, RPM ownership/integrity, and exactly one
  desktop entry/launcher.
- Verify both default branches and release commits remotely, both repositories'
  public visibility, release asset names/sizes/hashes, and unauthenticated HTTP
  access to repository and download URLs.

## Approaches considered

1. **Two repositories with one umbrella release (chosen).** Preserves history,
   keeps platform ownership clear, and provides one download page.
2. Merge both histories into a new monorepo. Rejected as an unnecessary
   migration with history and release risk.
3. Publish separate duplicate releases in both repositories. Rejected because
   it creates two canonical download locations and increases drift risk.
