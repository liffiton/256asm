#!/usr/bin/env python
"""
CS256 ISA Assembler: Command-line interface
Author: Mark Liffiton
"""

import os
import sys
from assembler import Assembler, AssemblerException


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print >> sys.stderr, "Usage: " + sys.argv[0] + " CONFIGFILE FILE.asm FILEOUT0 FILEOUT1"
        print >> sys.stderr, " -or-  " + sys.argv[0] + " CONFIGFILE FILE.asm # will create FILE.0.bin and FILE.1.bin"
        sys.exit(1)

    configfile = sys.argv[1]
    filename = sys.argv[2]
    if not os.path.exists(filename):
        print >> sys.stderr, "File not found: " + filename
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

    print  # blank line

    def printmsg(msgtuple, color="0;36"):
        msg, data = msgtuple
        print "[%sm%s:[m %s" % (color, msg, data)
        print

    a = Assembler(configfile, info_callback=printmsg)
    try:
        a.assemble_file(filename, fileout0, fileout1)
    except AssemblerException as e:
        printmsg( (e.msg, e.data), color="1;31" )

    # raw_input("Done.  Press enter to continue.")  # pause


if __name__ == "__main__":
    main()
