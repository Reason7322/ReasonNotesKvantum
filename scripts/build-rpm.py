#!/usr/bin/env python3
"""Build a Fedora RPM from the exact owner-accepted ReasonNotes revision."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess


ACCEPTED_REVISION = "cdf63233d2956718e5353ed58ad230dad07aad91"
VERSION = "0.1.0"


def prepare(source_root: Path, topdir: Path) -> Path:
    resolved = subprocess.run(
        ["git", "rev-parse", f"{ACCEPTED_REVISION}^{{commit}}"],
        cwd=source_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if resolved != ACCEPTED_REVISION:
        raise RuntimeError(f"accepted revision resolved unexpectedly: {resolved}")

    for name in ("BUILD", "BUILDROOT", "RPMS", "SOURCES", "SPECS", "SRPMS"):
        (topdir / name).mkdir(parents=True, exist_ok=True)
    archive = topdir / "SOURCES" / f"reasonnotes-{VERSION}.tar.gz"
    subprocess.run(
        [
            "git",
            "archive",
            "--format=tar.gz",
            f"--prefix=reasonnotes-{VERSION}/",
            f"--output={archive}",
            ACCEPTED_REVISION,
        ],
        cwd=source_root,
        check=True,
    )
    rpm_sources = source_root / "packaging/rpm"
    shutil.copy2(rpm_sources / "reasonnotes", topdir / "SOURCES/reasonnotes")
    shutil.copy2(
        rpm_sources / "org.reasonnotes.ReasonNotesKvantum.desktop",
        topdir / "SOURCES/org.reasonnotes.ReasonNotesKvantum.desktop",
    )
    spec = topdir / "SPECS/reasonnotes.spec"
    shutil.copy2(rpm_sources / "reasonnotes.spec", spec)
    return spec


def build(source_root: Path, topdir: Path, output: Path) -> list[Path]:
    spec = prepare(source_root, topdir)
    rpmbuild = shutil.which("rpmbuild")
    if rpmbuild is None:
        raise FileNotFoundError("rpmbuild is unavailable; install rpm-build")
    subprocess.run(
        [rpmbuild, "-bb", "--define", f"_topdir {topdir}", str(spec)],
        cwd=source_root,
        check=True,
    )
    packages = sorted(
        (topdir / "RPMS").glob(
            f"**/reasonnotes-{VERSION}-1.cdf6323*.x86_64.rpm"
        )
    )
    if len(packages) != 1:
        discovered = sorted(path.name for path in (topdir / "RPMS").glob("**/*.rpm"))
        raise RuntimeError(
            "expected one accepted-revision binary RPM, "
            f"found {len(packages)} matching packages; discovered {discovered}"
        )
    output.mkdir(parents=True, exist_ok=True)
    destination = output / packages[0].name
    shutil.copy2(packages[0], destination)
    return [destination]


def main(arguments=None) -> int:
    source_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--topdir", type=Path, default=source_root / ".build/rpm")
    parser.add_argument("--output", type=Path, default=source_root / "dist/rpm")
    parser.add_argument("--prepare-only", action="store_true")
    options = parser.parse_args(arguments)
    spec = prepare(source_root, options.topdir)
    print(f"PREPARED_REVISION={ACCEPTED_REVISION}")
    print(f"RPM_SPEC={spec}")
    if options.prepare_only:
        return 0
    for package in build(source_root, options.topdir, options.output):
        print(f"BUILT_RPM={package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
