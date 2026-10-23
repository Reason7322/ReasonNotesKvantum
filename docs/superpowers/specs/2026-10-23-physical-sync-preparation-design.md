# Physical Synchronization Preparation Design

## Intent

Prepare the approved Widgets checkpoint for one safe Fedora-to-Android-to-
Fedora JSON v1 round trip without launching, transmitting, reinstalling, or
touching production data during preparation.

## Safety architecture

- Preserve the existing JSON v1 transport and durable receipt protocol.
- Strengthen `resolve_launch_paths()` so an isolated `HOME` cannot hide the
  login account's canonical production data directory from the in-process
  guard.
- Keep `verify-candidate-isolation.py` as a mandatory pre-launch gate for
  resolved aliases, inherited HOME/XDG roots, broad parents, and conflicting
  production/candidate processes.
- Use a fresh persistent fixture beneath `/home/reason/Temporary/`; never reuse
  the prior physical-test repository or any production/candidate repository.
- Launch with explicit HOME, every XDG root, repository, inbox, received
  directory, device ID, and `--no-auto-receive`.

## First round trip

The existing deterministic `unicode-round-trip` fixture is the only selected
note. Record transfer request, KDE Connect delivery, Android durable import,
Android edit, returned carrier, Fedora durable import, receipt return, and
confirmed ledger state separately. Do not select the conflict/deletion fixtures
until a later authorized acceptance phase.

## Earlier write incident

Do not assign an unsupported cause. Preserve the observed timeline and explain
what it proves: the explicitly isolated runtime wrote only beneath its runtime
root, while separate production and installed-candidate trees changed later.
Without the exact launch commands/process provenance, causation remains unknown.

## Acceptance

Focused transport and isolation tests pass; a persistent fixture and evidence
manifest exist; current peer identities are recorded read-only where available;
and exact gated launch/round-trip instructions are documented. Physical sync
remains separately authorized and unproven.
