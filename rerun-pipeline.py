#!/usr/bin/env python

import sys
import argparse
from pathlib import Path
from os import environ

from dark.process import Executor


def makeParser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--sampleDir",
        required=True,
        help="The sample directory.",
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
    e = Executor(dryRun=args.dryRun)  # Doesn't work on BIH: , stdout=sys.stdout)
    # This will need adjusting if anyone else runs this.
    environ.setdefault("CIV_DIR", "/Users/terry/charite/diagnostics")

    sampleDir = Path(args.sampleDir)
    topDir = sampleDir.parent
    pipelineDir = Path(args.sampleDir) / "pipelines" / "standard"

    for panelDir in "04-panel-civ-rna", "04-panel-civ-rna-encephalitis":
        e.execute(f"cd {str(pipelineDir / panelDir)!r} && make clean && ./panel.sh")
        e.execute(f"cd {str(topDir)!r} && make html-civ-rna html-civ-rna-encephalitis")


if __name__ == "__main__":
    main()
