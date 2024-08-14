#!/usr/bin/env python

import sys
import argparse
import numpy as np
from PIL import Image
from io import StringIO
from json import dumps
import gzip
import bz2
from pathlib import Path
from random import uniform, normalvariate as normal

from dark.civ.proteins import SqliteIndex
from dark.diamond.conversion import DiamondTabularFormatReader
from dark.fasta import FastaReads
from dark.reads import DNARead

from jreads import BLACK, WHITE
from jreads.utils import rowLines


def makeParser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-n",
        type=int,
        default=10,
        dest="nReads",
        help="The number of reads to generate.",
    )

    parser.add_argument(
        "--database",
        default="20231106-rna-protein-genome.db",
        help="The protein/genome database to look for the protein in.",
    )

    parser.add_argument(
        "--sampleDir",
        help="The sample directory under which to put the generated data.",
    )

    parser.add_argument(
        "--json",
        required=True,
        help=(
            "The name of the file to write the JSON (fake) DIAMOND results to. "
            "Note that this file will be overwritten if it already exists."
        ),
    )

    parser.add_argument(
        "--fastq",
        required=True,
        help=(
            "The name of the file to write the (fake, gzipped) FASTQ reads to. "
            "Note that this file will be overwritten if it already exists."
        ),
    )

    parser.add_argument(
        "--fasta",
        default="20231106-rna-protein-genome.fasta",
        help="The FASTA file containing all databases proteins.",
    )

    parser.add_argument(
        "--tolerance",
        type=int,
        default=1,
        help=(
            "The number of horizontal white pixels to ignore between black pixels "
            "on the same row."
        ),
    )

    parser.add_argument(
        "--readCount",
        type=int,
        default=1000,
        help=(
            "The number of reads to make when making random reads (i.e., when "
            "not matching an image)."
        ),
    )

    parser.add_argument(
        "--modulus",
        type=int,
        default=5,
        help=(
            "The row sampling modulus. Only rows zero modulus this number "
            "will be shown. Use a higher number for less dense sampling."
        ),
    )

    parser.add_argument(
        "--image",
        help=(
            "The image file to read. If not given, random reads will "
            "be made to cover the protein."
        ),
    )

    parser.add_argument(
        "--protein", required=True, help="The accession number of the protein."
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra information during processing.",
    )

    return parser


def scaledHeight(img, width: int) -> int:
    """
    Return what the scaled height of an image should be if its width is set to a
    new value.

    @param img: The original C{Image}.
    @param width: The C{int} width that it will be adjusted to.
    @return: The C{int} new height the scaled image should be given in order to
        maintain its original aspect ratio.
    """
    ratio = img.width / width
    return int(img.height / ratio)


def pixels(image):
    result = set()
    for row in image:
        for pixel in row:
            result.add(pixel)

    return result


def ascii(image):
    for nRow, row in enumerate(image):
        # print(f"--> {nRow:2d}", end=" ")
        for pixel in row:
            print(" " if pixel == BLACK else "*", end="")
        print("|")


def rowLinesAscii(image, tolerance):
    for nRow, row in enumerate(image):
        colors = dict.fromkeys(range(len(row)), WHITE)
        for start, end in rowLines(row, tolerance):
            for i in range(start, end):
                assert colors[i] == WHITE
                colors[i] = BLACK

        # print(f"--> {nRow:2d}", end=" ")
        for i in range(len(row)):
            print(" " if colors[i] == BLACK else "*", end="")

        print("|")


def getProteinFASTAIds(filename):
    result = {}
    for read in FastaReads(filename):
        id_ = read.id.split("|", maxsplit=3)[2]
        result[id_] = read.id
    return result


def makeRead(id_, length):
    # Make a fake FASTQ read. We don't produce sequences from the actual virus, to be
    # sure they can never be mistaken for authentic sequencing reads.
    return DNARead(id_, "CAT" * length, "LOL" * length)


def makeHit(protein, genome, idFunc, bitscore, start, end):
    length = end - start
    id_ = next(idFunc)
    querySequence = makeRead(id_, length).sequence

    return {
        "alignments": [
            {
                "hsps": [
                    {
                        "bits": bitscore,
                        "btop": str(length),
                        "expect": 0.0,
                        "frame": 1,
                        "identicalCount": length,
                        "percentIdentical": 100.0,
                        "percentPositive": 100.0,
                        "positiveCount": length,
                        "query": querySequence,
                        "query_end": len(querySequence),
                        "query_start": 1,
                        "sbjct": protein["sequence"][start:end],
                        "sbjct_end": end,
                        "sbjct_start": start + 1,
                    },
                ],
                "length": protein["length"],
                "title": "|".join(
                    (
                        "civ",
                        "GenBank",
                        protein["accession"],
                        "GenBank",
                        genome["accession"],
                        protein["product"],
                    )
                )
                + f" [{genome['organism']}]",
            },
        ],
        "query": id_,
    }


def hitsForRegion(protein, genome, idFunc, bitscore, start, end):
    MIN_READ_LEN = 4
    READ_LEN = 65
    for thisStart in range(start, end, READ_LEN):
        thisEnd = thisStart + READ_LEN + int(uniform(-10.0, 10.0))
        if thisEnd > end:
            thisEnd = end
        if thisEnd - thisStart > MIN_READ_LEN:
            yield makeHit(
                protein,
                genome,
                idFunc,
                bitscore + normal(0.0, 3.0),
                thisStart,
                thisEnd,
            )


def randomReads(
    nReads,
    protein,
    genome,
    idFunc,
    fastaIds,
    verbose,
):
    length = protein["length"]
    hits = []

    for count in range(nReads):
        bitscore = normal(120, 5)
        start = int(uniform(0, length))
        end = start + length // 8

        if end > length:
            end = length

        hits.extend(hitsForRegion(protein, genome, idFunc, bitscore, start, end))

    return hits


def imageReads(
    imageFile,
    protein,
    genome,
    fastaIds,
    idFunc,
    tolerance,
    modulus,
    verbose,
):
    image = Image.open(imageFile).convert(mode="1")
    npImage = np.array(image, dtype=np.uint8)
    widthRatio = protein["length"] / image.width
    height = scaledHeight(image, protein["length"])

    if verbose:
        print(
            f"Image has width {image.width} and height {image.height}.", file=sys.stderr
        )
        print("Protein has length", protein["length"], file=sys.stderr)
        print("Width ratio", widthRatio, file=sys.stderr)
        print("Scaled height", height, file=sys.stderr)

    nRows = len(npImage)
    hits = []

    for nRow, row in enumerate(npImage):
        if nRow % modulus != 0:
            continue
        bitscore = ((nRows - nRow) / nRows) * height + 5
        for imgStart, imgEnd in rowLines(row, tolerance):
            start = int(imgStart * widthRatio)
            end = int(imgEnd * widthRatio)

            if verbose:
                print(
                    f"Image line {imgStart} -> {imgEnd} scaled to {start} -> {end}",
                    file=sys.stderr,
                )

            hits.extend(hitsForRegion(protein, genome, idFunc, bitscore, start, end))

    return hits


def idGenerator(prefix):
    count = 0
    while True:
        count += 1
        yield f"{prefix}{count}"


def main():
    args = makeParser().parse_args()
    database = SqliteIndex(args.database)
    protein = database.findProtein(args.protein)
    genome = database.findGenome(protein["genomeAccession"])
    fastaIds = getProteinFASTAIds(args.fasta)
    idFunc = idGenerator("FAKE-" + protein["accession"] + "-READ-")

    if args.image:
        hits = imageReads(
            args.image,
            protein,
            genome,
            fastaIds,
            idFunc,
            args.tolerance,
            args.modulus,
            args.verbose,
        )
    else:
        hits = randomReads(
            args.readCount,
            protein,
            genome,
            idFunc,
            fastaIds,
            args.verbose,
        )

    # Write the fake DIAMOND hits.
    readLengths = {}
    with bz2.open(args.json, "w") as fp:
        for hit in hits:
            fp.write((dumps(hit, sort_keys=True) + "\n").encode())
            readLengths[hit["query"]] = hit["alignments"][0]["hsps"][0]["query_end"]

    # Write the fake FASTQ reads.
    with gzip.open(args.fastq, "wb") as fp:
        for id_, length in readLengths.items():
            assert length % 3 == 0
            fp.write(makeRead(id_, length // 3).toString("fastq").encode())


if __name__ == "__main__":
    main()
