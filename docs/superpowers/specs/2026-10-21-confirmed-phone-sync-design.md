# Confirmed physical phone synchronization design

## Goal

Make the accepted ReasonNotes Sync drawer represent the complete physical-phone
operation: request transfer through KDE Connect, remain visibly in progress,
and report success only after the existing durable Android receipt has been
imported and the exact requested revisions are confirmed.

## Frozen presentation boundary

The accepted Sync drawer hierarchy, sizing, wording, scope controls, note list,
cards, and actions remain unchanged. The only visual addition is an
indeterminate progress bar inside the existing action card. It is hidden while
idle and visible only while synchronization is running.

## Synchronization semantics

- Preserve `sync_linux()` as the existing one-shot protocol operation used by
  the CLI and lower-level tests.
- Add a GUI orchestration operation that invokes the one-shot transfer, records
  the exact revision IDs requested by that click, and scans the existing inbox
  and KDE Connect receive directory until every requested revision is
  `DeliveryState.CONFIRMED` in the durable ledger.
- A confirmed ledger entry remains authoritative because the existing receipt
  path validates and durably stores the Android receipt before recording
  confirmation.
- A repeated user click may use the existing bounded retry policy for an
  unconfirmed transfer. It must not bypass the existing maximum-attempt state.
- Request rejection, peer unreachability or disconnection, scan errors, and a
  120-second receipt deadline produce an error result. Transfer-request
  acceptance alone never produces a success state.
- If there are no eligible revisions to request, return a neutral no-op message.
  Existing confirmations found during the initial scan may be reported, but
  must not be represented as a newly completed transfer.

## Compatibility and safety

All/Selected note behavior, immutable history, conflicts, tombstones, deletion
propagation, receipt validation, and protocol envelopes are unchanged. The
desktop operation remains on the existing background worker. Automated tests
use disposable repositories and injected clocks; physical validation uses only
the prepared disposable Android acceptance fixture. Production cutover is not
part of this work.

## Acceptance

Automated coverage must prove request-only is not success, exact receipt
confirmation is success, no-op is neutral, timeout/disconnect/request failure
is an error, bounded retry remains intact, and the progress bar follows the
running state. Native Wayland validation must preserve the accepted layout.
Physical Android validation must demonstrate both a durable-receipt success and
a real disconnected/unreachable failure using the disposable fixture.
