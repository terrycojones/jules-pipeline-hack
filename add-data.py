#!/usr/bin/env python

import sys
import argparse
from pathlib import Path

from dark.process import Executor


def makeParser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--json",
        nargs="+",
        required=True,
        help="The JSON files to put in place.",
    )

    parser.add_argument(
        "--fastq",
        nargs="+",
        required=True,
        help="The FASTQ files to put in place.",
    )

    parser.add_argument(
        "--sampleDir",
        required=True,
        help="The sample directory under which to put the generated data.",
    )

    parser.add_argument(
        "--dryRun",
        "-n",
        action="store_true",
        help="Just print the commands that would be run.",
    )

    return parser


def backup(sampleDir, suffix, e):
    assert sampleDir.exists()

    originals = list(sampleDir.glob("*." + suffix))
    if len(originals) == 1:
        original = originals[0]
    else:
        print(
            f"Did not find just one *.{suffix} file in {sampleDir}. "
            f"Found {originals}.",
            file=sys.stderr,
        )
        sys.exit(1)

    backup = Path(str(original) + ".orig")

    if backup.exists():
        print(f"Backup {backup} already exists.")
    else:
        e.execute(f"cp {str(original)!r} {str(backup)!r}")
        print(f"Backed-up {str(original)!r}.")


def add(sampleDir, suffix, files, e):
    try:
        (original,) = list(sampleDir.glob("*." + suffix + ".orig"))
    except IndexError:
        if e.dryRun:
            original = str(list(sampleDir.glob("*." + suffix))[0]) + ".orig"
        else:
            raise
    target = Path(str(original).removesuffix(".orig"))
    quotedFiles = " ".join(f"{str(filename)!r}" for filename in files)
    e.execute(f"cat {str(original)!r} {quotedFiles} > {str(target)!r}")
    print(("Would write " if e.dryRun else "Wrote ") + str(target))


def main():
    args = makeParser().parse_args()
    e = Executor(dryRun=args.dryRun)

    sampleDir = Path(args.sampleDir) / "pipelines" / "standard"

    jsonDir = sampleDir / "03-diamond-civ-rna"
    fastqDir = sampleDir / "025-dedup"

    backup(jsonDir, "bz2", e)
    backup(fastqDir, "gz", e)

    add(jsonDir, "bz2", args.json, e)
    add(fastqDir, "gz", args.fastq, e)

    if args.dryRun:
        print("\n".join(e.log))


if __name__ == "__main__":
    main()
