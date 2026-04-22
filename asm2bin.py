#!/usr/bin/env python3
"""
CS256 ISA Assembler: Command-line interface
Author: Mark Liffiton
"""

import argparse
import os
import sys

from assembler import Assembler, AssemblerException


def printmsg(msgtuple: tuple[str, str], color: str = "0;36") -> None:
    msg, data = msgtuple
    print(f"[{color}m{msg}: [0m{data}")
    print()


def parse_swap(s: str) -> tuple[str, int, int]:
    try:
        kind, vals = s.split(":")
        v1, v2 = map(int, vals.split(","))
        return kind, v1, v2
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Swap must be in format KIND:V1,V2 (e.g., r:5,6)"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="CS256 ISA Assembler")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--logisim", action="store_true", help="Output Logisim image format"
    )
    group.add_argument(
        "--256sim",
        dest="cpusim",
        action="store_true",
        help="Output 256sim image format",
    )

    parser.add_argument(
        "--swap",
        action="append",
        type=parse_swap,
        help="Value swap in format KIND:V1,V2 (e.g., 'r:1,2')",
    )

    parser.add_argument("configfile", help="Assembler config file")
    parser.add_argument("asmfile", help="Assembly source file")
    parser.add_argument("outfiles", nargs="*", help="Output files")

    args = parser.parse_args()

    # Determine format
    if args.logisim:
        format = "logisim"
    elif args.cpusim:
        format = "256sim"
    else:
        format = "bin"

    # Validate files
    if not os.path.exists(args.configfile):
        print("File not found: " + args.configfile, file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.asmfile):
        print("File not found: " + args.asmfile, file=sys.stderr)
        sys.exit(1)

    # Determine output files
    if args.outfiles:
        outfiles = args.outfiles
    else:
        basename = os.path.splitext(args.asmfile)[0]
        if format == "256sim" or format == "logisim":
            outfiles = [f"{basename}.bin"]
        else:
            outfiles = [f"{basename}.{i}.bin" for i in (0, 1)]

    print()  # blank line

    a = Assembler(args.configfile, info_callback=printmsg)

    if args.swap:
        for kind, v1, v2 in args.swap:
            a.add_swap(kind, v1, v2)

    try:
        a.assemble_file(args.asmfile, format, outfiles)
    except AssemblerException as e:
        printmsg(
            (e.msg, "{}\nLine {}: {}".format(e.data, e.lineno, e.inst)), color="1;31"
        )


if __name__ == "__main__":
    main()
