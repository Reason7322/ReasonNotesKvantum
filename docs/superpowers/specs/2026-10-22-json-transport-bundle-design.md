# ReasonNotes Canonical JSON Transport Bundle

## Goal

Reduce KDE Connect synchronization to one transport payload per ReasonNotes
operation in either direction, without changing revision, receipt, history,
conflict, deletion, retry, or durable-confirmation semantics.

## Wire format

The v1 payload is UTF-8 JSON with no byte-order mark or trailing newline:

```json
{"format":"reasonnotes-transport-bundle","items":[{"envelope":"<canonical UTF-8 envelope>","id":"<64 lowercase hex identity>","kind":"revision"}],"version":1}
```

Canonical serialization uses exactly this key order, compact separators, and
literal Unicode. Items are sorted by `kind` and then `id`. `kind` is either
`revision` or `receipt`; `envelope` is the existing canonical envelope text,
unchanged. The filename is
`reasonnotes-bundle-v1-<sha256-of-exact-payload-bytes>.json`.

A bundle contains 1 to 256 items. Each envelope is at most 16 MiB, total
envelope bytes are at most 64 MiB, and the outer payload is at most 64 MiB.
Duplicate `(kind, id)` entries are invalid.

## Validation and import

Receivers verify the canonical filename, payload hash, UTF-8/JSON syntax,
exact top-level and item fields, format/version, limits, ordering, unique
identities, envelope kind, and the identity recomputed by the existing
revision or receipt parser. The complete bundle is validated before the first
repository or ledger mutation.

After validation, each envelope follows the existing import path. Revisions
retain their immutable parent graph and tombstone semantics. Receipts retain
their per-revision durable confirmation checks. A single carrier never implies
that its contents were durably imported by the peer.

## Transport and compatibility

Each non-empty synchronization plan creates one content-addressed JSON bundle
and makes one KDE Connect transfer request. The existing ledgers advance each
included envelope to transfer-requested only after that one request is
accepted. Failure leaves every included envelope eligible under the existing
retry rules.

Legacy individual `.md` revision and receipt files remain accepted on both
platforms. Linux also retains read-only support for the already physically
received ZIP bundles in `~/Downloads`; neither platform creates a new ZIP.

## Acceptance

- Automated fixtures prove byte-identical Python/Java canonical output.
- Malformed, non-canonical, oversized, duplicate, reordered, or identity-
  mismatched bundles cause no repository mutation.
- Desktop and Android each request exactly one KDE Connect payload for a mixed
  multi-envelope sync plan.
- A physical candidate round trip transfers notes and receipts in both
  directions, with transfer count and elapsed time recorded.
- The accepted desktop UI and production launchers/data remain unchanged.
