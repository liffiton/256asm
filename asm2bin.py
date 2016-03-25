#!/usr/bin/python
import os
import sys
from assembler import Assembler, AssemblerException


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print >> sys.stderr, "Usage: " + sys.argv[0] + " FILE FILEOUT0 FILEOUT1"
        print >> sys.stderr, " -or-  " + sys.argv[0] + " FILE # will create FILE.0.bin and FILE.1.bin"
        sys.exit(1)

    filename = sys.argv[1]
    if not os.path.exists(filename):
        print >> sys.stderr, "File not found: " + filename
        sys.exit(1)

    if len(sys.argv) > 2:
        fileout0 = sys.argv[2]
        fileout1 = sys.argv[3]
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

    a = Assembler(info_callback=printmsg)
    try:
        a.assemble_file(filename, fileout0, fileout1)
    except AssemblerException as e:
        printmsg( (e.msg, e.data), color="1;31" )

    # raw_input("Done.  Press enter to continue.")  # pause


if __name__ == "__main__":
    main()
