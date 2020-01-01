#!/usr/bin/env python3
"""
CS256 ISA Assembler: Command-line interface
Author: Mark Liffiton
"""

import os
import sys

from assembler import Assembler, AssemblerException


def printmsg(msgtuple, color="0;36"):
    msg, data = msgtuple
    print("[{}m{}:[m {}".format(color, msg, data))
    print()


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print("Usage: {} [--logisim] CONFIGFILE FILE.asm FILEOUT0 FILEOUT1".format(sys.argv[0]), file=sys.stderr)
        print(" -or-  {} [--logisim] CONFIGFILE FILE.asm # will create FILE.0.bin and FILE.1.bin".format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--logisim":
        format = "logisim"
        del sys.argv[1]
    else:
        # default
        format = "bin"

    configfile = sys.argv[1]
    if not os.path.exists(configfile):
        print("File not found: " + configfile, file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[2]
    if not os.path.exists(filename):
        print("File not found: " + filename, file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) > 3:
        fileout0 = sys.argv[3]
        fileout1 = sys.argv[4]
    else:
        # produce .0.bin and .1.bin from the filename given
        # works well for drag-and-drop in Windows
        basename = os.path.splitext(filename)[0]
        fileout0 = basename + ".0.bin"
        fileout1 = basename + ".1.bin"

    print()  # blank line

    a = Assembler(configfile, info_callback=printmsg)
    try:
        a.assemble_file(filename, format, fileout0, fileout1)
    except AssemblerException as e:
        printmsg( (e.msg, "{}\nLine {}: {}".format(e.data, e.lineno, e.inst)), color="1;31" )

    # raw_input("Done.  Press enter to continue.")  # pause


if __name__ == "__main__":
    main()
