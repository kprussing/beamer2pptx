import argparse
import logging
import pathlib
import sys

from typing import (
    Sequence,
    Optional,
)

from . import convert


def _main(arguments: Optional[Sequence[str]] = None) -> None:
    """The main routine

    Parameters
    ----------

    arguments: list of strings, optional
        The command line arguments.

    """
    name = pathlib.Path(__file__).parent.stem
    parser = argparse.ArgumentParser(prog=name, description="""
        Convert a beamer presentation into a PowerPoint presentation by
        creating an image from each page of the beamer presentation and
        inserting it as a full slide in the PowerPoint version.  The
        default is to generate a PowerPoint presentation with the same
        stem as the input PDF but with the extension changed to '.pptx'.
        Notes can be inserted into the "Presenter Notes" section of the
        slide by providing a companions notes PDF generated using
        `\\setbeameroption{show only notes}`.  For best results, also
        use `\\usebeamertheme{note page}[plain]`.  The default mapping
        of notes to slides is one to one; however, this can be
        overridden with the --map option which specifies a file that
        lists the slide numbers for each slide in the notes file..
        """)
    parser.add_argument("pdf", type=argparse.FileType("rb"),
                        help="The path to the presentation to convert")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Ask before overwriting an existing file")
    parser.add_argument("-m", "--map", type=argparse.FileType("r"),
                        help=argparse.SUPPRESS)
    parser.add_argument("-n", "--notes", type=argparse.FileType("rb"),
                        help=argparse.SUPPRESS)
    parser.add_argument("-o", "--output",
                        help="The path to the output PowerPoint file.")
    parser.add_argument("-v", "--verbose", action="count",
                        help="Increase the verbosity level")

    args = parser.parse_args()

    levels = {1: logging.INFO, 2: logging.DEBUG}
    if args.verbose is not None and args.verbose not in levels:
        sys.exit(f"Invalid verbosity level {args.verbose} "
                 "(should be at most {max(_ for _ in levels)})")

    level = levels.get(args.verbose, logging.WARNING)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
    logger.addHandler(handler)

    # Preemptively close the files to avoid conflicts with multiple open
    # file handles (main for Windows).
    args.pdf.close()
    if args.notes is not None:
        args.notes.close()

    output = pathlib.Path(args.pdf).with_suffix(".pptx") \
        if args.output is None else pathlib.Path(args.output)

    if args.interactive and output.exists():
        while True:
            overwrite = input(f"File '{output}' exits. Overwrite [Yn]? ")
            if overwrite.lower().startswith("y") or overwrite == "":
                break
            elif overwrite.lower().startswith("n"):
                sys.exit(1)
            else:
                print(f"Invalid selection {overwrite}")

    mapping = []
    if args.map is not None:
        for line, _ in enumerate(args.map, start=1):
            try:
                mapping.append(int(_))
            except ValueError:
                sys.exit(f"Could not convert '{_}' on line {line} to "
                         "an integer")

    convert(args.pdf.name, output,
            args.notes if args.notes is None else args.notes.name,
            )
