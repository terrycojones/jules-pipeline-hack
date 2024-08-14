#!/usr/bin/env python

import sys
import argparse
from pathlib import Path

from dark.process import Executor


DATA = {
    "hendra": (
        ("NP_047106.1", None, 3, 1500),  # Hendra N 532 aa
        ("NP_047107.2", "dwight.png", 1, 1000),  # Hendra phosphoprotein 707 aa
        ("NP_047108.1", "happy.jpg", 2, 1400),  # Hendra NSP V 457 aa
        ("NP_047109.1", None, 3, 1200),  # Hendra NSP C 166 aa
        ("NP_047110.2", "heart.jpg", 4, 1000),  # Hendra M 352 aa
        ("NP_047111.2", "virus.webp", 1, 1000),  # Hendra F 546 aa
        ("NP_047112.2", "troll.jpg", 2, 1000),  # Hendra G 604 aa
        ("NP_047113.3", "mjs.webp", 1, 1000),  # Hendra polymerase 2244 aa
    ),
}


def makeParser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--virus",
        default="hendra",
        choices=tuple(DATA),
        help="The (fake) virus du jour.",
    )

    parser.add_argument(
        "--outDir",
        default="OUT",
        help="The top-level output directory.",
    )

    parser.add_argument(
        "--dryRun",
        "-n",
        action="store_true",
        help="Just print the commands that would be run.",
    )

    return parser


def main():
    args = makeParser().parse_args()
    e = Executor(dryRun=args.dryRun)

    outDir = Path(args.outDir)
    if not outDir.exists():
        e.execute(f"mkdir {str(outDir)!r}")

    for what in "fastq", "json":
        d = outDir / what
        if not d.exists():
            e.execute(f"mkdir {str(d)!r}")

    for protein, image, modulus, readCount in DATA[args.virus]:
        command = [
            "./jreads.py",
            "--database",
            "20231106-rna-protein-genome.db",
            "--protein",
            protein,
            "--tolerance",
            1,
            "--readCount",
            readCount,
            "--modulus",
            modulus,
            "--fastq",
            f"OUT/fastq/{protein}.fastq.gz",
            "--json",
            f"OUT/json/{protein}.json.bz2",
        ]

        if image:
            print(f"Making reads for protein {protein} using image {image}.")
            command.extend(("--image", f"images/{image}"))
        else:
            print(f"Making random reads for protein {protein}.")

        result = e.execute(" ".join(map(str, command)))

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr)

    if args.dryRun:
        print("\n".join(e.log))


if __name__ == "__main__":
    main()
